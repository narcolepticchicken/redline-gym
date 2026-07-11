#!/usr/bin/env bash
# Idempotent CUDA-pod bootstrap. Run manually on the pod from the synced repo.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="${VENV_DIR:-"$ROOT/.venv-pod"}"
PYTHON_BIN="${VENV_DIR}/bin/python"

# These defaults are intentionally version-pinned. Override only after checking
# compatibility for the particular pod image/model architecture.
#
# 2026-07-10 pod-run deviation (A100 80GB, CUDA 13.0 driver): the original pins
# (transformers 4.51.3 / trl 0.15.2 / peft 0.15.2 / bitsandbytes 0.45.5 /
# accelerate 1.6.0 / datasets 3.3.2 / vllm 0.8.5.post1 on torch 2.6.0+cu126)
# cannot load Qwen/Qwen3.5-9B (model_type qwen3_5,
# Qwen3_5ForConditionalGeneration, requires transformers >= 4.57). The pod was
# upgraded in place to the pins below; torch 2.11.0 (PyPI default CUDA build)
# was pulled in by vllm 0.24.0, replacing the explicit cu126 wheel install.
# flash-attn stayed uninstalled (no nvcc on the pod image; it is optional).
TORCH_VERSION="${TORCH_VERSION:-2.6.0}"
TRANSFORMERS_VERSION="${TRANSFORMERS_VERSION:-5.13.0}"
TRL_VERSION="${TRL_VERSION:-1.8.0}"
PEFT_VERSION="${PEFT_VERSION:-0.19.1}"
BITSANDBYTES_VERSION="${BITSANDBYTES_VERSION:-0.49.2}"
ACCELERATE_VERSION="${ACCELERATE_VERSION:-1.14.0}"
DATASETS_VERSION="${DATASETS_VERSION:-5.0.0}"
VLLM_VERSION="${VLLM_VERSION:-0.24.0}"
FLASH_ATTN_VERSION="${FLASH_ATTN_VERSION:-2.7.4.post1}"

if ! command -v nvidia-smi >/dev/null 2>&1 && ! command -v nvcc >/dev/null 2>&1; then
  echo "ERROR: no nvidia-smi or nvcc found; this script must run on a CUDA pod." >&2
  exit 1
fi

CUDA_VERSION=""
if command -v nvidia-smi >/dev/null 2>&1; then
  CUDA_VERSION="$(nvidia-smi 2>/dev/null | sed -n 's/.*CUDA Version: \([0-9.][0-9.]*\).*/\1/p' | head -n 1)"
fi
if [[ -z "$CUDA_VERSION" ]] && command -v nvcc >/dev/null 2>&1; then
  CUDA_VERSION="$(nvcc --version | sed -n 's/.*release \([0-9.][0-9.]*\).*/\1/p' | head -n 1)"
fi
if [[ -z "$CUDA_VERSION" ]]; then
  echo "ERROR: could not detect a CUDA version from nvidia-smi or nvcc." >&2
  exit 1
fi

# Select the newest compatible PyTorch wheel channel for the detected driver
# runtime. CUDA drivers are backward compatible with these wheel runtimes.
case "$CUDA_VERSION" in
  13.*|12.6*|12.7*|12.8*|12.9*) TORCH_CUDA_TAG="cu126" ;;
  12.4*|12.5*) TORCH_CUDA_TAG="cu124" ;;
  12.1*|12.2*|12.3*) TORCH_CUDA_TAG="cu121" ;;
  11.8*) TORCH_CUDA_TAG="cu118" ;;
  *)
    echo "ERROR: CUDA $CUDA_VERSION has no configured PyTorch wheel mapping." >&2
    echo "Set up a supported CUDA image (11.8 or 12.1+) or update this mapping deliberately." >&2
    exit 1
    ;;
esac
TORCH_INDEX_URL="https://download.pytorch.org/whl/${TORCH_CUDA_TAG}"

if command -v apt-get >/dev/null 2>&1; then
  SUDO=()
  if [[ "$(id -u)" -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      SUDO=(sudo)
    else
      echo "ERROR: apt-get needs root or sudo on this pod image." >&2
      exit 1
    fi
  fi
  "${SUDO[@]}" apt-get update
  "${SUDO[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    ca-certificates \
    curl \
    git \
    ninja-build \
    pkg-config \
    python3 \
    python3-dev \
    python3-venv
else
  echo "WARNING: apt-get is unavailable; assuming build and Python dependencies already exist." >&2
fi

if command -v uv >/dev/null 2>&1; then
  echo "Creating/reusing virtual environment with uv: $VENV_DIR"
  uv venv --python python3 "$VENV_DIR"
else
  echo "uv is unavailable; creating/reusing virtual environment with venv: $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

"$PYTHON_BIN" -m pip install --upgrade "pip==25.0.1" "setuptools==75.8.0" "wheel==0.45.1"
echo "Installing torch ${TORCH_VERSION}+${TORCH_CUDA_TAG} from ${TORCH_INDEX_URL}"
"$PYTHON_BIN" -m pip install --upgrade \
  --index-url "$TORCH_INDEX_URL" \
  "torch==${TORCH_VERSION}+${TORCH_CUDA_TAG}"

"$PYTHON_BIN" -m pip install --upgrade \
  "transformers==${TRANSFORMERS_VERSION}" \
  "trl==${TRL_VERSION}" \
  "peft==${PEFT_VERSION}" \
  "bitsandbytes==${BITSANDBYTES_VERSION}" \
  "accelerate==${ACCELERATE_VERSION}" \
  "datasets==${DATASETS_VERSION}" \
  "vllm==${VLLM_VERSION}"

if ! "$PYTHON_BIN" -m pip install --upgrade --no-build-isolation "flash-attn==${FLASH_ATTN_VERSION}"; then
  echo "WARNING: flash-attn installation failed; continuing without it." >&2
  echo "WARNING: training and vLLM serving must not be configured to require flash-attn." >&2
fi

echo
echo "Installed package versions:"
"$PYTHON_BIN" - <<'PY'
from importlib.metadata import PackageNotFoundError, version

for package in ("torch", "transformers", "trl", "peft", "bitsandbytes", "accelerate", "vllm"):
    try:
        print(f"{package}={version(package)}")
    except PackageNotFoundError:
        print(f"{package}=NOT INSTALLED")
PY

echo
echo "CUDA / driver information:"
echo "detected_cuda_runtime=$CUDA_VERSION"
echo "torch_wheel_channel=$TORCH_CUDA_TAG"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
fi
if command -v nvcc >/dev/null 2>&1; then
  nvcc --version
fi
echo "Bootstrap complete. Inspect the versions above before spending GPU-hours."
