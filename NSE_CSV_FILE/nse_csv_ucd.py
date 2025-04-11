import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import os
import logging
import sys

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("download_script.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

download_dir = os.getcwd()

if not os.path.exists(download_dir):
    os.makedirs(download_dir)


options = uc.ChromeOptions()
options.headless = False
# options.add_argument("--headless=new") 
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--disable-gpu")
# options.add_argument("--disable-software-rasterizer")
# options.add_argument("--remote-debugging-port=9222")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

# Start the Chrome driver
driver = uc.Chrome(options=options)

params = {'behavior':'allow', 'downloadPath':os.getcwd()}
driver.execute_cdp_cmd('Page.setDownloadBehavior', params)

driver.get("https://www.nseindia.com/all-reports")

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
)

def wait_for_download_to_finish(timeout=60):
    logging.info("Waiting for download to finish...")
    start_time = time.time()
    while True:
        files = os.listdir(download_dir)
        in_progress = [f for f in files if f.endswith(".crdownload")]
        if not in_progress:
            completed_files = [f for f in files if f.endswith(".csv")]
            if completed_files:
                logging.info("Download finished. File(s): " + ", ".join(completed_files))
                return True
            else:
                logging.warning("No CSV File Found")
                return False
        elif time.time() - start_time > timeout:
            logging.warning("Download did not complete within the timeout period.")
            return False
        else:
            time.sleep(1)

success = False
logging.info("Script Started")

# First attempt: UI interaction
try:
    logging.info("Attempting to interact with UI to trigger download...")

    input_field = WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.ID, 'crEquityDailySearch'))
    )

    input_field.clear()
    input_field.send_keys("Full Bhavcopy")
    time.sleep(2)
    input_field.send_keys(Keys.RETURN)
    time.sleep(4)

    label = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Full Bhavcopy and Security Deliverable data')]"))
    )

    download_link = label.find_element(By.XPATH, ".//following::span[contains(@class, 'reportDownloadIcon')]//a[contains(@class, 'pdf-download-link')]")
    download_link.click()
    time.sleep(5)
    if wait_for_download_to_finish():
        logging.info("Download via direct URL completed.")

    success = True
    logging.info("Download triggered via UI.")
except Exception as e:
    logging.error("First attempt (UI) failed:", exc_info=True)

# Second attempt: Use hardcoded URL if UI fails
if not success:
    try:
        logging.info("Trying hardcoded URL download...")

        today = datetime.now().strftime("%d%m%Y")
        today = '09042025'  
        logging.info(f"Date: {today}")
        download_url = f'https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{today}.csv'

        logging.info(f"Download URL: {download_url}")
        driver.get(download_url)
        time.sleep(5)
        if wait_for_download_to_finish():
            logging.info("Download via direct URL completed.")

        logging.info("Download via direct URL completed.")
    except Exception as e:
        logging.error("Second attempt (download URL) failed:", exc_info=True)

logging.info("Script execution completed.")
