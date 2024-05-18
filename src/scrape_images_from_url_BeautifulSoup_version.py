import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO

# Custom printf function
def printf(format, *args):
    sys.stdout.write(format % args + '\n')
    
# Recursive function to find and download images within div elements
def find_and_download_images(container, base_url, folder_path):
    '''
    # DEBUG Print details of the endpoint response
    # Print result of all divs with the specific ID
    printf("Found divs: %s.\n", 
       container)
    '''
    
    # for all direct children
    child_list = container.find_all("div", { "class" : "image-viewer-main image-viewer-container" })
    
    for child in child_list:
        print (child)
        
    for child in child_list():
        print (child)

    # Find all img tags within the container
    for div_tag in container.find_all('div'):
        div_src = div_tag.get('src') or div_tag.get('data-src')
        alt_text = div_tag.get('alt', 'unnamed_image').replace(' ', '_').replace('/', '_')
        if div_src:
            div_src = urljoin(base_url, div_src)  # Ensure div_src is an absolute URL
            download_image(div_src, alt_text, folder_path)
    
    # Recursively search for img tags within nested divs
    for div in container.find_all('div', recursive=False):
        find_and_download_images(div, base_url, folder_path)
        
# Function to process a given URL
def process_url(url, folder_path):
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)

    response.raise_for_status()  # Raise an exception for HTTP errors

    soup = BeautifulSoup(response.text, 'html.parser')
    
    '''
    # DEBUG Print details of the endpoint response
    printf("1. Response from url: '%s'.\n2. Response text: %s.\n3. Response code: %s.\n4. Response headers: %s\n", 
       response.url, response.text, response.status_code, response.headers)
    '''
    
    # Start the recursive image download process from the top-level of the HTML
    find_and_download_images(soup, url, folder_path)


# Function to download image from its direct source
def download_image(img_url, alt_text, folder_path):
    try:
        img_resp = requests.get(img_url, stream=True)
        img_resp.raise_for_status()  # Raise an exception for HTTP errors

        # Load the image to get its size and format
        img_file = Image.open(BytesIO(img_resp.content))
        img_format = img_file.format
        img_size = len(img_resp.content)

        # Generate the filename
        safe_alt_text = alt_text.replace(' ', '_').replace('/', '_')
        file_name = f"{safe_alt_text}.{img_format.lower()}"
        file_path = os.path.join(folder_path, file_name)

        # Save the image file
        with open(file_path, 'wb') as f:
            for chunk in img_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        # Print details of the downloaded image
        printf("Downloaded %s with resolution %dx%d, size %d bytes, format %s", 
               file_path, img_file.width, img_file.height, img_size, img_format)

    except Exception as e:
        printf("Failed to download %s: %s", img_url, e)

# Main function to start the process
def main():
    folder_path = './downloaded_images'
    quit_commands = {"q!", "stop", "finish", "quit", "done", "complete"}

    while True:
        url_input = input("Enter URL to download images from (or type 'q!', 'stop', 'finish', 'quit', 'done', 'complete' to quit): ").strip().lower()
        
        # Check if the input is a quit command
        if url_input in quit_commands:
            break

        # Validate if the input is a proper URL by checking for a scheme (e.g., http, https)
        if not (url_input.startswith('http://') or url_input.startswith('https://')):
            printf("Invalid URL entered. Please enter a valid URL or a quit command.")
            continue
        
        # Ensure the folder_path exists
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)

        # Process the URL
        process_url(url_input, folder_path)

if __name__ == "__main__":
    main()
