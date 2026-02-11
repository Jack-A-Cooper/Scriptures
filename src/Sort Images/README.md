
sort_images.py — Image & Prompt Renamer (Recursive, Rerun‑Safe)
================================================================

Overview
--------
This script organizes image outputs (e.g., Stable Diffusion) into a clean, numbered dataset.

It will:
1) Rename images to sequential numbers: 1.png, 2.jpg, 3.webp, ...
2) Rename matching prompt text files:
      HASH.txt              -> <n>_prompt.txt
      HASH_negative.txt     -> <n>_negative_prompt.txt
      HASH_anysuffix.txt    -> <n>_anysuffix_prompt.txt
3) Work safely across multiple runs:
   - Detects already-numbered images
   - Only processes NEW hash-named images
   - Uses the next available number (fills gaps)

Supported image types (default):
.png .jpg .jpeg .webp .bmp .tif .tiff


Important Behavior
------------------
• Already-numbered files are NEVER renamed again.
• Prompts stay paired to their correct image number.
• Orphan .txt files (no matching image) are left untouched.
• If rerun later, new images continue numbering automatically.
• Safe to run repeatedly in the same folder.


Flags
-----

-r / --recursive
    Start at the folder WHERE THE SCRIPT EXISTS and process every subfolder depth‑first.
    Skips any folder named "backup".

--no_backup
    Do not create backup folders and do not copy originals.
    Faster but irreversible.

--clean_up
    Recursively delete ALL folders named "backup" under the processing root.
    (Use with --dry_run first to preview.)

--clean_up_scripts
    Recursively delete duplicate files named "sort_images.py"
    found in subfolders under the script’s directory.
    The root script itself is NEVER deleted.

--overwrite
    Allows replacing existing destination files.
    (Backups still occur unless --no_backup is set.)

--backup_dir PATH
    Store backups in a specified location instead of each folder’s local "backup".

--dry_run
    Shows what WOULD happen without changing files.

--verbose
    Shows detailed actions.

--log_to_file
    Saves logs to "image_sorting.log".

--log_level
    DEBUG, INFO, WARNING, ERROR, CRITICAL

--naming_convention
    "{index}"          -> 1.png
    "{index}_{random}" -> 1_ab12cd.png

--file_extensions
    Override supported image extensions.

--assume_yes
    Skip confirmation prompts.


Command Examples
----------------

1) Basic organize current folder
--------------------------------
python sort_images.py .

Result:
- Hash images renamed sequentially
- Prompts paired
- Backups created in ./backup


2) Safe rerun after adding images
---------------------------------
python sort_images.py .

Result:
- Existing numbered images unchanged
- New images continue numbering


3) Process all Stable Diffusion sessions
----------------------------------------
python sort_images.py -r

Result:
- Starts in the script’s folder
- Walks every subfolder depth‑first
- Organizes each dataset folder automatically


4) Fast dataset ingest (no backups)
-----------------------------------
python sort_images.py -r --no_backup

Result:
- Same as recursive
- No backups created
- Faster processing


5) Preview before running
-------------------------
python sort_images.py -r --dry_run --verbose

Result:
- Displays exactly what would happen
- No files changed


6) Clean backup folders
-----------------------
Preview:
python sort_images.py -r --clean_up --dry_run

Delete:
python sort_images.py -r --clean_up

Result:
- Removes every "backup" directory under script root


7) Remove duplicate copies of the script
----------------------------------------
Preview:
python sort_images.py -r --clean_up_scripts --dry_run

Delete duplicates:
python sort_images.py -r --clean_up_scripts

Result:
- Deletes all subfolder "sort_images.py"
- Keeps the root script intact


8) Full maintenance run
-----------------------
python sort_images.py -r --clean_up --clean_up_scripts --no_backup

Result:
- Removes backup folders
- Removes duplicate scripts
- Organizes all image datasets
- Leaves a clean numbered dataset tree


Recommended Workflow
--------------------
Generate images -> Drop into folders -> Run script -> Dataset auto‑organized

You can safely run this script repeatedly.
