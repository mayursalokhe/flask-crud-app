import httpx
import os
import sys
import time
import logging
from datetime import datetime, time as dtime

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("NSE_CSV_File_Download.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

download_dir = os.getcwd()
# download_dir = ''
# if not os.path.exists(download_dir):
#     os.makedirs(download_dir)

# Function to confirm file write completed
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

def download_nse_csv():
    # Time configuration
    start_time_window = dtime(17, 0)  # 5 PM
    end_time_window = dtime(19, 0)    # 7 PM
    check_interval_minutes = 1

    logging.info("Script Started Monitoring...")
    downloaded = False

    while True:
        now = datetime.now()
        current_time = now.time()

        if start_time_window <= current_time <= end_time_window and not downloaded:
            try:
                today = now.strftime("%d%m%Y")
                logging.info(f"Checking for file dated: {today}")
                download_url = f'https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{today}.csv'

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Connection": "keep-alive",
                    "Host": "nsearchives.nseindia.com",
                    "Referer": "https://www.nseindia.com/"
                }

                with httpx.Client(http2=True, timeout=30, headers=headers) as client:
                    logging.info(f"Downloading from: {download_url}")
                    response = client.get(download_url)

                    logging.info(f"Status code: {response.status_code}")
                    if response.status_code == 200:
                        download_file = os.path.join(download_dir, f"sec_bhavdata_full_{today}.csv")
                        with open(download_file, "wb") as f:
                            f.write(response.content)

                        if wait_for_download_to_finish(download_file):
                            logging.info(f"Download completed for {download_file}.")
                            downloaded = True
                        else:
                            logging.warning("Download failed or file not fully written.")
                    else:
                        logging.info(f"File not available yet. Status code: {response.status_code}")

            except httpx.RemoteProtocolError as e:
                logging.error(f"RemoteProtocolError: {e}")
            except httpx.RequestError as e:
                logging.error(f"HTTPX RequestError: {e}")
            except Exception as e:
                logging.error("Unexpected error occurred:", exc_info=True)

            time.sleep(check_interval_minutes * 60)

        elif current_time > end_time_window:
            logging.info("Time window ended. Exiting script.")
            break
        else:
            logging.info("Waiting for 5 PM to begin download attempts...")
            time.sleep(60)

    logging.info("Script execution completed.")

if __name__ == "__main__":
    download_nse_csv()
