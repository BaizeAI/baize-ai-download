#!/bin/bash

set -e

CUR_DIR=$(
    cd -- "$(dirname "$0")" >/dev/null 2>&1
    pwd -P
)

mkdir -p outputs

d=$(mktemp -d -p outputs)

huggingface-cli download --local-dir ${d} --local-dir-use-symlinks=False --resume-download --token "${HF_TOKEN}" $1

python ${CUR_DIR}/sync.py ${d} $2
