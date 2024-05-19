from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import logging

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

CHROMEDRIVER_PATH = 'D:/Chromedriver/chromedriver.exe'

def test_chromedriver():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        logging.info("ChromeDriver started successfully.")
        
        driver.get("http://www.google.com")
        logging.info(f"Page title: {driver.title}")
        
        driver.quit()
        logging.info("ChromeDriver session ended.")
    except Exception as e:
        logging.error(f"Error starting ChromeDriver: {e}")

if __name__ == "__main__":
    test_chromedriver()
