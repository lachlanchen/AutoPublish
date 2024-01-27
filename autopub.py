import os
import csv
import re
import argparse
import traceback
import zipfile
import json
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor, as_completed
from xhs_pub import XiaoHongShuPublisher
from bilibili_pub import BilibiliPublisher
from douyin_pub import DouyinPublisher
from process_video import VideoProcessor
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.chrome.service import Service

chromedriver_path = '/usr/lib/chromium-browser/chromedriver'
service = Service(executable_path=chromedriver_path)

# Define video file pattern
video_file_pattern = re.compile(r'.+\.(mp4|mov|avi|flv|wmv|mkv)$', re.IGNORECASE)

# Paths for the folders and files
# logs_folder_path = '/Users/lachlan/Documents/iProjects/auto-publish/logs'
# autopublish_folder_path = '/Users/lachlan/Nutstore Files/Vlog/AutoPublish'
# videos_db_path = '/Users/lachlan/Documents/iProjects/auto-publish/videos_db.csv'
# processed_path = '/Users/lachlan/Documents/iProjects/auto-publish/processed.csv'
logs_folder_path = '/home/lachlan/Projects/auto-publish/logs'
autopublish_folder_path = '/home/lachlan/Projects/auto-publish/videos'
videos_db_path = '/home/lachlan/Projects/auto-publish/videos_db.csv'
processed_path = '/home/lachlan/Projects/auto-publish/processed.csv'

# Ensure the logs and database files exist
os.makedirs(logs_folder_path, exist_ok=True)
open(videos_db_path, 'a').close()
open(processed_path, 'a').close()



# Function to read CSV and get a list of filenames
def read_csv(csv_path):
    with open(csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0] for row in reader]

# Function to check if a file is listed in a CSV, and if not, add it
def update_csv_if_new(file_path, csv_path):
    existing_files = read_csv(csv_path)
    if file_path not in existing_files:
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([file_path])

# Function to create a new WebDriver instance
def create_new_driver(port=5003):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{str(port)}")
    # driver = webdriver.Chrome(options=options)
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver
    
# Helper function to publish on a platform and handle exceptions
def publish_platform(publisher, platform_name):
    try:
        print(f"Publishing on {platform_name}...")
        publisher.publish()
        print(f"Successfully published on {platform_name}.")
        return 1
    except Exception as e:
        print(f"Failed to publish on {platform_name}: {e}")
        traceback.print_exc()
        return 0

def clean_title(title):
    # Define a regex pattern that matches Chinese characters, English letters, numbers, Japanese characters, and punctuation
    pattern = r'[\u4e00-\u9fff\u0030-\u0039\u0041-\u005a\u0061-\u007a\u3000-\u303f\uff00-\uffef]+'

    # Find all substrings that match the pattern
    matches = re.findall(pattern, title)

    # Join the matches to get the cleaned title
    cleaned_title = ''.join(matches)
    
    return cleaned_title

# Function to process and publish the file based on given parameters
def process_file(
    file_path, transcription_path, upload_url, process_url, 
    publish_xhs, publish_bilibili, publish_douyin, 
    test_mode, use_cache=False, driver=None):
    success = 0
    # Create an instance of VideoProcessor
    processor = VideoProcessor(upload_url, process_url, file_path, transcription_path)
    zip_file_path = processor.process_video(use_cache=use_cache)

    zip_file_name = Path(zip_file_path).stem
    transcription_path = os.path.join(transcription_path, zip_file_name)
    os.makedirs(transcription_path, exist_ok=True)
    
    # Unzip the file
    if zip_file_path and os.path.exists(zip_file_path):
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            print("Extracting zipfile...")
            zip_ref.extractall(transcription_path)
        
        # Read the metadata JSON file
        metadata_json_path = os.path.join(transcription_path, f"{Path(file_path).stem}_metadata.json")
        print("metadata_json_path: ", metadata_json_path)
        if os.path.exists(metadata_json_path):
            with open(metadata_json_path, 'r', encoding='utf-8') as json_file:
                metadata = json.load(json_file)
                metadata["title"] = clean_title(metadata["title"])
            
            # Construct paths for the processed video and cover using filenames from the metadata
            video_filename = metadata.get('video_filename', None)
            cover_filename = metadata.get('cover_filename', None)
            
            # Concatenate the transcription_path with filenames to get full paths
            path_mp4 = os.path.join(transcription_path, video_filename) if video_filename else None
            path_cover = os.path.join(transcription_path, cover_filename) if cover_filename else None

            # Create a new driver for each publishing process
            xhs_driver = create_new_driver(5003) if driver is None else driver
            douyin_driver = create_new_driver(5004) if driver is None else driver
            bilibili_driver = create_new_driver(5005) if driver is None else driver

            
            if not path_mp4 or not path_cover:
                print("Processed video or cover file not found. Exiting...")
            else:
                publishers = []
                if publish_xhs:
                    xhs_publisher = XiaoHongShuPublisher(
                        driver=xhs_driver,
                        path_mp4=path_mp4,
                        path_cover=path_cover,
                        metadata=metadata,
                        test=test_mode
                    )
                    publishers.append((xhs_publisher, 'XiaoHongShu'))

                if publish_douyin:
                    douyin_publisher = DouyinPublisher(
                        driver=douyin_driver,
                        path_mp4=path_mp4,
                        path_cover=path_cover,
                        metadata=metadata,
                        test=test_mode
                    )
                    publishers.append((douyin_publisher, 'Douyin'))

                if publish_bilibili:
                    bilibili_publisher = BilibiliPublisher(
                        driver=bilibili_driver,
                        path_mp4=path_mp4,
                        path_cover=path_cover,
                        metadata=metadata,
                        test=test_mode
                    )
                    publishers.append((bilibili_publisher, 'Bilibili'))

                # Publishing in parallel using ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=len(publishers)) as executor:
                    future_to_publisher = {executor.submit(publish_platform, publisher, name): name for publisher, name in publishers}
                    for future in as_completed(future_to_publisher):
                        success += future.result()

                # for publisher, name in publishers:
                #     publisher.publish()

        else:
            print(f"Metadata JSON file not found in {transcription_path}")
    else:
        print(f"Zip file not found at {zip_file_path}")

    return success

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--pub-xhs', action='store_true', help="Publish on XiaoHongShu")
    parser.add_argument('--pub-bilibili', action='store_true', help="Publish on Bilibili")
    parser.add_argument('--pub-douyin', action='store_true', help="Publish on DouYin")
    parser.add_argument('--test', action='store_true', help="Run in test mode")
    parser.add_argument('--use-cache', action='store_true', help="Use cache")
    args = parser.parse_args()

    # Determine publishing platforms based on provided arguments
    platforms_provided = args.pub_xhs or args.pub_bilibili or args.pub_douyin
    publish_xhs = args.pub_xhs or not platforms_provided
    publish_bilibili = args.pub_bilibili or not platforms_provided
    publish_douyin = args.pub_douyin or not platforms_provided
    test_mode = args.test
    use_cache = args.use_cache

    current_datetime = datetime.now()
    log_filename = f"{current_datetime.strftime('%Y-%m-%d %H-%M-%S')}.txt"
    log_file_path = os.path.join(logs_folder_path, log_filename)
    upload_url = 'http://lachlanserver:8081/upload'
    process_url = 'http://lachlanserver:8081/video-processing'
    transcription_path = "/home/lachlan/Projects/auto-publish/transcription_data"

    with open(log_file_path, 'a') as log_file:
        log_file.write(f"Log entry at {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("Updated files:\n")
        
        processed_files = read_csv(processed_path)
        
        # Check each file in the autopublish folder
        for filename in os.listdir(autopublish_folder_path):
            if filename.startswith("preprocessed"):
                update_csv_if_new(filename, processed_path)
                continue

            if video_file_pattern.match(filename):
                file_path = os.path.join(autopublish_folder_path, filename)
                if os.path.isfile(file_path):
                    # Check and update videos_db.csv
                    update_csv_if_new(filename, videos_db_path)
                    
                    # Log the new file
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M-%S')
                    log_file.write(f"New video file: {filename}, last modified: {mod_time}\n")
                    
                    # If not processed, process the file and update processed.csv
                    if filename not in processed_files:
                        success = process_file(
                            file_path, 
                            transcription_path, 
                            upload_url, 
                            process_url, 
                            publish_xhs=publish_xhs,
                            publish_bilibili=publish_bilibili,
                            publish_douyin=publish_douyin,
                            test_mode=test_mode,
                            use_cache=use_cache
                        )
                        if success > 0:
                            update_csv_if_new(filename, processed_path)

