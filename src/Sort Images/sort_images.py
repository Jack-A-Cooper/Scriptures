import os

def rename_images():
    # Get the current working directory
    current_dir = os.getcwd()
    
    # List all files in the directory
    files = os.listdir(current_dir)
    
    # Filter out only .jpg and .png files
    images = [file for file in files if file.endswith('.jpg') or file.endswith('.png')]
    
    # Sort the images to ensure consistent numbering
    images.sort()
    
    # Rename images
    for i, image in enumerate(images, start=1):
        # Get the file extension
        file_extension = os.path.splitext(image)[1]
        # Create the new file name
        new_name = f"{i}{file_extension}"
        # Get full path of the current and new file names
        current_path = os.path.join(current_dir, image)
        new_path = os.path.join(current_dir, new_name)
        # Rename the file
        os.rename(current_path, new_path)
        print(f"Renamed {current_path} to {new_path}")

if __name__ == "__main__":
    rename_images()
