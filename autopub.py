import os
import csv
import re
from datetime import datetime
from xhs_pub import XiaoHongShuPublisher
from bilibili_pub import BilibiliPublisher
from douyin_pub import DouyinPublisher
from process_video import VideoProcessor

import selenium
from selenium import webdriver
import pathlib
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException, TimeoutException
import time

import zipfile

import os
import requests
from urllib.parse import urlparse
from pathlib import Path

import json
import json5

# Define video file pattern
video_file_pattern = re.compile(r'.+\.(mp4|mov|avi|flv|wmv|mkv)$', re.IGNORECASE)

# Paths for the folders and files
logs_folder_path = '/Users/lachlan/Documents/iProjects/auto-publish/logs'
autopublish_folder_path = '/Users/lachlan/Nutstore Files/Vlog/AutoPublish'
videos_db_path = '/Users/lachlan/Documents/iProjects/auto-publish/videos_db.csv'
processed_path = '/Users/lachlan/Documents/iProjects/auto-publish/processed.csv'

# Ensure the logs and database files exist
os.makedirs(logs_folder_path, exist_ok=True)
open(videos_db_path, 'a').close()
open(processed_path, 'a').close()

# Function to create a new WebDriver instance
def create_new_driver(port=5003):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{str(port)}")
    driver = webdriver.Chrome(options=options)
    return driver

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

# Placeholder for your process function
# def process_file(file_path):
#     print(f"Processing {file_path}...")  # Placeholder
#     # Add your actual file processing code here

# # Function to update process_file
# def process_file(file_path, transcription_path, server_url, driver):
#     # Create an instance of VideoProcessor
#     processor = VideoProcessor(server_url, file_path, transcription_path)
#     zip_file_path = processor.process_video()
    
#     # Unzip the file
#     if zip_file_path and os.path.exists(zip_file_path):
#         with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:

#             print("Extracting zipfile...")
#             zip_ref.extractall(transcription_path)
        
#         # Read the metadata JSON file
#         metadata_json_path = os.path.join(transcription_path, f"{Path(file_path).stem}_metadata.json")
#         print("metadata_json_path: ", metadata_json_path)
#         if os.path.exists(metadata_json_path):
#             with open(metadata_json_path, 'r') as json_file:
#                 metadata = json.load(json_file)
#             # Extract paths for the processed video and cover
#             # path_mp4, path_cover = get_media_paths(transcription_path)
#             if not path_mp4 or not path_cover:
#                 print("Processed video or cover file not found. Exiting...")
#             else:
#                 # Create an instance of the XiaoHongShuPublisher
#                 xhs_publisher = XiaoHongShuPublisher(
#                     driver=driver,
#                     path_mp4=path_mp4,
#                     path_cover=path_cover,
#                     metadata=metadata
#                 )
#                 # Start publishing process
#                 print("Publishing...")
#                 xhs_publisher.publish()
#         else:
#             print(f"Metadata JSON file not found in {transcription_path}")
#     else:
#         print(f"Zip file not found at {zip_file_path}")

def process_file(file_path, transcription_path, server_url, driver=None):
    # Create an instance of VideoProcessor
    processor = VideoProcessor(server_url, file_path, transcription_path)
    zip_file_path = processor.process_video()
    
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
            
            # Construct paths for the processed video and cover using filenames from the metadata
            video_filename = metadata.get('video_filename', None)
            cover_filename = metadata.get('cover_filename', None)
            
            # Concatenate the transcription_path with filenames to get full paths
            path_mp4 = os.path.join(transcription_path, video_filename) if video_filename else None
            path_cover = os.path.join(transcription_path, cover_filename) if cover_filename else None


            # Create a new driver for each publishing process
            xhs_driver = create_new_driver(5003) if driver is None else driver
            bilibili_driver = create_new_driver(5003) if driver is None else driver
            douyin_driver = create_new_driver(5003) if driver is None else driver
            
            if not path_mp4 or not path_cover:
                print("Processed video or cover file not found. Exiting...")
            else:
                # Create an instance of the XiaoHongShuPublisher
                xhs_publisher = XiaoHongShuPublisher(
                    driver=xhs_driver,
                    path_mp4=path_mp4,
                    path_cover=path_cover,
                    metadata=metadata
                )
                # Start publishing process
                print("Publishing on XiaoHongShu...")
                xhs_publisher.publish()


                # Create an instance of the BilibiliPublisher
                bilibili_publisher = BilibiliPublisher(
                    driver=bilibili_driver,
                    path_mp4=path_mp4,
                    path_cover=path_cover,
                    metadata=metadata
                )

                # Start publishing process
                print("Publishing on Bilibili...")
                bilibili_publisher.publish()


                # Create an instance of the DouYinPublisher
                douyin_publisher = DouyinPublisher(
                    driver=douyin_driver,
                    path_mp4=path_mp4,
                    path_cover=path_cover,
                    metadata=metadata
                )

                # Start publishing process
                print("Publishing on Douyin...")
                douyin_publisher.publish()




                


        else:
            print(f"Metadata JSON file not found in {transcription_path}")
    else:
        print(f"Zip file not found at {zip_file_path}")

if __name__ == "__main__":
    # Create a new log entry
    current_datetime = datetime.now()
    log_filename = f"{current_datetime.strftime('%Y-%m-%d %H-%M-%S')}.txt"
    log_file_path = os.path.join(logs_folder_path, log_filename)
    server_url = 'http://lachlanserver:8080/video-processing'
    transcription_path = "/Users/lachlan/Nutstore Files/Vlog/transcription_data"

    # # Chrome options
    # options = webdriver.ChromeOptions()
    # options.add_experimental_option("debuggerAddress", "127.0.0.1:5003")

    # # Initialize the driver
    # driver = webdriver.Chrome(options=options)

    # # Check if there is an existing window to work with or if a new window should be opened
    # try:
    #     driver.current_window_handle
    # except NoSuchWindowException:
    #     driver = webdriver.Chrome(executable_path=chrome_driver_path, options=options)


    with open(log_file_path, 'a') as log_file:
        log_file.write(f"Log entry at {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("Updated files:\n")
        
        processed_files = read_csv(processed_path)
        
        # Check each file in the autopublish folder
        for filename in os.listdir(autopublish_folder_path):
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
                        process_file(file_path, transcription_path, server_url)
                        update_csv_if_new(filename, processed_path)

    print("Success")
