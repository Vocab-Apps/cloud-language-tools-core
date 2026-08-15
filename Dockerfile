# syntax=docker/dockerfile:1.7
# base image for cloud-language-tools: contains cloudlanguagetools and all runtime deps
# inspecting this image:
# docker run --rm -it vocabai/cloud-language-tools-core:16.1.1 /bin/bash
FROM python:3.14-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# libasound2t64: azure speech sdk native libs (libMicrosoft.CognitiveServices.Speech.extension.audio.sys.so)
# libmagic1t64:  python-magic, used by the tests
# ffmpeg:        pydub
# git, gnupg:    required by downstream images (git+ pip requirement, gpg secret decryption)
#
# the azure speech sdk ships libpal_azure_c_shared_openssl3.so and dlopens openssl at
# runtime, so the openssl 1.1.1 source build previous images needed is no longer required.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        ffmpeg \
        git \
        gnupg \
        libasound2t64 \
        libmagic1t64 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# dependency layer, pinned by uv.lock. only invalidated when dependencies change.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv export --frozen --no-dev --no-emit-project --output-file requirements.txt && \
    uv pip install --system --requirements requirements.txt

# application layer: the wheel built by package.sh
ARG CLT_CORE_VERSION
COPY dist/cloudlanguagetools-${CLT_CORE_VERSION}-py3-none-any.whl ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-deps cloudlanguagetools-${CLT_CORE_VERSION}-py3-none-any.whl

# downstream images COPY into / and use ENTRYPOINT ["./start.sh"], so leave WORKDIR at /
WORKDIR /
RUN rm -rf /build
