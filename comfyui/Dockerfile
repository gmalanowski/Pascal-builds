FROM pytorch/pytorch:2.7.1-cuda12.6-cudnn9-runtime

ARG COMFYUI_REF
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    CC=/usr/bin/gcc \
    CXX=/usr/bin/g++

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       git \
       gcc \
       g++ \
       libc6-dev \
       libgl1 \
       libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone --filter=blob:none https://github.com/Comfy-Org/ComfyUI.git \
    && cd ComfyUI \
    && git checkout --detach "${COMFYUI_REF}"

WORKDIR /opt/ComfyUI

# Modern Kornia releases may pull kornia-rs wheels built with CPU instructions
# unavailable on pre-AVX2 machines. Keep the pure-Python compatible release.
RUN sed -i '/^kornia/d' requirements.txt \
    && python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -m pip uninstall -y kornia-rs 2>/dev/null || true \
    && python -m pip install --force-reinstall --no-deps 'kornia==0.7.1'

RUN python - <<'PY'
import platform
import shutil
import torch
import kornia
print('Python:', platform.python_version())
print('Torch:', torch.__version__)
print('Kornia:', kornia.__version__)
print('C compiler:', shutil.which('gcc'))
assert kornia.__version__.startswith('0.7.1')
assert shutil.which('gcc')
PY

EXPOSE 8188
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--lowvram"]
