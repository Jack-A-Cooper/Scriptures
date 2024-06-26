import os
import time
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ImageScraper:
    def __init__(self, chromedriver_path, save_directory='./downloaded_images', headless=True):
        self.chromedriver_path = chromedriver_path
        self.save_directory = save_directory
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
        chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        chrome_service = Service(self.chromedriver_path)
        
        try:
            self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            logging.info("Selenium WebDriver setup complete.")
        except Exception as e:
            logging.error(f"Error setting up Selenium WebDriver: {e}")
            raise

    @staticmethod
    def create_directory(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def is_valid_url(url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def extract_image_urls(self, url):
        image_urls = []
        try:
            self.driver.get(url)
            # Scroll to the bottom to load all images
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for the page to load
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Wait for images to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "img"))
            )
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            for img in soup.find_all('img'):
                img_url = img.attrs.get('src')
                if img_url and img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url:
                    img_url = urljoin(url, img_url)
                if self.is_valid_url(img_url):
                    image_urls.append(img_url)
        except Exception as e:
            logging.error(f"Error fetching URL {url}: {e}")
        return image_urls

    def download_image(self, url, save_path):
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            img.save(save_path)
            return True
        except UnidentifiedImageError:
            logging.error(f"Cannot identify image file {url}")
            return False
        except Exception as e:
            logging.error(f"Failed to download {url}: {e}")
            return False

    def scrape_images(self, start_url):
        self.create_directory(self.save_directory)

        image_urls = self.extract_image_urls(start_url)

        if not image_urls:
            logging.warning(f"No images found at {start_url}")
            return

        with tqdm(total=len(image_urls), desc=f"Downloading images from {start_url}", leave=False) as pbar:
            for img_url in image_urls:
                img_name = os.path.join(self.save_directory, os.path.basename(urlparse(img_url).path))
                if self.download_image(img_url, img_name):
                    logging.info(f"Downloaded {img_url} to {img_name}")
                pbar.update(1)

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

                self.scrape_images(start_url)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            if self.driver:
                self.driver.quit()
            logging.info("ChromeDriver session ended.")

if __name__ == "__main__":
    scraper = ImageScraper(chromedriver_path='D:/Chromedriver/chromedriver.exe')
    scraper.run()
