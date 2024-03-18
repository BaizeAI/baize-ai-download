FROM busybox as content

WORKDIR /app 

RUN wget http://baize-ai.daocloud.io/gpt2-train-data/gpt2-vocab.json && \
    wget http://baize-ai.daocloud.io/gpt2-train-data/gpt2-merges.txt && \
    wget http://baize-ai.daocloud.io/gpt2-train-data/meg-gpt2_text_document.bin && \
    wget http://baize-ai.daocloud.io/gpt2-train-data/meg-gpt2_text_document.idx

FROM nvcr.io/nvidia/pytorch:24.02-py3

COPY --from=content /app /data/gpt2-train-data
ADD train-gpt.sh .
