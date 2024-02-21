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
from pub_xhs import XiaoHongShuPublisher
from pub_bilibili import BilibiliPublisher
from pub_douyin import DouyinPublisher
from process_video import VideoProcessor
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.chrome.service import Service

chromedriver_path = '/usr/lib/chromium-browser/chromedriver'
service = Service(executable_path=chromedriver_path)


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

    # Create an instance of VideoProcessor
    processor = VideoProcessor(upload_url, process_url, file_path, transcription_path)
    zip_file_path = processor.process_video(use_cache=use_cache)

    return zip_file_path


# Function to process and publish the file based on given parameters
def process_file(
    zip_file_path, transcription_path, upload_url, process_url, 
    publish_xhs, publish_bilibili, publish_douyin, 
    test_mode, use_cache=False, driver=None):
    success = 0


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
                    pub_xhslisher = XiaoHongShuPublisher(
                        driver=xhs_driver,
                        path_mp4=path_mp4,
                        path_cover=path_cover,
                        metadata=metadata,
                        test=test_mode
                    )
                    publishers.append((pub_xhslisher, 'XiaoHongShu'))

                if publish_douyin:
                    pub_douyinlisher = DouyinPublisher(
                        driver=douyin_driver,
                        path_mp4=path_mp4,
                        path_cover=path_cover,
                        metadata=metadata,
                        test=test_mode
                    )
                    publishers.append((pub_douyinlisher, 'Douyin'))

                if publish_bilibili:
                    pub_bilibililisher = BilibiliPublisher(
                        driver=bilibili_driver,
                        path_mp4=path_mp4,
                        path_cover=path_cover,
                        metadata=metadata,
                        test=test_mode
                    )
                    publishers.append((pub_bilibililisher, 'Bilibili'))

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