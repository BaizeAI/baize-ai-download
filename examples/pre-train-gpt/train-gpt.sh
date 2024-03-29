#!/bin/bash

# Runs the "345M" parameter model

set -x

export CUDA_DEVICE_MAX_CONNECTIONS=1

CHECKPOINT_PATH=/checkpoints
VOCAB_FILE=/data/gpt2-train-data/gpt2-vocab.json
MERGE_FILE=/data/gpt2-train-data/gpt2-merges.txt
DATA_PATH=/data/gpt2-train-data/meg-gpt2_text_document

# TRAIN_SIZE:
# nano: for single p4 can run.
TRAIN_SIZE=${TRAIN_SIZE:-nano}

if [[ ${TRAIN_SIZE} == "nano" ]]; then # eg: p4, gtx 1080?
    GPT_SIZE_ARGS="
        --num-layers 12 \
        --hidden-size 512 \
        --num-attention-heads 8
    "
elif [[ ${TRAIN_SIZE} == "mini" ]]; then # eg: t4, v100
    GPT_SIZE_ARGS="
        --num-layers 24 \
        --hidden-size 1024 \
        --num-attention-heads 16
    "
else
    GPT_SIZE_ARGS="
        --num-layers 28 \
        --hidden-size 2048 \
        --num-attention-heads 32
    "
fi

GPT_ARGS="
    --tensor-model-parallel-size ${TENSOR_PARALLEL_SIZE:-1} \
    --seq-length 1024 \
    --max-position-embeddings 1024 \
    --micro-batch-size 4 \
    --global-batch-size 8 \
    --lr 0.00015 \
    --train-iters 500000 \
    --lr-decay-iters 320000 \
    --lr-decay-style cosine \
    --min-lr 1.0e-5 \
    --weight-decay 1e-2 \
    --lr-warmup-fraction .01 \
    --clip-grad 1.0 \
    --fp16
"

DATA_ARGS="
    --data-path $DATA_PATH \
    --vocab-file $VOCAB_FILE \
    --merge-file $MERGE_FILE \
    --split 949,50,1
"

OUTPUT_ARGS=${OUTPUT_ARGS:-"
    --log-interval 100 \
    --save-interval 500000 \
    --eval-interval 1000 \
    --eval-iters 10
"}

torchrun pretrain_gpt.py \
    $GPT_SIZE_ARGS \
    $GPT_ARGS \
    $DATA_ARGS \
    $OUTPUT_ARGS \
    $EXTRA_ARGS \
    --save $CHECKPOINT_PATH \
    --load $CHECKPOINT_PATH
