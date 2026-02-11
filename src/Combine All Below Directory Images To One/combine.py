import os
import sys
import shutil
from pathlib import Path

# Accepted image extensions (lowercase)
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

def is_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTS

def collect_images(root: Path, combined_dirname: str = "Combined") -> list[Path]:
    """
    Recursively collect image files under root, skipping the Combined directory
    if it exists underneath root.
    Returns a sorted list of Paths (deterministic).
    """
    collected: list[Path] = []

    # Walk top-down so we can prune 'Combined'
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Skip the output directory if encountered within the tree
        # Compare directory names case-insensitively and exact name match
        dirnames[:] = [d for d in dirnames if d != combined_dirname]

        current_dir = Path(dirpath)
        for name in filenames:
            p = current_dir / name
            if is_image_file(p):
                collected.append(p)

    # Deterministic ordering by (parent path, name)
    collected.sort(key=lambda p: (str(p.parent).lower(), p.name.lower()))
    return collected

def ensure_combined_dir(root: Path, combined_dirname: str = "Combined") -> Path:
    out = root / combined_dirname
    if out.exists():
        if not out.is_dir():
            print(f"ERROR: '{out}' exists and is not a directory.", file=sys.stderr)
            sys.exit(1)
        # If directory exists but not empty, bail to avoid confusion/overwrite
        # (Change this if you want to append instead.)
        contents = list(out.iterdir())
        if contents:
            print(
                f"ERROR: '{out}' already exists and is not empty "
                f"({len(contents)} item(s) found). Aborting to avoid overwrites.",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        out.mkdir(parents=True, exist_ok=True)
    return out

def main() -> None:
    # 1) Current directory path for use
    root = Path(os.getcwd()).resolve()
    print(f"Root directory: {root}")

    # 2) Recursively find all images, skipping the Combined folder if present
    images = collect_images(root)
    total = len(images)
    if total == 0:
        print("No JPEG/PNG images found. Nothing to do.")
        return
    print(f"Found {total} image(s).")

    # 3) Create 'Combined' directory at the root (fail if not empty)
    combined_dir = ensure_combined_dir(root)
    print(f"Output directory: {combined_dir}")

    # 4) Copy images as 1..n with original extension preserved
    for idx, src in enumerate(images, start=1):
        ext = src.suffix.lower()  # normalize extension to lowercase
        dst = combined_dir / f"{idx}{ext}"
        # Use copy2 to preserve file metadata (mtime, etc.)
        shutil.copy2(src, dst)

    print(f"Done. Copied {total} file(s) into '{combined_dir.name}'.")
    print("Example outputs:")
    example_count = min(5, total)
    for i in range(1, example_count + 1):
        print(f"  {combined_dir / (str(i) + images[i-1].suffix.lower())}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)