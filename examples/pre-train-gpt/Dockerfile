FROM nvcr.io/nvidia/pytorch:24.02-py3 as content

WORKDIR /app

RUN wget http://baize-ai.daocloud.io/gpt2-train-data/gpt2-vocab.json && \
    wget http://baize-ai.daocloud.io/gpt2-train-data/gpt2-merges.txt && \
    wget http://baize-ai.daocloud.io/gpt2-train-data/meg-gpt2_text_document.bin && \
    wget http://baize-ai.daocloud.io/gpt2-train-data/meg-gpt2_text_document.idx

RUN git clone https://github.com/NVIDIA/Megatron-LM /Megatron-LM --depth=1

FROM nvcr.io/nvidia/pytorch:24.02-py3

COPY --from=content /app /data/gpt2-train-data
COPY --from=content /Megatron-LM .
ADD train-gpt.sh .

CMD ["sh", "train-gpt.sh"]
