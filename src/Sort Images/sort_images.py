#!/usr/bin/env python3
"""
Image + prompt/negative prompt renamer.

What it does
- Renames image files to a deterministic sequence (default: 1.png, 2.jpg, ...).
- Also renames associated .txt files that share the same hash/base name as the image:
    HASH.txt              -> <n>_prompt.txt
    HASH_negative.txt     -> <n>_negative_prompt.txt
    HASH_anysuffix.txt    -> <n>_anysuffix_prompt.txt

Safety / convenience features (ported from sort_images.py)
- argparse CLI
- logging (stdout or file)
- optional backup directory (copies originals before changes)
- overwrite mode
- dry-run mode
- verbose mode
- progress bar (tqdm if installed; otherwise simple loop)
- optional elevation (if 'elevate' is installed)

Notes
- Orphan .txt files (no corresponding image stem) are left untouched.
- If an image has no prompt/negative prompt .txt files, it is renamed normally.
"""

import os
import argparse
import logging
import shutil
import random
import string
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Optional dependencies
try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover
    tqdm = None  # type: ignore

try:
    from elevate import elevate  # type: ignore
except Exception:  # pragma: no cover
    elevate = None  # type: ignore


IMAGE_EXTS_DEFAULT = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff']
TXT_EXT = '.txt'


def setup_logging(log_to_file: bool = False, log_level: int = logging.INFO, log_file: str = "image_sorting.log") -> None:
    """Sets up logging configuration."""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    if log_to_file:
        logging.basicConfig(filename=log_file, level=log_level, format=log_format)
    else:
        logging.basicConfig(level=log_level, format=log_format)
    logging.getLogger().setLevel(log_level)


def get_random_string(length: int = 8) -> str:
    """Generates a random string of specified length."""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def validate_directory(directory: str) -> None:
    """Validates if the given directory path exists and is a directory."""
    if not os.path.isdir(directory):
        logging.error(f"{directory} is not a valid directory")
        raise NotADirectoryError(f"{directory} is not a valid directory")


def create_backup_dir(backup_dir: Path, dry_run: bool) -> None:
    """Creates a backup directory if it does not exist."""
    if dry_run:
        logging.info(f"DRY RUN: Would ensure backup directory exists at {backup_dir}")
        return
    backup_dir.mkdir(parents=True, exist_ok=True)


def backup_file(file_path: Path, backup_dir: Path, dry_run: bool) -> Optional[Path]:
    """Backs up a file to the specified backup directory."""
    if not file_path.exists():
        return None
    backup_path = backup_dir / file_path.name
    try:
        if dry_run:
            logging.info(f"DRY RUN: Would back up {file_path} -> {backup_path}")
            return backup_path
        shutil.copy2(str(file_path), str(backup_path))
        logging.info(f"Backed up {file_path} -> {backup_path}")
        return backup_path
    except Exception as e:
        logging.error(f"Backup failed for {file_path}: {e}")
        return None


def confirm_backup(overwrite: bool, num_images: int, assume_yes: bool = False) -> None:
    """
    Asks for user confirmation before proceeding with backup/overwrite if the number of files is large.
    """
    if overwrite and num_images > 50 and not assume_yes:
        response = input(f"About to overwrite (and backup) outputs for {num_images} images. Proceed? (y/n): ")
        if response.strip().lower() != 'y':
            logging.info("Operation cancelled by user.")
            raise SystemExit(0)


def _unique_temp_name(existing_lower: set, ext: str) -> str:
    """Generate a unique temp filename (no path) with the given extension."""
    while True:
        name = f"__tmp__{get_random_string(16)}{ext}"
        if name.lower() not in existing_lower:
            existing_lower.add(name.lower())
            return name


def _iter_images(images: List[Path], desc: str):
    if tqdm is not None:
        return tqdm(images, desc=desc, unit="image")
    return images


def _match_txt_to_image_stem(txt_stem: str, stem_to_number: Dict[str, int]) -> Optional[Tuple[str, int]]:
    """
    Match a .txt stem to an image stem:
    - exact match: STEM
    - prefix match: STEM_<suffix> (choosing the longest STEM match)
    Returns (matched_image_stem, image_number) or None.
    """
    if txt_stem in stem_to_number:
        return (txt_stem, stem_to_number[txt_stem])

    best: Optional[Tuple[str, int]] = None
    for stem, num in stem_to_number.items():
        if txt_stem.startswith(stem + "_"):
            if best is None or len(stem) > len(best[0]):
                best = (stem, num)
    return best


def _desired_txt_name(matched_number: int, matched_image_stem: str, txt_stem: str) -> str:
    """
    Build desired txt filename (no path) based on the mapping rules:
      HASH.txt          -> <n>_prompt.txt
      HASH_negative.txt -> <n>_negative_prompt.txt
      HASH_active.txt   -> <n>_active_prompt.txt
    Also normalizes existing _prompt / _negative_prompt endings.
    """
    remainder = txt_stem[len(matched_image_stem):]  # includes leading '_' if present
    remainder_lower = remainder.lower()

    # Normalize if someone already has _prompt / _negative_prompt
    if remainder_lower.endswith("_negative_prompt"):
        remainder = remainder[:-len("_negative_prompt")]
        remainder_lower = remainder.lower()
    elif remainder_lower.endswith("_prompt"):
        remainder = remainder[:-len("_prompt")]
        remainder_lower = remainder.lower()

    if remainder == "":
        return f"{matched_number}_prompt{TXT_EXT}"
    if remainder_lower == "_negative":
        return f"{matched_number}_negative_prompt{TXT_EXT}"
    # keep suffix (e.g. "_active") and add "_prompt"
    return f"{matched_number}{remainder}_prompt{TXT_EXT}"


def rename_images_and_txt(
    current_dir: str,
    overwrite: bool = False,
    backup_dir: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
    naming_convention: str = "{index}",
    file_extensions: Optional[List[str]] = None,
    assume_yes: bool = False,
) -> None:
    """
    Renames images and associated .txt files in current_dir.

    naming_convention supports:
      - {index}  -> sequential integer (1..N)
      - {random} -> random string
    Default is "{index}" to produce plain numbers for images.
    """
    validate_directory(current_dir)
    dir_path = Path(current_dir)

    exts = [e.lower() for e in (file_extensions or IMAGE_EXTS_DEFAULT)]
    all_files = [p for p in dir_path.iterdir() if p.is_file()]
    images = [p for p in all_files if p.suffix.lower() in exts]
    txts = [p for p in all_files if p.suffix.lower() == TXT_EXT]

    images.sort(key=lambda p: p.name.lower())
    if not images:
        logging.info("No matching image files found to rename.")
        return

    if backup_dir is None:
        backup_path = dir_path / "backup"
    else:
        backup_path = Path(backup_dir)

    create_backup_dir(backup_path, dry_run=dry_run)
    confirm_backup(overwrite=overwrite, num_images=len(images), assume_yes=assume_yes)

    # Build mapping from original image stems to assigned numbers
    stem_to_number: Dict[str, int] = {}
    for idx, img in enumerate(images, start=1):
        stem_to_number.setdefault(img.stem, idx)

    # Precompute planned operations per image, so we can skip consistently when conflicts occur
    planned_ops: List[Tuple[List[Tuple[Path, Path]], str]] = []  # ([(src, dst), ...], image_name)

    used_targets_lower: set = set(p.name.lower() for p in all_files)

    for idx, img in enumerate(images, start=1):
        unique_id = get_random_string()
        new_base = naming_convention.format(index=idx, random=unique_id)
        new_img_name = f"{new_base}{img.suffix.lower()}"
        new_img_path = dir_path / new_img_name

        # Determine txt files that correspond to this image (exact stem or stem_*)
        # We'll gather by scanning txts and matching to this image stem specifically.
        related_txts: List[Path] = []
        for t in txts:
            if t.stem == img.stem or t.stem.startswith(img.stem + "_"):
                related_txts.append(t)

        # Build desired txt renames
        rename_pairs: List[Tuple[Path, Path]] = []

        # First: image itself
        rename_pairs.append((img, new_img_path))

        for t in related_txts:
            desired_txt_filename = _desired_txt_name(idx, img.stem, t.stem)
            desired_txt_path = dir_path / desired_txt_filename

            # If multiple txts would map to same destination, disambiguate
            candidate = desired_txt_path
            k = 2
            while candidate.name.lower() in used_targets_lower and candidate != t:
                candidate = dir_path / f"{candidate.stem}_dup{k}{TXT_EXT}"
                k += 1
            used_targets_lower.add(candidate.name.lower())

            rename_pairs.append((t, candidate))

        planned_ops.append((rename_pairs, img.name))

    # Execute planned ops, per image, using two-phase rename to avoid collisions
    for rename_pairs, img_name in _iter_images(planned_ops, desc="Processing Images"):
        # Detect conflicts: if any destination exists and overwrite is False, skip whole group
        conflicts = []
        for src, dst in rename_pairs:
            if src.resolve() == dst.resolve():
                continue
            if dst.exists() and not overwrite:
                conflicts.append(dst)

        if conflicts:
            logging.warning(f"Skipped {img_name} due to existing target(s): {', '.join(str(c) for c in conflicts)}")
            continue

        # Backup sources (and any overwritten destinations)
        for src, dst in rename_pairs:
            if src.exists():
                backup_file(src, backup_path, dry_run=dry_run)
            if dst.exists() and overwrite:
                backup_file(dst, backup_path, dry_run=dry_run)

        if dry_run:
            for src, dst in rename_pairs:
                if verbose:
                    logging.info(f"DRY RUN: Would rename {src} -> {dst}")
            continue

        # Two-phase rename (temp then final) for this group
        group_files = [src for src, _ in rename_pairs if src.exists()]
        existing_names_lower = set(p.name.lower() for p in dir_path.iterdir() if p.is_file())

        temp_map: Dict[Path, Path] = {}
        try:
            # Phase 1: move sources to unique temp names
            for src, dst in rename_pairs:
                if not src.exists():
                    continue
                temp_name = _unique_temp_name(existing_names_lower, src.suffix)
                temp_path = src.with_name(temp_name)
                if verbose:
                    logging.info(f"Temp rename: {src} -> {temp_path}")
                src.rename(temp_path)
                temp_map[src] = temp_path

            # Phase 2: temp -> final (remove target first if overwrite)
            for src, dst in rename_pairs:
                if src not in temp_map:
                    continue
                tmp = temp_map[src]
                if dst.exists() and overwrite:
                    try:
                        dst.unlink()
                    except Exception as e:
                        logging.error(f"Failed to remove existing target {dst}: {e}")
                        raise
                if verbose:
                    logging.info(f"Final rename: {tmp} -> {dst}")
                tmp.rename(dst)

            logging.info(f"Renamed group for {img_name} ({len(rename_pairs)} file(s))")

        except Exception as e:
            logging.error(f"Error processing group for {img_name}: {e}")
            # Best-effort rollback: leave temps as-is (they're backed up). Avoid partial further actions.
            continue


def main() -> None:
    if elevate is not None:
        try:
            elevate()  # Elevate to admin if available (Windows UAC, etc.)
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Rename images to sequential numbers and rename associated prompt/negative prompt .txt files.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=r"""Examples:
  python organizeImgDirs_merged.py ./images
  python organizeImgDirs_merged.py ./images --overwrite --backup_dir ./backup --log_to_file --dry_run --verbose --log_level DEBUG
  python organizeImgDirs_merged.py ./images --naming_convention "{index}_{random}" --file_extensions .jpg .png .webp
""",
    )
    parser.add_argument('directory', nargs='?', default=os.getcwd(),
                        help='Directory containing image files (default: current directory)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files (backs up first)')
    parser.add_argument('--backup_dir', type=str, default=None, help='Directory to store backups (default: <dir>/backup)')
    parser.add_argument('--log_to_file', action='store_true', help='Log to a file instead of stdout')
    parser.add_argument('--log_file', type=str, default="image_sorting.log", help='Log filename when --log_to_file is set')
    parser.add_argument('--dry_run', action='store_true', help='Perform a dry run without making changes')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--log_level', type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Set the logging level')
    parser.add_argument('--naming_convention', type=str, default="{index}",
                        help='Naming convention for new image base names. Supports {index} and {random}. Default: "{index}"')
    parser.add_argument('--file_extensions', type=str, nargs='+', default=IMAGE_EXTS_DEFAULT,
                        help='Image file extensions to include (default includes common image types)')
    parser.add_argument('--assume_yes', action='store_true',
                        help='Do not prompt for confirmation when overwriting many files')

    args = parser.parse_args()
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    setup_logging(log_to_file=args.log_to_file, log_level=log_level, log_file=args.log_file)

    rename_images_and_txt(
        current_dir=args.directory,
        overwrite=args.overwrite,
        backup_dir=args.backup_dir,
        dry_run=args.dry_run,
        verbose=args.verbose,
        naming_convention=args.naming_convention,
        file_extensions=args.file_extensions,
        assume_yes=args.assume_yes,
    )


if __name__ == "__main__":
    main()
