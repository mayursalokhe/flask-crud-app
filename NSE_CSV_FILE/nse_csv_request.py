import requests
from datetime import datetime
import os
import logging
import sys
import time

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

def wait_for_download_to_finish(filename, timeout=60):
    logging.info(f"Waiting for download of {filename} to finish...")
    start_time = time.time()
    while True:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            logging.info(f"Download finished. File: {filename}")
            return True
        elif time.time() - start_time > timeout:
            logging.warning(f"Download did not complete within the timeout period for {filename}.")
            return False
        else:
            time.sleep(1)

success = False
logging.info("Script Started")

try:
    logging.info("Trying hardcoded URL download...")

    today = datetime.now().strftime("%d%m%Y")
    today = '09042025'  
    logging.info(f"Date: {today}")
    download_url = f'https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{today}.csv'

    logging.info(f"Download URL: {download_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

    response = requests.get(download_url, headers=headers, stream=True, timeout=30) 

    if response.status_code == 200:
        download_file = os.path.join(download_dir, f"sec_bhavdata_full_{today}.csv")
        with open(download_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):  
                f.write(chunk)
        logging.info(f"Download initiated for {download_file}")

        if wait_for_download_to_finish(download_file):
            logging.info(f"Download completed for {download_file}.")
        else:
            logging.warning(f"Failed to download the file within the timeout period.")
    else:
        logging.error(f"Failed to retrieve the file. HTTP Status Code: {response.status_code}")
    
    logging.info("Download via direct URL completed.")
    success = True

except requests.exceptions.Timeout:
    logging.error("Request timed out. The server took too long to respond.")
except requests.exceptions.RequestException as e:
    logging.error(f"An error occurred while making the request: {e}")
except Exception as e:
    logging.error("Attempt to download via URL failed:", exc_info=True)

logging.info("Script execution completed.")
