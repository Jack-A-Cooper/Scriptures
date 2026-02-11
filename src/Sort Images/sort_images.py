#!/usr/bin/env python3
"""
sort_images.py — Image + prompt/negative prompt organizer (incremental, safe on reruns)

Core behavior
- Renames image files to a sequential index: 1.png, 2.jpg, 3.webp, ...
- Renames associated .txt files that share the same hash/base name:
    HASH.txt              -> <n>_prompt.txt
    HASH_negative.txt     -> <n>_negative_prompt.txt
    HASH_anysuffix.txt    -> <n>_anysuffix_prompt.txt

Rerun-safe behavior
- Detects already-numbered images (numeric stems like "12.png")
- Only processes new/un-numbered images on subsequent runs
- Assigns the next available number (fills gaps)

Recursive + cleanup
- -r / --recursive: process the script directory and all subdirectories (depth-first), skipping "backup" dirs
- --clean_up: delete all directories named "backup" under the processing root
- --clean_up_scripts: delete any duplicate "sort_images.py" files in subdirectories under the script directory,
  but NEVER deletes the root script itself

Safety / convenience
- argparse CLI
- logging
- optional backups (default)
- --no_backup to skip backup creation/copying
- --overwrite, --dry_run, --verbose
- optional tqdm progress bar if installed
- optional elevate if installed
"""

import argparse
import logging
import os
import random
import re
import shutil
import string
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    if log_to_file:
        logging.basicConfig(filename=log_file, level=log_level, format=log_format)
    else:
        logging.basicConfig(level=log_level, format=log_format)
    logging.getLogger().setLevel(log_level)


def get_random_string(length: int = 8) -> str:
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def validate_directory(directory: str) -> None:
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"{directory} is not a valid directory")


def create_backup_dir(backup_dir: Path, dry_run: bool) -> None:
    if dry_run:
        logging.info(f"DRY RUN: Would ensure backup directory exists at {backup_dir}")
        return
    backup_dir.mkdir(parents=True, exist_ok=True)


def backup_file(file_path: Path, backup_dir: Path, dry_run: bool) -> Optional[Path]:
    if not file_path.exists():
        return None
    backup_path = backup_dir / file_path.name
    try:
        if dry_run:
            logging.info(f"DRY RUN: Would back up {file_path} -> {backup_path}")
            return backup_path
        shutil.copy2(str(file_path), str(backup_path))
        return backup_path
    except Exception as e:
        logging.error(f"Backup failed for {file_path}: {e}")
        return None


def _unique_temp_name(existing_lower: Set[str], ext: str) -> str:
    while True:
        name = f"__tmp__{get_random_string(16)}{ext}"
        if name.lower() not in existing_lower:
            existing_lower.add(name.lower())
            return name


def _iter(items: List, desc: str):
    if tqdm is not None:
        return tqdm(items, desc=desc, unit="item")
    return items


def _desired_txt_name(matched_number: int, matched_image_stem: str, txt_stem: str) -> str:
    """
    Build desired txt filename (no path) based on mapping rules:
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
    return f"{matched_number}{remainder}_prompt{TXT_EXT}"


def _is_already_organized_prompt(stem: str) -> bool:
    # matches: 1_prompt, 1_negative_prompt, 1_anything_prompt, 12_negative_prompt, etc.
    return re.match(r"^\d+.*_prompt$", stem.lower()) is not None


def rename_images_and_txt(
    current_dir: str,
    overwrite: bool = False,
    backup_dir: Optional[str] = None,
    no_backup: bool = False,
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
    Default "{index}" produces plain numbers for images.
    """
    validate_directory(current_dir)
    dir_path = Path(current_dir)

    # Normalize extensions (allow "png" or ".png")
    exts: List[str] = []
    for e in (file_extensions or IMAGE_EXTS_DEFAULT):
        e = e.strip().lower()
        if not e:
            continue
        if not e.startswith('.'):
            e = '.' + e
        exts.append(e)

    all_files = [p for p in dir_path.iterdir() if p.is_file()]
    images = [p for p in all_files if p.suffix.lower() in exts]
    txts = [p for p in all_files if p.suffix.lower() == TXT_EXT]

    images.sort(key=lambda p: p.name.lower())
    txts.sort(key=lambda p: p.name.lower())

    if verbose:
        logging.info(f"Scanning: {dir_path}")
        logging.info(f"Found {len(images)} image(s) and {len(txts)} txt file(s)")

    if not images:
        return

    # Backups
    backup_path: Optional[Path] = None
    if not no_backup:
        backup_path = (dir_path / "backup") if backup_dir is None else Path(backup_dir)
        create_backup_dir(backup_path, dry_run=dry_run)

        # confirmation for big overwrites
        if overwrite and len(images) > 50 and not assume_yes:
            response = input(f"About to overwrite (and backup) outputs for {len(images)} images. Proceed? (y/n): ")
            if response.strip().lower() != 'y':
                logging.info("Operation cancelled by user.")
                raise SystemExit(0)
    else:
        # confirmation for big overwrites even with no backup
        if overwrite and len(images) > 50 and not assume_yes:
            response = input(f"About to overwrite outputs for {len(images)} images (NO BACKUP). Proceed? (y/n): ")
            if response.strip().lower() != 'y':
                logging.info("Operation cancelled by user.")
                raise SystemExit(0)

    # Rerun-safe: only process un-numbered images
    used_numbers: Set[int] = set()
    images_to_process: List[Path] = []

    for img in images:
        if img.stem.isdigit():
            used_numbers.add(int(img.stem))
        else:
            images_to_process.append(img)

    if not images_to_process:
        return

    def next_free_number(start: int = 1) -> int:
        n = start
        while n in used_numbers:
            n += 1
        return n

    # Track targets to avoid collisions (case-insensitive)
    used_targets_lower: Set[str] = set(p.name.lower() for p in all_files)

    # Track txt files already attached (important when multiple images share the same hash stem)
    txt_used_lower: Set[str] = set()

    current_index = next_free_number(1)

    planned_ops: List[Tuple[List[Tuple[Path, Path]], str]] = []

    for img in images_to_process:
        idx = current_index
        used_numbers.add(idx)
        current_index = next_free_number(idx + 1)

        unique_id = get_random_string()
        new_base = naming_convention.format(index=idx, random=unique_id)
        new_img_name = f"{new_base}{img.suffix.lower()}"
        new_img_path = dir_path / new_img_name

        # Collect related txts for this image (exact stem or stem_*)
        related_txts: List[Path] = []
        for t in txts:
            if t.name.lower() in txt_used_lower:
                continue
            if _is_already_organized_prompt(t.stem):
                continue
            if t.stem == img.stem or t.stem.startswith(img.stem + "_"):
                related_txts.append(t)
                txt_used_lower.add(t.name.lower())

        # Build rename pairs for this group
        rename_pairs: List[Tuple[Path, Path]] = [(img, new_img_path)]

        for t in related_txts:
            desired_txt_filename = _desired_txt_name(idx, img.stem, t.stem)
            desired_txt_path = dir_path / desired_txt_filename

            # Disambiguate if target already exists (or would collide with another planned target)
            candidate = desired_txt_path
            k = 2
            while candidate.name.lower() in used_targets_lower and candidate != t:
                candidate = dir_path / f"{desired_txt_path.stem}_dup{k}{TXT_EXT}"
                k += 1
            used_targets_lower.add(candidate.name.lower())
            rename_pairs.append((t, candidate))

        planned_ops.append((rename_pairs, img.name))

    # Execute planned ops (two-phase rename per group)
    for rename_pairs, img_name in _iter(planned_ops, desc=f"Processing {dir_path.name}"):
        # If any destination exists and overwrite is False, skip whole group
        conflicts = []
        for src, dst in rename_pairs:
            try:
                if src.resolve() == dst.resolve():
                    continue
            except Exception:
                pass
            if dst.exists() and not overwrite:
                conflicts.append(dst)

        if conflicts:
            logging.warning(
                f"Skipped {img_name} due to existing target(s): {', '.join(str(c) for c in conflicts)}"
            )
            continue

        # Backup sources and overwritten destinations (if enabled)
        if backup_path is not None:
            for src, dst in rename_pairs:
                if src.exists():
                    backup_file(src, backup_path, dry_run=dry_run)
                if dst.exists() and overwrite:
                    backup_file(dst, backup_path, dry_run=dry_run)

        if dry_run:
            if verbose:
                for src, dst in rename_pairs:
                    logging.info(f"DRY RUN: Would rename {src} -> {dst}")
            continue

        existing_names_lower = set(p.name.lower() for p in dir_path.iterdir() if p.is_file())
        temp_map: Dict[Path, Path] = {}

        try:
            # Phase 1: move sources to unique temp names
            for src, _dst in rename_pairs:
                if not src.exists():
                    continue
                temp_name = _unique_temp_name(existing_names_lower, src.suffix)
                temp_path = src.with_name(temp_name)
                if verbose:
                    logging.info(f"Temp rename: {src} -> {temp_path}")
                src.rename(temp_path)
                temp_map[src] = temp_path

            # Phase 2: temp -> final (delete target first if overwrite)
            for src, dst in rename_pairs:
                if src not in temp_map:
                    continue
                tmp = temp_map[src]
                if dst.exists() and overwrite:
                    dst.unlink()
                if verbose:
                    logging.info(f"Final rename: {tmp} -> {dst}")
                tmp.rename(dst)

            logging.info(f"Renamed group for {img_name} ({len(rename_pairs)} file(s))")

        except Exception as e:
            logging.error(f"Error processing group for {img_name}: {e}")
            # We keep temps as-is; backups (if enabled) preserve originals.
            continue


def cleanup_backup_dirs(root_dir: Path, dry_run: bool = False) -> int:
    """Recursively delete directories named exactly 'backup' (case-insensitive) under root_dir."""
    deleted = 0
    for current_root, dirnames, _ in os.walk(root_dir, topdown=False):
        for d in list(dirnames):
            if d.lower() == "backup":
                p = Path(current_root) / d
                try:
                    if dry_run:
                        logging.info(f"DRY RUN: Would delete backup directory {p}")
                    else:
                        shutil.rmtree(p)
                        logging.info(f"Deleted backup directory {p}")
                    deleted += 1
                except Exception as e:
                    logging.error(f"Failed to delete backup directory {p}: {e}")
    return deleted


def cleanup_scripts(root_dir: Path, root_script_path: Path, dry_run: bool = False) -> int:
    """
    Recursively delete any files named exactly 'sort_images.py' under root_dir,
    EXCEPT for root_script_path itself.
    """
    removed = 0
    for current_root, _dirnames, filenames in os.walk(root_dir, topdown=False):
        for fn in filenames:
            if fn.lower() == "sort_images.py":
                p = Path(current_root) / fn
                # Never delete the root script
                try:
                    if p.resolve() == root_script_path.resolve():
                        continue
                except Exception:
                    # If resolve fails, fall back to string compare
                    if str(p) == str(root_script_path):
                        continue

                try:
                    if dry_run:
                        logging.info(f"DRY RUN: Would delete script file {p}")
                    else:
                        p.unlink()
                        logging.info(f"Deleted script file {p}")
                    removed += 1
                except Exception as e:
                    logging.error(f"Failed to delete script file {p}: {e}")
    return removed


def iter_dirs_depth_first(root_dir: Path):
    """Depth-first traversal of directories starting at root_dir. Skips any directory named 'backup'."""
    stack = [root_dir]
    while stack:
        current = stack.pop()
        if current.name.lower() == "backup":
            continue
        yield current
        try:
            children = [p for p in current.iterdir() if p.is_dir()]
        except Exception:
            continue
        children.sort(key=lambda p: p.name.lower())
        for child in reversed(children):
            stack.append(child)


def process_recursively(
    root_dir: Path,
    overwrite: bool,
    backup_dir: Optional[str],
    no_backup: bool,
    dry_run: bool,
    verbose: bool,
    naming_convention: str,
    file_extensions: List[str],
    assume_yes: bool,
) -> None:
    """Run rename_images_and_txt() on root_dir and every subdirectory (depth-first)."""
    for d in iter_dirs_depth_first(root_dir):
        per_dir_backup = None
        if (not no_backup) and (backup_dir is not None):
            # Mirror relative path under backup_dir so backups from different folders don't collide
            try:
                rel = d.resolve().relative_to(root_dir.resolve())
                per_dir_backup = str(Path(backup_dir) / rel)
            except Exception:
                per_dir_backup = str(Path(backup_dir) / d.name)

        try:
            rename_images_and_txt(
                current_dir=str(d),
                overwrite=overwrite,
                backup_dir=per_dir_backup,
                no_backup=no_backup,
                dry_run=dry_run,
                verbose=verbose,
                naming_convention=naming_convention,
                file_extensions=file_extensions,
                assume_yes=assume_yes,
            )
        except Exception as e:
            logging.error(f"Error processing directory {d}: {e}")


def main() -> None:
    if elevate is not None:
        try:
            elevate()
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Rename images to sequential numbers and rename associated prompt/negative prompt .txt files.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument('directory', nargs='?', default=os.getcwd(),
                        help='Directory containing image files (default: current directory)')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Process the script directory and all subdirectories depth-first')
    parser.add_argument('--no_backup', action='store_true',
                        help='Do NOT create backups (skips backup directory creation and backup copies)')
    parser.add_argument('--clean_up', action='store_true',
                        help='Recursively delete any directories named "backup" under the processing root (use with --dry_run to preview)')
    parser.add_argument('--clean_up_scripts', action='store_true',
                        help='Recursively delete duplicate "sort_images.py" files under the script directory (does not delete the root script)')
    parser.add_argument('--overwrite', action='store_true',
                        help='Overwrite existing destination files (backs up first unless --no_backup)')
    parser.add_argument('--backup_dir', type=str, default=None,
                        help='Directory to store backups (default: <each folder>/backup)')
    parser.add_argument('--log_to_file', action='store_true',
                        help='Log to a file instead of stdout')
    parser.add_argument('--log_file', type=str, default="image_sorting.log",
                        help='Log filename when --log_to_file is set')
    parser.add_argument('--dry_run', action='store_true',
                        help='Perform a dry run without making changes')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose output')
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

    script_dir = Path(__file__).resolve().parent
    script_path = Path(__file__).resolve()

    # Processing root:
    # - recursive: script directory
    # - non-recursive: user-provided directory
    if args.recursive:
        root_dir = script_dir
    else:
        root_dir = Path(args.directory).resolve()

    # Cleanup scripts is ALWAYS scoped to script_dir (as requested)
    if args.clean_up_scripts:
        removed = cleanup_scripts(script_dir, script_path, dry_run=args.dry_run)
        logging.info(f"Script cleanup complete. Removed duplicate sort_images.py files: {removed}")

    if args.clean_up:
        deleted = cleanup_backup_dirs(root_dir, dry_run=args.dry_run)
        logging.info(f"Backup cleanup complete. Backup directories removed: {deleted}")

    if args.recursive:
        process_recursively(
            root_dir=root_dir,
            overwrite=args.overwrite,
            backup_dir=args.backup_dir,
            no_backup=args.no_backup,
            dry_run=args.dry_run,
            verbose=args.verbose,
            naming_convention=args.naming_convention,
            file_extensions=args.file_extensions,
            assume_yes=args.assume_yes,
        )
    else:
        rename_images_and_txt(
            current_dir=str(root_dir),
            overwrite=args.overwrite,
            backup_dir=args.backup_dir,
            no_backup=args.no_backup,
            dry_run=args.dry_run,
            verbose=args.verbose,
            naming_convention=args.naming_convention,
            file_extensions=args.file_extensions,
            assume_yes=args.assume_yes,
        )


if __name__ == "__main__":
    main()
