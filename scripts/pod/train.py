#!/usr/bin/env python3
"""QLoRA SFT entry point for the Redline Gym CUDA-pod pilot.

The module deliberately imports only the Python standard library at import
time.  That keeps --dry-run useful on the Mac, where the GPU packages are not
installed, and avoids accidental model downloads during local checks.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from pathlib import Path
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT = (
    "You are a careful contract reviewer. Review the documents against the visible "
    "playbook only. Read the contract, flag only real playbook violations with exact "
    "quotes, escalate topics where the documents are silent, and finalize a concise "
    "schema-valid card."
)

# This is a best guess, not a verified conversion source for
# mlx-community/Qwen3.5-9B-4bit.  The pilot rows are instruction/chat data, so an
# instruct variant is the sane default.  Set BASE_MODEL or --base-model after
# confirming the original non-MLX Hugging Face repository ID on the pod.
DEFAULT_BASE_MODEL = "Qwen/Qwen3.5-9B-Instruct"
EXPECTED_ROLES = ("system", "user", "assistant")
HISTOGRAM_BUCKETS = ("<512", "512-1024", "1024-2048", "2048-4096", ">4096")


def _env_path(name: str, default: Path) -> Path:
    return Path(os.getenv(name, str(default)))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-model",
        default=os.getenv("BASE_MODEL", DEFAULT_BASE_MODEL),
        help="Original non-MLX Hugging Face model ID; override BASE_MODEL after verification.",
    )
    parser.add_argument(
        "--train-file",
        type=Path,
        default=_env_path("TRAIN_FILE", ROOT / "data" / "pilot" / "train.jsonl"),
    )
    parser.add_argument(
        "--valid-file",
        type=Path,
        default=_env_path("VALID_FILE", ROOT / "data" / "pilot" / "valid.jsonl"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_env_path("ADAPTER_OUTPUT_DIR", ROOT / "adapters_pod" / "pilot_v2"),
    )
    parser.add_argument("--max-seq-length", type=int, default=int(os.getenv("MAX_SEQ_LENGTH", "4096")))
    parser.add_argument("--epochs", type=float, default=float(os.getenv("NUM_EPOCHS", "3")))
    parser.add_argument("--learning-rate", type=float, default=float(os.getenv("LEARNING_RATE", "1e-4")))
    parser.add_argument(
        "--resume-from-checkpoint",
        nargs="?",
        const="auto",
        default=None,
        metavar="PATH",
        help="Resume from PATH, or pass without a value to auto-select the newest checkpoint.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate JSONL and print local-only token statistics without loading model weights.",
    )
    return parser.parse_args(argv)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number}: JSONL row must be an object")
        rows.append(row)
    return rows


def _messages_from_row(row: dict[str, Any], *, source: str, index: int) -> list[dict[str, str]]:
    messages = row.get("messages")
    if not isinstance(messages, list):
        raise ValueError(f"{source} row {index}: expected a messages list")
    normalized: list[dict[str, str]] = []
    for message_index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"{source} row {index} message {message_index}: expected an object")
        role = message.get("role")
        content = message.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            raise ValueError(
                f"{source} row {index} message {message_index}: role and content must both be strings"
            )
        normalized.append({"role": role, "content": content})
    return normalized


def _row_problem(row: dict[str, Any], *, source: str, index: int) -> str | None:
    try:
        messages = _messages_from_row(row, source=source, index=index)
    except ValueError as exc:
        return str(exc)
    roles = tuple(message["role"] for message in messages)
    if len(messages) != 3 or roles != EXPECTED_ROLES:
        return (
            f"{source} row {index}: expected exactly three roles "
            f"{','.join(EXPECTED_ROLES)}, found {len(messages)} roles {','.join(roles)}"
        )
    if messages[0]["content"] != SYSTEM_PROMPT:
        return f"{source} row {index}: system prompt differs from baselines.honest_llm.SYSTEM_PROMPT"
    return None


def _validated_rows(path: Path) -> list[dict[str, Any]]:
    rows = _read_jsonl(path)
    if not rows:
        raise ValueError(f"{path}: no non-empty JSONL rows")
    problems = [_row_problem(row, source=str(path), index=index) for index, row in enumerate(rows, start=1)]
    problems = [problem for problem in problems if problem]
    if problems:
        raise ValueError("\\n".join(problems))
    return rows


def _approximate_chat_tokens(messages: list[dict[str, str]]) -> int:
    """A deliberately simple stdlib-only estimate used only by --dry-run."""
    text = json.dumps(messages, ensure_ascii=False, separators=(",", ":"))
    return max(1, len(text) // 4)


def _bucket(token_count: int) -> str:
    if token_count < 512:
        return "<512"
    if token_count <= 1024:
        return "512-1024"
    if token_count <= 2048:
        return "1024-2048"
    if token_count <= 4096:
        return "2048-4096"
    return ">4096"


def _try_local_tokenizer(base_model: str) -> tuple[Any | None, str]:
    """Load only a locally cached tokenizer; never contact the Hub in dry-run mode."""
    try:
        from transformers import AutoTokenizer
    except ImportError:
        return None, "approx, no tokenizer (transformers is not installed)"
    try:
        tokenizer = AutoTokenizer.from_pretrained(base_model, local_files_only=True)
    except Exception as exc:  # offline/cache failure is expected on the Mac.
        return None, f"approx, no tokenizer (not available in local cache: {type(exc).__name__})"
    if not getattr(tokenizer, "chat_template", None):
        return None, "approx, no tokenizer (cached tokenizer has no chat_template)"
    return tokenizer, "exact tokenizer (local cache only)"


def _dry_run_lengths(
    rows: list[dict[str, Any]], *, source: str, tokenizer: Any | None
) -> tuple[list[int], list[str]]:
    lengths: list[int] = []
    problems: list[str] = []
    for index, row in enumerate(rows, start=1):
        problem = _row_problem(row, source=source, index=index)
        if problem:
            problems.append(problem)
            continue
        messages = _messages_from_row(row, source=source, index=index)
        if tokenizer is None:
            lengths.append(_approximate_chat_tokens(messages))
            continue
        try:
            token_ids = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=False,
            )
            lengths.append(len(token_ids))
        except Exception as exc:
            problems.append(f"{source} row {index}: chat-template tokenization failed: {exc}")
    return lengths, problems


def run_dry_run(args: argparse.Namespace) -> int:
    train_rows = _read_jsonl(args.train_file)
    valid_rows = _read_jsonl(args.valid_file)
    tokenizer, tokenizer_mode = _try_local_tokenizer(args.base_model)

    all_rows = [("train", train_rows), ("valid", valid_rows)]
    message_counts: Counter[int] = Counter()
    role_sequences: Counter[tuple[str, ...]] = Counter()
    system_prompt_matches = 0
    total_rows = 0
    all_problems: list[str] = []
    lengths_by_split: dict[str, list[int]] = {}

    for split, rows in all_rows:
        for index, row in enumerate(rows, start=1):
            total_rows += 1
            try:
                messages = _messages_from_row(row, source=split, index=index)
            except ValueError as exc:
                all_problems.append(str(exc))
                continue
            message_counts[len(messages)] += 1
            role_sequences[tuple(message["role"] for message in messages)] += 1
            if messages and messages[0]["content"] == SYSTEM_PROMPT:
                system_prompt_matches += 1
        lengths, problems = _dry_run_lengths(rows, source=split, tokenizer=tokenizer)
        lengths_by_split[split] = lengths
        all_problems.extend(problems)

    print("DRY RUN ONLY: no model weights or tokenizer downloads were attempted.")
    print(f"Base model: {args.base_model}")
    print(f"Tokenizer mode: {tokenizer_mode}")
    print(f"Train examples: {len(train_rows)}")
    print(f"Valid examples: {len(valid_rows)}")
    print("Message-count-per-example distribution:")
    for count in sorted(message_counts):
        print(f"  {count}: {message_counts[count]}")
    print("Role-sequence distribution:")
    for roles, count in sorted(role_sequences.items()):
        label = ",".join(roles)
        suffix = " (expected)" if roles == EXPECTED_ROLES else " (UNEXPECTED)"
        print(f"  {label}: {count}{suffix}")
    expected_count = role_sequences[EXPECTED_ROLES]
    role_status = "OK" if expected_count == total_rows and not all_problems else "FAILED"
    print(f"Role sequence check (system,user,assistant): {expected_count}/{total_rows} {role_status}")
    print(f"Fixed honest_llm system prompt matches: {system_prompt_matches}/{total_rows}")
    print(f"Full chat-template token-length histogram ({tokenizer_mode}):")
    for split in ("train", "valid"):
        histogram = Counter(_bucket(length) for length in lengths_by_split[split])
        print(f"  {split}:")
        for label in HISTOGRAM_BUCKETS:
            print(f"    {label}: {histogram[label]}")
    combined = [length for values in lengths_by_split.values() for length in values]
    histogram = Counter(_bucket(length) for length in combined)
    print("  all:")
    for label in HISTOGRAM_BUCKETS:
        print(f"    {label}: {histogram[label]}")
    if all_problems:
        print("Format surprises:")
        for problem in all_problems:
            print(f"  - {problem}")
        return 1
    print("Format surprises: none.")
    return 0


def _load_training_dependencies() -> dict[str, Any]:
    """Import GPU-only dependencies only for a real pod training run."""
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            EarlyStoppingCallback,
            TrainingArguments,
        )
        from trl import SFTTrainer
    except ImportError as exc:
        raise SystemExit(
            "Real training requires the pod environment from scripts/pod/setup.sh. "
            "Use --dry-run locally; the missing dependency is: "
            f"{exc}"
        ) from exc
    return {
        "torch": torch,
        "Dataset": Dataset,
        "LoraConfig": LoraConfig,
        "get_peft_model": get_peft_model,
        "prepare_model_for_kbit_training": prepare_model_for_kbit_training,
        "AutoModelForCausalLM": AutoModelForCausalLM,
        "AutoTokenizer": AutoTokenizer,
        "BitsAndBytesConfig": BitsAndBytesConfig,
        "EarlyStoppingCallback": EarlyStoppingCallback,
        "TrainingArguments": TrainingArguments,
        "SFTTrainer": SFTTrainer,
    }


def _batch_config(torch: Any) -> tuple[int, int, float]:
    """Return (per-device batch, gradient accumulation, detected VRAM in GiB)."""
    vram_gib = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    if vram_gib >= 70:
        return 4, 4, vram_gib
    if vram_gib >= 46:
        return 2, 8, vram_gib
    if vram_gib >= 30:
        return 1, 16, vram_gib
    if vram_gib >= 20:
        return 1, 24, vram_gib
    return 1, 32, vram_gib


def _ids(value: Any) -> list[int]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    return [int(token) for token in value]


def _chat_template_tokenize(
    rows: list[dict[str, Any]], *, tokenizer: Any, max_seq_length: int, source: str
) -> list[dict[str, list[int]]]:
    """Render the exact OpenAI-style messages with the model's own chat template.

    Labels mask system/user tokens: the lone final assistant action is the SFT
    target.  We first use a template-provided assistant mask when available.
    Older templates fall back to comparing the template's generation-prefix IDs;
    this intentionally errors rather than silently training on prompt tokens if
    that comparison is unsafe for a particular architecture.
    """
    tokenized: list[dict[str, list[int]]] = []
    for index, row in enumerate(rows, start=1):
        messages = _messages_from_row(row, source=source, index=index)
        assistant_mask: list[int] | None = None
        full_ids: list[int] | None = None
        try:
            encoded = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=False,
                return_dict=True,
                return_assistant_tokens_mask=True,
            )
            full_ids = _ids(encoded["input_ids"])
            raw_mask = encoded.get("assistant_masks")
            if raw_mask is None:
                raw_mask = encoded.get("assistant_tokens_mask")
            if raw_mask is not None:
                assistant_mask = [int(value) for value in raw_mask]
                if len(assistant_mask) != len(full_ids) or not any(assistant_mask):
                    assistant_mask = None
        except (TypeError, ValueError, KeyError):
            full_ids = None

        if full_ids is None:
            full_ids = _ids(
                tokenizer.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=False,
                )
            )

        if assistant_mask is not None:
            labels = [token if is_assistant else -100 for token, is_assistant in zip(full_ids, assistant_mask)]
        else:
            prompt_ids = _ids(
                tokenizer.apply_chat_template(
                    messages[:2],
                    tokenize=True,
                    add_generation_prompt=True,
                )
            )
            if len(prompt_ids) > len(full_ids) or full_ids[: len(prompt_ids)] != prompt_ids:
                raise RuntimeError(
                    f"{source} row {index}: chat template does not expose an assistant mask and its "
                    "generation prefix is not a prefix of the full conversation. Refusing to blur "
                    "prompt and target tokens; use a tokenizer/template with assistant masks."
                )
            labels = [-100] * len(prompt_ids) + full_ids[len(prompt_ids) :]

        # Keep the final assistant action when a very long observation crosses the
        # limit. Right truncation could discard the only supervised target.
        if len(full_ids) > max_seq_length:
            full_ids = full_ids[-max_seq_length:]
            labels = labels[-max_seq_length:]
        if not any(label != -100 for label in labels):
            raise RuntimeError(f"{source} row {index}: no final assistant tokens remained after truncation")
        tokenized.append(
            {
                "input_ids": full_ids,
                "attention_mask": [1] * len(full_ids),
                "labels": labels,
            }
        )
    return tokenized


def _collator(torch: Any, pad_token_id: int):
    def collate(features: list[dict[str, list[int]]]) -> dict[str, Any]:
        max_length = max(len(feature["input_ids"]) for feature in features)
        batch_input_ids: list[list[int]] = []
        batch_attention: list[list[int]] = []
        batch_labels: list[list[int]] = []
        for feature in features:
            padding = max_length - len(feature["input_ids"])
            batch_input_ids.append(feature["input_ids"] + [pad_token_id] * padding)
            batch_attention.append(feature["attention_mask"] + [0] * padding)
            batch_labels.append(feature["labels"] + [-100] * padding)
        return {
            "input_ids": torch.tensor(batch_input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(batch_attention, dtype=torch.long),
            "labels": torch.tensor(batch_labels, dtype=torch.long),
        }

    return collate


def _latest_checkpoint(output_dir: Path) -> Path | None:
    checkpoints = []
    for path in output_dir.glob("checkpoint-*"):
        if not path.is_dir():
            continue
        try:
            checkpoints.append((int(path.name.rsplit("-", 1)[1]), path))
        except ValueError:
            continue
    return max(checkpoints, default=(0, None))[1]


def _write_loss_curve(output_dir: Path, log_history: list[dict[str, Any]]) -> None:
    fields = ("event", "step", "epoch", "loss", "eval_loss", "learning_rate")
    with (output_dir / "loss_curve.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in log_history:
            if "loss" not in record and "eval_loss" not in record:
                continue
            writer.writerow(
                {
                    "event": "eval" if "eval_loss" in record else "train",
                    "step": record.get("step", ""),
                    "epoch": record.get("epoch", ""),
                    "loss": record.get("loss", ""),
                    "eval_loss": record.get("eval_loss", ""),
                    "learning_rate": record.get("learning_rate", ""),
                }
            )


def run_training(args: argparse.Namespace) -> int:
    deps = _load_training_dependencies()
    torch = deps["torch"]
    if not torch.cuda.is_available():
        raise SystemExit("No CUDA device is available. This is a pod-only training command; use --dry-run locally.")
    if args.max_seq_length < 1:
        raise ValueError("--max-seq-length must be positive")
    if args.epochs <= 0:
        raise ValueError("--epochs must be positive")

    train_rows = _validated_rows(args.train_file)
    valid_rows = _validated_rows(args.valid_file)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    per_device_batch, gradient_accumulation, vram_gib = _batch_config(torch)
    bf16 = bool(torch.cuda.is_bf16_supported())
    compute_dtype = torch.bfloat16 if bf16 else torch.float16
    print(
        f"CUDA GPU VRAM: {vram_gib:.1f} GiB; per-device batch={per_device_batch}, "
        f"gradient accumulation={gradient_accumulation}, effective batch="
        f"{per_device_batch * gradient_accumulation}"
    )
    print("Validation set has one example: early stopping is intentionally enabled but its signal is noisy.")
    print("Also inspect the per-step train-loss plateau in loss_curve.csv before drawing conclusions.")

    AutoTokenizer = deps["AutoTokenizer"]
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if not getattr(tokenizer, "chat_template", None):
        raise RuntimeError(f"{args.base_model} tokenizer has no chat_template; refusing to hand-roll one")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    train_tokens = _chat_template_tokenize(
        train_rows,
        tokenizer=tokenizer,
        max_seq_length=args.max_seq_length,
        source=str(args.train_file),
    )
    valid_tokens = _chat_template_tokenize(
        valid_rows,
        tokenizer=tokenizer,
        max_seq_length=args.max_seq_length,
        source=str(args.valid_file),
    )
    Dataset = deps["Dataset"]
    train_dataset = Dataset.from_list(train_tokens)
    valid_dataset = Dataset.from_list(valid_tokens)

    BitsAndBytesConfig = deps["BitsAndBytesConfig"]
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )
    AutoModelForCausalLM = deps["AutoModelForCausalLM"]
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=quantization_config,
        torch_dtype=compute_dtype,
        device_map={"": 0},
    )
    model.config.use_cache = False
    model = deps["prepare_model_for_kbit_training"](model, use_gradient_checkpointing=True)
    # These are the usual Qwen attention/MLP projection names. Verify them after
    # resolving the actual Qwen3.5 architecture because module names can vary.
    lora_config = deps["LoraConfig"](
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )
    model = deps["get_peft_model"](model, lora_config)
    model.print_trainable_parameters()

    TrainingArguments = deps["TrainingArguments"]
    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        per_device_train_batch_size=per_device_batch,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=gradient_accumulation,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_strategy="steps",
        logging_steps=1,
        evaluation_strategy="steps",
        eval_steps=1,
        save_strategy="steps",
        save_steps=50,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=not bf16,
        bf16=bf16,
        gradient_checkpointing=True,
        optim="paged_adamw_32bit",
        report_to=[],
        remove_unused_columns=False,
    )
    # This pre-tokenized Dataset is the SFT chat-template formatter: it came
    # exclusively from tokenizer.apply_chat_template above, and packing remains off
    # so short independent turns never share a packed sequence.
    SFTTrainer = deps["SFTTrainer"]
    trainer_kwargs = {
        "model": model,
        "args": training_args,
        "train_dataset": train_dataset,
        "eval_dataset": valid_dataset,
        "data_collator": _collator(torch, int(tokenizer.pad_token_id)),
        "callbacks": [deps["EarlyStoppingCallback"](early_stopping_patience=2)],
        "max_seq_length": args.max_seq_length,
        "packing": False,
    }
    try:
        trainer = SFTTrainer(tokenizer=tokenizer, **trainer_kwargs)
    except TypeError as exc:
        # TRL renamed tokenizer to processing_class. Keep the fallback narrow so a
        # genuine configuration error is not accidentally swallowed.
        if "tokenizer" not in str(exc):
            raise
        trainer = SFTTrainer(processing_class=tokenizer, **trainer_kwargs)

    resume: str | None = None
    if args.resume_from_checkpoint:
        if args.resume_from_checkpoint == "auto":
            checkpoint = _latest_checkpoint(args.output_dir)
            if checkpoint is None:
                print("No checkpoint found; starting a fresh run.")
            else:
                resume = str(checkpoint)
        else:
            checkpoint = Path(args.resume_from_checkpoint)
            if not checkpoint.is_dir():
                raise FileNotFoundError(f"--resume-from-checkpoint path does not exist: {checkpoint}")
            resume = str(checkpoint)
    if resume:
        print(f"Resuming from checkpoint: {resume}")

    started = time.monotonic()
    train_result = trainer.train(resume_from_checkpoint=resume)
    evaluation = trainer.evaluate()
    wall_clock_seconds = time.monotonic() - started
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    _write_loss_curve(args.output_dir, trainer.state.log_history)

    summary = {
        "base_model": args.base_model,
        "final_train_loss": float(train_result.metrics.get("train_loss", float("nan"))),
        "final_valid_loss": float(evaluation.get("eval_loss", float("nan"))),
        "total_steps": int(trainer.state.global_step),
        "wall_clock_seconds": wall_clock_seconds,
        "detected_vram_gib": vram_gib,
        "per_device_batch_size": per_device_batch,
        "gradient_accumulation_steps": gradient_accumulation,
        "effective_batch_size": per_device_batch * gradient_accumulation,
        "max_seq_length": args.max_seq_length,
        "epochs_requested": args.epochs,
        "learning_rate": args.learning_rate,
        "train_examples": len(train_rows),
        "valid_examples": len(valid_rows),
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.dry_run:
        return run_dry_run(args)
    return run_training(args)


if __name__ == "__main__":
    raise SystemExit(main())
