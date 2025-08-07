#!/bin/bash

set -e

CUR_DIR=$(
    cd -- "$(dirname "$0")" >/dev/null 2>&1
    pwd -P
)

python ${CUR_DIR}/sync.py --hf "$1" "$2"
