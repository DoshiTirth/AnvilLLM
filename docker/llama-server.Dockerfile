# Builds llama.cpp's server binary (llama-server) from source.
# CPU build by default. See docs/deployment.md for GPU (CUDA) build notes.

FROM ubuntu:24.04 AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --depth 1 https://github.com/ggerganov/llama.cpp.git .

RUN cmake -B build -DGGML_NATIVE=OFF -DLLAMA_CURL=OFF \
    && cmake --build build --config Release -j"$(nproc)" --target llama-server

FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /build/build/bin/llama-server /usr/local/bin/llama-server

RUN mkdir -p /models
VOLUME ["/models"]

EXPOSE 8081

ENTRYPOINT ["llama-server"]
