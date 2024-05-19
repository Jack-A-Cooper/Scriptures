import os
import argparse
import random
import string
import shutil
from tqdm import tqdm
import logging
from elevate import elevate

def setup_logging(log_to_file=False, log_level=logging.INFO):
    """Sets up the logging configuration."""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    if log_to_file:
        logging.basicConfig(filename='image_sorting.log', level=log_level, format=log_format)
    else:
        logging.basicConfig(level=log_level, format=log_format)
    logging.getLogger().setLevel(log_level)  # Explicitly set the root logger level

def get_random_string(length=8):
    """Generates a random string of specified length."""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def create_backup_dir(backup_dir):
    """Creates a backup directory if it does not exist."""
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        logging.info(f"Backup directory created at {backup_dir}")

def backup_file(file_path, backup_dir):
    """Backs up a file to the specified backup directory."""
    if os.path.exists(file_path):
        backup_path = os.path.join(backup_dir, os.path.basename(file_path))
        shutil.copy2(file_path, backup_path)
        logging.info(f"Backed up {file_path} to {backup_path}")
        return backup_path
    return None

def rename_file(current_path, new_path, dry_run, verbose):
    """Renames a file from current_path to new_path."""
    try:
        if dry_run:
            if verbose:
                logging.info(f"DRY RUN: Would rename {current_path} to {new_path}")
        else:
            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(current_path, new_path)
            logging.info(f"Renamed {current_path} to {new_path}")
    except Exception as e:
        logging.error(f"Error renaming {current_path} to {new_path}: {e}")

def process_txt_files(base_name, new_base_name, backup_dir, current_dir, dry_run, verbose):
    """Processes and renames associated .txt files."""
    for txt_file in os.listdir(current_dir):
        if txt_file.startswith(base_name) and txt_file.endswith('.txt'):
            suffix = txt_file[len(base_name):]
            current_txt_path = os.path.join(current_dir, txt_file)
            new_txt_name = f"{new_base_name}{suffix}"
            new_txt_path = os.path.join(current_dir, new_txt_name)
            if os.path.exists(current_txt_path):
                backup_file(current_txt_path, backup_dir)
                rename_file(current_txt_path, new_txt_path, dry_run, verbose)

def process_image(image, new_name, current_dir, backup_dir, overwrite, dry_run, verbose):
    """Processes and renames an image file and its associated .txt files."""
    current_path = os.path.join(current_dir, image)
    new_path = os.path.join(current_dir, new_name)
    base_name = os.path.splitext(image)[0]
    new_base_name = os.path.splitext(new_name)[0]
    
    process_txt_files(base_name, new_base_name, backup_dir, current_dir, dry_run, verbose)
    
    if os.path.exists(new_path):
        if overwrite:
            backup_file(new_path, backup_dir)
            rename_file(current_path, new_path, dry_run, verbose)
        else:
            logging.warning(f"Skipped {current_path} (already exists)")
    else:
        rename_file(current_path, new_path, dry_run, verbose)

def validate_directory(directory):
    """Validates if the given directory path exists and is a directory."""
    if not os.path.isdir(directory):
        logging.error(f"{directory} is not a valid directory")
        raise NotADirectoryError(f"{directory} is not a valid directory")

def confirm_backup(overwrite, num_files):
    """Asks for user confirmation before proceeding with backup/overwrite if the number of files is large."""
    if overwrite and num_files > 50:
        response = input(f"About to overwrite and backup {num_files} files. Do you want to proceed? (y/n): ")
        if response.lower() != 'y':
            logging.info("Operation cancelled by user.")
            exit()

def rename_images(current_dir, overwrite=False, backup_dir=None, dry_run=False, verbose=False, naming_convention="{index}_{random}", file_extensions=['.jpg', '.png']):
    """Renames image files in the current directory and handles their associated .txt files."""
    validate_directory(current_dir)
    os.chdir(current_dir)
    
    files = os.listdir(current_dir)
    images = [file for file in files if any(file.endswith(ext) for ext in file_extensions)]
    images.sort()

    if not images:
        logging.info("No matching image files found to rename.")
        return
    
    if backup_dir is None:
        backup_dir = os.path.join(current_dir, "backup")
    create_backup_dir(backup_dir)
    
    confirm_backup(overwrite, len(images))
    
    for i, image in enumerate(tqdm(images, desc="Processing Images", unit="image"), start=1):
        file_extension = os.path.splitext(image)[1]
        unique_id = get_random_string()
        new_name = naming_convention.format(index=i, random=unique_id) + file_extension
        process_image(image, new_name, current_dir, backup_dir, overwrite, dry_run, verbose)

def main():
    elevate()  # Elevate to admin level privileges
    parser = argparse.ArgumentParser(
        description='Rename image files in the specified directory.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Example usage:
  python sort_images.py ./images --overwrite --backup_dir ./backup --log_to_file --dry_run --verbose --log_level DEBUG --naming_convention "{index}_{random}" --file_extensions .jpg .png
        """
    )
    parser.add_argument('directory', type=str, nargs='?', default=os.getcwd(), help='Directory containing the image files to rename (default: current directory)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files')
    parser.add_argument('--backup_dir', type=str, help='Directory to store backups', default=None)
    parser.add_argument('--log_to_file', action='store_true', help='Log to a file instead of stdout')
    parser.add_argument('--dry_run', action='store_true', help='Perform a dry run without making changes')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--log_level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set the logging level')
    parser.add_argument('--naming_convention', type=str, default="{index}_{random}", help='Custom naming convention for new file names')
    parser.add_argument('--file_extensions', type=str, nargs='+', default=['.jpg', '.png'], help='File extensions to include in renaming process')
    args = parser.parse_args()
    
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    setup_logging(log_to_file=args.log_to_file, log_level=log_level)
    rename_images(
        current_dir=args.directory, 
        overwrite=args.overwrite, 
        backup_dir=args.backup_dir, 
        dry_run=args.dry_run, 
        verbose=args.verbose, 
        naming_convention=args.naming_convention, 
        file_extensions=args.file_extensions
    )

if __name__ == "__main__":
    main()
