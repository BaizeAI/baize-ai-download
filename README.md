# baize-ai-download

Utilities for syncing Hugging Face repositories or local directories to Qiniu cloud storage.

## Usage

### Upload a local directory

```bash
python sync.py /path/to/local/dir qiniu/remote/path
```

### Upload directly from Hugging Face

```bash
python sync.py --hf repo-id qiniu/remote/path
```

Use optional arguments `--ak`, `--sk` and `--bucket` or environment variables `QUNIU_ACCESS_TOKEN`, `QUNIU_SECRET_KEY` and `QUNIU_BUCKET_NAME` to configure Qiniu credentials.  Provide a Hugging Face access token with `--hf-token` or the `HF_TOKEN` environment variable when required.

