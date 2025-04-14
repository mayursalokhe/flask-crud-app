import requests
from datetime import datetime, time as dtime
import os
import logging
import sys
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("NSE_CSV_File_Download.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Directory setup
download_dir = os.getcwd()

# download_dir = ''
# if not os.path.exists(download_dir):
#     os.makedirs(download_dir)

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


start_check = dtime(17, 0)  # 5 PM
end_check = dtime(19, 0)    # 7 PM
check_interval_minutes = 1  

downloaded = False
logging.info("Script Started Monitoring...")

while True:
    now = datetime.now()
    current_time = now.time()

    if start_check <= current_time <= end_check and not downloaded:
        try:
            today = now.strftime("%d%m%Y")
            logging.info(f"Checking for file dated: {today}")

            download_url = f'https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{today}.csv'
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
                    downloaded = True
                else:
                    logging.warning("File download failed or timed out.")
            else:
                logging.info(f"File not available yet (status {response.status_code}). Retrying in {check_interval_minutes} minutes.")

        except requests.exceptions.Timeout:
            logging.error("Request timed out.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
        except Exception as e:
            logging.error("Unexpected error occurred:", exc_info=True)

        time.sleep(check_interval_minutes * 60)

    elif current_time > end_check:
        logging.info("Monitoring window (5 PM to 7 PM) ended for today.")
        break
    else:
        logging.info("Waiting for 5 PM to start checking...")
        time.sleep(60)  

logging.info("Script execution completed for the day.")
