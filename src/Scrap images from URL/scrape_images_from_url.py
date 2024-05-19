import os
import sys
import requests
from requests_html import HTMLSession
from urllib.parse import urljoin

# Custom printf function
def printf(format, *args):
    sys.stdout.write(format % args + '\n')

def download_image(img_url, folder_path):
    # Check if "logo" or ".md" appears in the img_url
    if "logo" in img_url or ".md" in img_url:
        printf("Skipping download for %s as it contains 'logo' or '.md'\n", img_url)
        return

    try:
        img_resp = requests.get(img_url, stream=True)
        img_resp.raise_for_status()  # Check if the request was successful
        file_name = os.path.basename(img_url.split('?')[0])  # Remove URL parameters
        file_path = os.path.join(folder_path, file_name)

        # Save the image
        with open(file_path, 'wb') as f:
            for chunk in img_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        printf("Downloaded image saved to %s\n", file_path)
    except Exception as e:
        printf("Failed to download %s due to %s\n", img_url, e)

def scrape_images(session, url, folder_path):
    r = session.get(url)
    # Look specifically for high-quality images in <meta> tags
    meta_images = r.html.xpath('//meta[contains(@property, "og:image")]/@content')
    for img_url in meta_images:
        img_url = urljoin(url, img_url)  # Ensure the URL is absolute
        download_image(img_url, folder_path)
    
    # Download all <img> tags in the body for completeness
    body_images = r.html.find('body img')
    for img in body_images:
        src = img.attrs.get('src') or img.attrs.get('data-src')
        src = urljoin(url, src)
        download_image(src, folder_path)
    
    printf("Processed URL: %s\n", url)

def main():
    printf("Enter a URL to scrape images from, or type 'quit' to exit.\n")
    folder_path = './downloaded_images'
    session = HTMLSession()

    while True:
        url_input = input("URL: ").strip()

        if url_input.lower() == 'quit':
            printf("Exiting program.\n")
            break

        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)

        scrape_images(session, url_input, folder_path)

if __name__ == "__main__":
    main()
