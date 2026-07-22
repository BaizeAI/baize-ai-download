import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sync import get_credentials


def test_env_credentials():
    env = {
        "QINIU_ACCESS_KEY": "ak",
        "QINIU_SECRET_KEY": "sk",
        "QINIU_BUCKET_NAME": "bucket",
    }
    with patch.dict(os.environ, env, clear=True):
        args = SimpleNamespace(ak=None, sk=None, bucket=None)
        ak, sk, bucket = get_credentials(args)
        assert ak == "ak"
        assert sk == "sk"
        assert bucket == "bucket"
