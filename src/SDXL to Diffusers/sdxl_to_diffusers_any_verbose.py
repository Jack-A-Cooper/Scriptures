#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sdxl_to_diffusers_any_verbose.py
Convert SDXL .safetensors/.ckpt to a Diffusers folder with extra debugging.
"""

from __future__ import annotations
import argparse, os, sys, time, traceback
from pathlib import Path
from typing import Optional

# Be loud about crashes
try:
    import faulthandler
    faulthandler.enable()
except Exception:
    pass

def log(m): print(m, flush=True)
def err(m): print(m, file=sys.stderr, flush=True)

def choose_out(inp: Path, out_arg: Optional[str]) -> Path:
    return Path(out_arg) if out_arg else inp.parent / (inp.stem + "_diffusers")

def check_libs():
    missing = []
    try: import diffusers  # noqa
    except Exception: missing.append("diffusers>=0.27")
    try: import transformers  # noqa
    except Exception: missing.append("transformers>=4.41")
    try: import accelerate  # noqa
    except Exception: missing.append("accelerate>=0.28")
    try: import safetensors  # noqa
    except Exception: missing.append("safetensors")
    if missing:
        err("[ERR] Missing: " + ", ".join(missing))
        err('      Try: pip install --upgrade "diffusers>=0.27" "transformers>=4.41" "accelerate>=0.28" safetensors')
        sys.exit(2)

def save_pipe(pipe, out_dir: Path, fp16_meta: bool):
    out_dir.mkdir(parents=True, exist_ok=True)
    pipe.save_pretrained(str(out_dir), safe_serialization=True)
    if fp16_meta:
        import json
        mi = out_dir / "model_index.json"
        data = {}
        if mi.exists():
            try: data = json.loads(mi.read_text(encoding="utf-8"))
            except Exception: pass
        data.setdefault("_converted_by", "sdxl_to_diffusers_any_verbose.py")
        data["_recommended_dtype"] = "float16"
        mi.write_text(json.dumps(data, indent=2), encoding="utf-8")

def try_base(inp: Path, out: Path, fp16: bool):
    from diffusers import StableDiffusionXLPipeline
    import torch
    dtype = torch.float16 if (fp16 and torch.cuda.is_available()) else None
    log("[STEP] Loading as SDXL Base …")
    pipe = StableDiffusionXLPipeline.from_single_file(str(inp), torch_dtype=dtype, use_safetensors=True)
    log("[OK] Loaded Base. Saving …")
    save_pipe(pipe, out, fp16)
    log(f"[OK] Saved: {out}")

def try_refiner(inp: Path, out: Path, fp16: bool):
    from diffusers import StableDiffusionXLRefinerPipeline
    import torch
    dtype = torch.float16 if (fp16 and torch.cuda.is_available()) else None
    log("[STEP] Loading as SDXL Refiner …")
    pipe = StableDiffusionXLRefinerPipeline.from_single_file(str(inp), torch_dtype=dtype, use_safetensors=True)
    log("[OK] Loaded Refiner. Saving …")
    save_pipe(pipe, out, fp16)
    log(f"[OK] Saved: {out}")

def try_inpaint(inp: Path, out: Path, fp16: bool):
    from diffusers import StableDiffusionXLInpaintPipeline
    import torch
    dtype = torch.float16 if (fp16 and torch.cuda.is_available()) else None
    log("[STEP] Loading as SDXL Inpainting …")
    pipe = StableDiffusionXLInpaintPipeline.from_single_file(str(inp), torch_dtype=dtype, use_safetensors=True)
    log("[OK] Loaded Inpaint. Saving …")
    save_pipe(pipe, out, fp16)
    log(f"[OK] Saved: {out}")

def main():
    # Make sure any stale allocator flag won’t kill import
    if "PYTORCH_CUDA_ALLOC_CONF" in os.environ and "expandable_segments" in os.environ["PYTORCH_CUDA_ALLOC_CONF"]:
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = ",".join(
            p for p in os.environ["PYTORCH_CUDA_ALLOC_CONF"].split(",")
            if not p.strip().lower().startswith("expandable_segments")
        )

    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out")
    ap.add_argument("--force", choices=["auto","base","refiner","inpaint"], default="auto")
    ap.add_argument("--fp16", action="store_true")
    args = ap.parse_args()

    inp = Path(args.input)
    if not inp.is_file():
        err(f"[ERR] Not found: {inp}"); sys.exit(1)

    out = choose_out(inp, args.out)
    log(f"[INFO] PY  : {sys.executable}")
    log(f"[INFO] In  : {inp}")
    log(f"[INFO] Out : {out}")
    log(f"[INFO] Mode: {args.force}")

    check_libs()

    order = {
        "auto": ["base", "refiner", "inpaint"],
        "base": ["base"],
        "refiner": ["refiner"],
        "inpaint": ["inpaint"],
    }[args.force]

    for kind in order:
        try:
            if kind == "base":   try_base(inp, out, args.fp16)
            if kind == "refiner":try_refiner(inp, out, args.fp16)
            if kind == "inpaint":try_inpaint(inp, out, args.fp16)
            log("\n[DONE] Select the output folder as SDXL (Diffusers) in your GUI.")
            return
        except Exception:
            err(f"[WARN] Failed as {kind}:\n" + traceback.format_exc())

    err("\n[ERR] All attempts failed. See full tracebacks above.")
    sys.exit(3)

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        err("[FATAL] Unhandled:\n" + traceback.format_exc())
        sys.exit(1)
