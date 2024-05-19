import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import logging
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class ImageScraper:
    def __init__(self, chromedriver_path, save_directory='./downloaded_images', max_depth=2, headless=True):
        self.chromedriver_path = chromedriver_path
        self.save_directory = save_directory
        self.max_depth = max_depth
        self.headless = headless
        self.driver = None
        self.setup_logging()

    def setup_logging(self):
        log_file = 'scraper.log'
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[logging.FileHandler(log_file), logging.StreamHandler()])
        logging.info("Logging setup complete.")

    def setup_selenium(self):
        logging.info("Setting up Selenium WebDriver.")
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_service = Service(self.chromedriver_path)
        
        try:
            self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            logging.info("Selenium WebDriver setup complete.")
        except Exception as e:
            logging.error(f"Error setting up Selenium WebDriver: {e}")
            raise

    @staticmethod
    def get_domain(url):
        return urlparse(url).netloc

    @staticmethod
    def create_directory(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def is_valid_url(url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def extract_imgur_image_urls(self, url):
        image_urls = []
        try:
            self.driver.get(url)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            for img in soup.find_all('img'):
                img_url = img.attrs.get('src')
                if img_url and img_url.startswith('//'):
                    img_url = 'https:' + img_url
                if self.is_valid_url(img_url):
                    image_urls.append(img_url)
        except Exception as e:
            logging.error(f"Error fetching Imgur URL {url}: {e}")
        return image_urls

    def extract_image_urls(self, url):
        domain = self.get_domain(url)
        if 'imgur.com' in domain:
            return self.extract_imgur_image_urls(url)

        image_urls = []
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for img in soup.find_all('img'):
                img_url = img.attrs.get('src')
                if not img_url:
                    continue
                img_url = urljoin(url, img_url)
                if self.is_valid_url(img_url):
                    image_urls.append(img_url)
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
        return image_urls

    @staticmethod
    def download_image(url, save_path):
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            content_type = response.headers['Content-Type']
            if 'svg' in content_type:
                logging.info(f"Skipping SVG image: {url}")
                return False
            img = Image.open(BytesIO(response.content))
            img.save(save_path)
            return True
        except UnidentifiedImageError:
            logging.error(f"Cannot identify image file {url}")
            return False
        except Exception as e:
            logging.error(f"Failed to download {url}: {e}")
            return False

    def depth_first_image_scraper(self, start_url):
        visited = set()
        stack = [(start_url, 0)]
        domain = self.get_domain(start_url)
        self.create_directory(self.save_directory)

        while stack:
            url, depth = stack.pop()
            if depth > self.max_depth or url in visited:
                continue

            visited.add(url)
            logging.info(f"Visiting {url}")
            image_urls = self.extract_image_urls(url)

            if not image_urls:
                logging.warning(f"No images found at {url}")
                continue

            with tqdm(total=len(image_urls), desc=f"Downloading images from {url}", leave=False) as pbar:
                for img_url in image_urls:
                    img_name = os.path.join(self.save_directory, os.path.basename(urlparse(img_url).path))
                    if self.download_image(img_url, img_name):
                        logging.info(f"Downloaded {img_url} to {img_name}")
                    pbar.update(1)

            if depth < self.max_depth:
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        next_url = urljoin(url, a['href'])
                        if self.is_valid_url(next_url) and domain in next_url and next_url not in visited:
                            stack.append((next_url, depth + 1))
                except requests.RequestException as e:
                    logging.error(f"Error fetching {url}: {e}")

    def run(self):
        try:
            self.setup_selenium()
            while True:
                start_url = input("Enter URL to scrape (or 'q!', 'q', 'exit', 'terminate' to quit): ")
                if start_url.lower() in {'q!', 'q', 'exit', 'terminate'}:
                    logging.info("Exiting the scraper.")
                    break
                if not self.is_valid_url(start_url):
                    logging.error("Invalid URL. Please try again.")
                    continue

                self.depth_first_image_scraper(start_url)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            if self.driver:
                self.driver.quit()
            logging.info("ChromeDriver session ended.")


if __name__ == "__main__":
    scraper = ImageScraper(chromedriver_path='D:/Chromedriver/chromedriver.exe')
    scraper.run()
