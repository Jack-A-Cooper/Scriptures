import os
from PIL import Image

def convert_jpg_large_to_jpg(directory):
    # Iterate through all files in the current directory
    for filename in os.listdir(directory):
        # Check if the file is a .jpg_large file
        if filename.endswith('.jpg_large'):
            # Construct the new filename by replacing .jpg_large with .jpg
            new_filename = filename.replace('.jpg_large', '.jpg')
            os.rename(filename, new_filename)
            print(f'Renamed {filename} to {new_filename}')

# Specify the directory to scan for .jpg_large files, '.' means the current directory
directory = '.'
convert_jpg_large_to_jpg(directory)
