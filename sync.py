import argparse
import os
import io
from collections import defaultdict
from typing import Optional

import requests
from qiniu import Auth, put_file, put_stream_v2, put_data
from qiniu import config as qiniu_config
from jinja2 import Environment, BaseLoader
from huggingface_hub import HfApi, hf_hub_url
from huggingface_hub.hf_api import RepoFolder
import fsspec


# 直接在脚本中定义模板
template_string = """
<!DOCTYPE html>
<html>
<head>
    <title>Index of {{ directory }}/</title>
</head>
<body>
    <h1>Index of {{ directory }}/</h1>
    <ul>
        {% for dir in directories %}
            <li><a href="./{{ dir }}/">{{ dir }}/</a></li>
        {% endfor %}
        {% for file in files %}
            <li><a href="./{{ file }}">{{ file }}</a></li>
        {% endfor %}
    </ul>
</body>
</html>
"""

# 使用字符串作为模板


def upload_directory(ak, sk, bucket_name, directory_path, target):
    # 初始化七牛云认证和 BucketManager
    q = Auth(ak, sk)
    env = Environment(loader=BaseLoader())
    template = env.from_string(template_string)
    for root, dirs, files in os.walk(directory_path):
        # 相对路径
        relative_path = os.path.relpath(root, directory_path)
        if relative_path == ".":
            relative_path = ""
        # 过滤出非 index.html 的文件
        files = [f for f in files if f != 'index.html']
        # 生成 index.html 内容
        index_content = template.render(directory=os.path.basename(root) or "/", directories=dirs, files=files)
        index_file_path = os.path.join(root, 'index.html')
        with open(index_file_path, 'w') as f:
            f.write(index_content)

        # 上传 index.html
        upload_file(q, bucket_name, index_file_path, os.path.join(target, relative_path, 'index.html'))

        # 上传目录下的文件
        for file in files:
            file_path = os.path.join(root, file)
            upload_file(q, bucket_name, file_path, os.path.join(target, relative_path, file))


def upload_file(client, bucket_name, local_file, remote_file):
    token = client.upload_token(bucket_name, remote_file, 3600)
    put_file(token, remote_file, local_file)
    print(f"Uploaded {local_file} to {remote_file}")


def upload_data(client, bucket_name, data, remote_file):
    token = client.upload_token(bucket_name, remote_file, 3600)
    put_data(token, remote_file, data)
    print(f"Uploaded bytes data to {remote_file}")


def upload_stream(client, bucket_name, stream, remote_file, file_name, file_size):
    token = client.upload_token(bucket_name, remote_file, 36000)
    print(f"Uploading stream to {remote_file}")
    d, resp = put_stream_v2(token, remote_file, stream, file_name, file_size)
    if d is None:
        raise RuntimeError(resp)


def upload_hf_repo(
    ak,
    sk,
    bucket_name,
    repo_id,
    target,
    repo_type="model",
    revision="main",
    token: Optional[str] = None,
):
    q = Auth(ak, sk)
    env = Environment(loader=BaseLoader())
    template = env.from_string(template_string)

    api = HfApi(token=token)
    tree = api.list_repo_tree(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        recursive=True,
    )

    structure: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"dirs": set(), "files": set()}
    )

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    for item in tree:
        if isinstance(item, RepoFolder):
            continue

        dir_path = os.path.dirname(item.path)
        file_name = os.path.basename(item.path)
        parts = dir_path.split("/") if dir_path else []
        for i, part in enumerate(parts):
            parent_dir = "/".join(parts[:i])
            child_dir = parts[i]
            structure[parent_dir]["dirs"].add(child_dir)
        structure[dir_path]["files"].add(file_name)

        url = hf_hub_url(repo_id, item.path, repo_type=repo_type, revision=revision)
        remote_path = os.path.join(target, item.path)
        # with requests.get(url, stream=True, headers=headers) as r:
        #     r.raise_for_status()
        with fsspec.open(url, block_size=1_000_000) as f:
            upload_stream(q, bucket_name, f, remote_path, file_name, item.size)

    for dir_path, content in structure.items():
        index_content = template.render(
            directory=os.path.basename(dir_path) or "/",
            directories=sorted(content["dirs"]),
            files=sorted(content["files"]),
        )
        remote_index = os.path.join(target, dir_path, "index.html")
        upload_data(q, bucket_name, index_content.encode("utf-8"), remote_index)


if __name__ == '__main__':
    # Configure longer timeout for large file uploads (5 minutes instead of default 30s)
    # This prevents TimeoutError when uploading large files like model.bin through qiniu's put_stream_v2
    qiniu_config.set_default(connection_timeout=60*60*3)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--ak', type=str, help='qiniu access key')
    parser.add_argument('--sk', type=str, help='qiniu secret key')
    parser.add_argument('--bucket', type=str, required=False, help='qiniu bucket name')
    parser.add_argument('--hf', action='store_true', help='treat src as HuggingFace repo id')
    parser.add_argument('--repo-type', type=str, default='model', help='HuggingFace repo type')
    parser.add_argument('--revision', type=str, default='main', help='HuggingFace repo revision')
    parser.add_argument('--hf-token', type=str, help='HuggingFace access token')
    parser.add_argument('src', type=str, help='Local dir or HF repo id to be upload')
    parser.add_argument('dst', type=str, help='Qiniu dir prefix')
    args = parser.parse_args()
    ak = args.ak or os.getenv('QUNIU_ACCESS_TOKEN', '')
    sk = args.sk or os.getenv('QUNIU_SECRET_KEY', '')
    bucket = args.bucket or os.getenv('QUNIU_BUCKET_NAME', '') or 'baize-ai'
    if args.hf:
        hf_token = args.hf_token or os.getenv('HF_TOKEN', None)
        upload_hf_repo(
            ak,
            sk,
            bucket,
            args.src,
            args.dst,
            repo_type=args.repo_type,
            revision=args.revision,
            token=hf_token,
        )
    else:
        upload_directory(ak, sk, bucket, args.src, args.dst)
