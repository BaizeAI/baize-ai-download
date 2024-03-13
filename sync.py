import argparse
import os
from qiniu import Auth, put_file, BucketManager
from jinja2 import Environment, BaseLoader


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ak', type=str, help='qiniu access key')
    parser.add_argument('--sk', type=str, help='qiniu secret key')
    parser.add_argument('--bucket', type=str, required=False, help='qiniu bucket name')
    parser.add_argument('src', type=str, help='Local dir to be upload')
    parser.add_argument('dst', type=str, help='Qiniu dir prefix')
    args = parser.parse_args()
    ak = args.ak or os.getenv('QUNIU_ACCESS_TOKEN', '')
    sk = args.sk or os.getenv('QUNIU_SECRET_KEY', '')
    bucket = args.bucket or os.getenv('QUNIU_BUCKET_NAME', '') or 'baize-ai'
    upload_directory(ak, sk, args.bucket, args.src, args.dst)
