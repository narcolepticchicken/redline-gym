# CUDA-pod QLoRA pilot

**UNTESTED-ON-POD.** Nothing in this path has run on a real GPU or against a
real vLLM endpoint. It is build scaffolding only. The checks performed locally
are static Python compilation, Bash syntax checks, a stdlib-only
train.py --dry-run over the checked-in JSONL, task/path checks, and source
inspection of the evaluator environment variables and scorer. They do not
validate package compatibility, CUDA kernels, model availability, merging,
vLLM, SSH, or network evaluation.

This is a manual operator runbook. Training happens on the pod. Evaluation is
run from this Mac against the pod's OpenAI-compatible endpoint; do not run the
evaluator on the pod or inside a coding-assistant harness.

## VERIFY BEFORE FIRST RUN: base model ID

The original non-MLX Hugging Face ID for the pilot's
mlx-community/Qwen3.5-9B-4bit source was not verified in this repository.
Scripts default to Qwen/Qwen3.5-9B-Instruct only because the training rows are
instruction/chat style. That is a best guess, not a confirmed fact.

Before spending GPU time, confirm the source model on the pod, for example:

~~~
huggingface-cli repo info Qwen/Qwen3.5-9B-Instruct
~~~

Also check the mlx-community model card/conversion source if necessary. Set
BASE_MODEL once to the confirmed original model ID; it is the single override
point used by both train.py and serve.sh. Also confirm that the resolved
architecture exposes the Qwen-style LoRA module names used by train.py and is
supported by the installed Transformers and vLLM versions.

## 1. Create a pod

Illustrative placeholder, with the exact Prime CLI flags and availability to
be verified in the operator's current account:

~~~
prime pods create --name redline-qwen-pilot --gpu A100-80GB --disk-gb 100
~~~

Use one A100 80GB-class GPU (an H100 80GB is also fine if pricing makes sense).
QLoRA training of a 9B model can fit on a 24GB L4/A10/4090-class card, but the
separate merged bf16 serving phase starts with roughly 18GB of model weights
before vLLM runtime and KV-cache headroom. An 80GB card is therefore the safer
single-pod choice for a 8192-token server, even though training and serving are
sequenced rather than concurrent. For this tiny dataset an H100's speed
usually does not justify a large premium over an A100; setup/download time is
more likely to dominate.

Provision enough disk for Python wheels, the base checkpoint cache, a roughly
bf16-sized merged checkpoint, adapter checkpoints, and logs. 100GB is a
starting point, not a guarantee for an unknown final model repository.

## 2. Sync the training inputs up from the Mac

On this Mac, set the SSH destination. SSH_DEST accepts either an SSH alias or
the requested user@host:port form:

~~~
export SSH_DEST='user@pod-host:22'
export REMOTE_ROOT='redline-gym'
bash scripts/pod/sync_up.sh
~~~

The sync contains data/pilot and scripts/pod, which are the only repository
inputs needed by the standalone trainer. It is safe to rerun.

## 3. Bootstrap the pod

SSH to the pod manually, change into the synced directory, and bootstrap:

~~~
ssh -p 22 user@pod-host
cd redline-gym
bash scripts/pod/setup.sh
~~~

setup.sh detects the CUDA runtime and selects a matching/backward-compatible
PyTorch wheel channel, creates .venv-pod with uv when available (otherwise
venv), installs pinned dependencies, and attempts flash-attn without making it
mandatory. Read its printed package, CUDA, and driver versions before
continuing. If a package resolver changes the pinned Torch wheel or a new
Qwen3.5 architecture requires newer packages, stop and resolve that
compatibility intentionally.

## 4. Train the adapter on the pod

First validate the data from the pod environment, then train with the
confirmed model ID:

~~~
.venv-pod/bin/python scripts/pod/train.py --dry-run
export BASE_MODEL='CONFIRMED_ORIGINAL_HF_MODEL_ID'
.venv-pod/bin/python scripts/pod/train.py
~~~

Optional resume behavior:

~~~
.venv-pod/bin/python scripts/pod/train.py --resume-from-checkpoint
.venv-pod/bin/python scripts/pod/train.py --resume-from-checkpoint adapters_pod/pilot_v2/checkpoint-50
~~~

The trainer uses 4-bit NF4 QLoRA, LoRA r=16/alpha=32, no packing, a
4096-token limit, a VRAM-bracketed batch/accumulation choice, cosine LR at
1e-4, three epochs, checkpoints every 50 optimizer steps, and early stopping
on the one-example validation set. The validation signal is consequently very
noisy; inspect both validation loss and the logged train-loss plateau.

There are only eight training rows and three epochs, so once the model is
downloaded and initialized the actual training computation should be minutes,
not hours (often only a handful of optimizer steps with the default effective
batch sizes). That is a rough operational estimate, not a measured pod
benchmark. Initial package install, model download, first CUDA initialization,
and later merging can take longer than the training loop itself.

Artifacts are written under adapters_pod/pilot_v2, including loss_curve.csv and
summary.json. No Git metadata or Git commands are involved.

## 5. Serve the merged result on the pod

Pick a high-entropy bearer key and retain it for the Mac-side evaluation:

~~~
export BASE_MODEL='CONFIRMED_ORIGINAL_HF_MODEL_ID'
export VLLM_API_KEY='replace-with-a-long-random-secret'
bash scripts/pod/serve.sh
~~~

serve.sh intentionally merges the PEFT adapter into a bf16 Hugging Face
checkpoint before starting vLLM on port 8000 with /v1 and model name
redline-pilot-v2. Merged full-weight serving is less flexible than raw
enable-lora hot-swapping, but is more robust for a newly resolved architecture:
it avoids requiring vLLM's LoRA injection path to support every target module.
The one-time merge needs extra disk and host/GPU memory; do it on the 80GB pod,
not on this Mac.

The default server context is 8192. REDLINE_AGENT_MAX_TOKENS defaults to 4000
on the evaluator, so increase VLLM_MAX_MODEL_LEN deliberately if observations
plus completions require it.

## 6. Evaluate from this Mac, never from the pod

Leave the server running, return to this repository on the Mac, then run:

~~~
export POD_BASE_URL='http://pod-host:8000/v1'
export POD_MODEL='redline-pilot-v2'
export POD_API_KEY='the-same-value-as-VLLM_API_KEY'
bash scripts/pod/eval_remote.sh
~~~

The evaluator sets REDLINE_AGENT_BASE_URL, REDLINE_AGENT_MODEL,
REDLINE_AGENT_KEY_ENV=POD_API_KEY, the POD_API_KEY itself,
REDLINE_AGENT_TEMPERATURE=0 by default, REDLINE_AGENT_MAX_TOKENS=4000 by
default, and REDLINE_SCORER_V2=1 by default. All values are overridable in the
environment. It evaluates the six historical baseline task IDs plus the
default transfer tasks T1-DPA-301 and T2-EMP-703 at seeds 0, 1, and 2. It
creates runs_pod_eval/<task>-seed<seed>, rescoring each separate run directory,
then prints a markdown composite table and the delta against 0.374.

Override the transfer list or seed list without editing the script:

~~~
TRANSFER_TASKS='T1-DPA-301 T2-EMP-703' EVAL_SEEDS='0 1 2' bash scripts/pod/eval_remote.sh
~~~

### Data-contamination / interpretation caveat

This is not a clean holdout aggregate. The training manifest contains exactly
three task IDs: T2-MSA-001, T2-DPA-302, and T2-EMP-702, three rows each. Those
same three are among the six historical baseline tasks, so eval_remote.sh
labels them in-distribution-for-training=yes. The other historical baseline
tasks (T1-DPA-311, T1-MSA-121, T1-NDA-101) are outside the training manifest
and are a different T1 family/tier. The two default transfer tasks are
different instances untouched by the manifest. This mirrors PILOT.md's
protocol of re-evaluating distillation tasks plus untouched transfer tasks,
but the combined mean must not be presented as a clean holdout number.

## 7. Sync artifacts down and destroy the pod

After training, from the Mac:

~~~
export SSH_DEST='user@pod-host:22'
export REMOTE_ROOT='redline-gym'
bash scripts/pod/sync_down.sh
~~~

This retrieves adapters_pod, including the loss CSV and summary JSON. Set
SYNC_MERGED=1 only if the large merged checkpoint is also wanted locally.

When serving/evaluation and artifact sync are complete, stop the server and
destroy the pod promptly to avoid idle GPU charges:

~~~
prime pods destroy POD_ID
~~~

Verify the current Prime command syntax and then confirm the pod is gone in
the provider UI or CLI.
