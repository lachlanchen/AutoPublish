import os
import csv
import re
import traceback
import zipfile
import json

import tornado.web
import tornado.ioloop
import tornado.autoreload
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor, as_completed
from xhs_pub import XiaoHongShuPublisher
from bilibili_pub import BilibiliPublisher
from douyin_pub import DouyinPublisher
from y2b_pub import YouTubePublisher
from selenium.webdriver.chrome.service import Service

import subprocess

from utils import bring_to_front

# Global variables for paths and publishers
logs_folder_root = '/home/lachlan/Projects/auto-publish/logs'
autopublish_folder_root = '/home/lachlan/Projects/auto-publish/videos'
videos_db_path = '/home/lachlan/Projects/auto-publish/videos_db.csv'
processed_path = '/home/lachlan/Projects/auto-publish/processed.csv'
transcription_root = "/home/lachlan/Projects/auto-publish/transcription_data"
upload_url = 'http://lachlanserver:8081/upload'
process_url = 'http://lachlanserver:8081/video-processing'
chromedriver_path = '/usr/lib/chromium-browser/chromedriver'

# Ensure the logs and database files exist
os.makedirs(logs_folder_root, exist_ok=True)
open(videos_db_path, 'a').close()
open(processed_path, 'a').close()

# Function to create a new WebDriver instance
def create_new_driver(port=5003):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{str(port)}")
    service = Service(executable_path=chromedriver_path)
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

# Define the clean_bmp function
def clean_bmp(text):
    # Replace non-BMP characters with spaces
    cleaned_text = ''.join(char if ord(char) < 65536 else '' for char in text)
    return cleaned_text


# def bring_to_front(window_name_pattern):
#     try:
#         # List all Chromium windows
#         window_list = subprocess.check_output(["xdotool", "search", "--name", "Chromium"]).decode().strip().split('\n')
#         # Iterate through the list of window IDs
#         for window_id in window_list:
#             # Get the name of each window using its ID
#             window_name = subprocess.check_output(["xdotool", "getwindowname", window_id]).decode().strip()
#             # Check if the window name matches any of the patterns provided
#             if any(text in window_name for text in window_name_pattern):
#                 # If a match is found, activate the window
#                 subprocess.run(["xdotool", "windowactivate", "--sync", window_id])
#                 # Optionally, add a brief pause to ensure the window comes to the front
#                 subprocess.run(["sleep", "1"])
#                 break  # Exit the loop after the first match
#     except subprocess.CalledProcessError as e:
#         print(f"Error: {e.output.decode()}")


# @tornado.web.stream_request_body
class PublishHandler(tornado.web.RequestHandler):
    def initialize(self, transcription_root, chromedriver_path):
        self.transcription_root = transcription_root
        self.chromedriver_path = chromedriver_path

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def create_new_driver(self, port):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{str(port)}")
        service = Service(executable_path=self.chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        return driver


    def get(self):

        print("test")

        self.write("test")

    # @tornado.web.stream_request_body
    def post(self):
        # Extract filename from form fields or use current datetime as default
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = self.get_argument('filename')
        # basename = Path(filename_provided).stem
        # Use provided filename with timestamp if it's not the default timestamp
        # filename = f"{basename}_{timestamp}.zip" if basename != timestamp else filename_provided
        
        
        # Define path for the zip file
        video_name_without_ext = Path(filename).stem
        transcription_dir = os.path.join(self.transcription_root, video_name_without_ext)
        os.makedirs(transcription_dir, exist_ok=True)
        transcription_path = os.path.join(transcription_dir, filename)

        # Write the received content to the file
        with open(transcription_path, 'wb') as f:
            f.write(self.request.body)

        # Read publishing options from request
        publish_xhs = self.get_argument('publish_xhs', 'false').lower() == 'true'
        publish_bilibili = self.get_argument('publish_bilibili', 'false').lower() == 'true'
        publish_douyin = self.get_argument('publish_douyin', 'false').lower() == 'true'
        publish_y2b = self.get_argument('publish_y2b', 'false').lower() == 'true'
        test_mode = self.get_argument('test', 'false').lower() == 'true'


        # Unzip the file
        with zipfile.ZipFile(transcription_path, 'r') as zip_ref:
            zip_ref.extractall(transcription_dir)
        
        # Process the files inside the ZIP
        try:
            metadata_json_path = os.path.join(transcription_dir, f"{Path(filename).stem}_metadata.json")
            if os.path.exists(metadata_json_path):
                with open(metadata_json_path, 'r', encoding='utf-8') as json_file:
                    metadata = json.load(json_file)
                    metadata["title"] = clean_title(metadata["title"])
                    # Clean the description fields
                    fields_to_clean = ["brief_description", "middle_description", "long_description"]
                    for field in fields_to_clean:
                        metadata[field] = clean_bmp(metadata[field])

                    metadata_en = metadata["english_version"]
                    metadata_en["title"] = clean_title(metadata_en["title"])
                    # Clean the description fields
                    fields_to_clean = ["brief_description", "middle_description", "long_description"]
                    for field in fields_to_clean:
                        metadata_en[field] = clean_bmp(metadata_en[field])

                
                video_filename = metadata.get('video_filename', None)
                cover_filename = metadata.get('cover_filename', None)
                path_mp4 = os.path.join(transcription_dir, video_filename) if video_filename else None
                path_cover = os.path.join(transcription_dir, cover_filename) if cover_filename else None

                publishers = []
                if publish_xhs:
                    xhs_publisher = XiaoHongShuPublisher(self.create_new_driver(5003), path_mp4, path_cover, metadata, test_mode)
                    publishers.append((xhs_publisher, 'XiaoHongShu'))
                if publish_douyin:
                    douyin_publisher = DouyinPublisher(self.create_new_driver(5004), path_mp4, path_cover, metadata, test_mode)
                    publishers.append((douyin_publisher, 'Douyin'))
                if publish_bilibili:
                    bilibili_publisher = BilibiliPublisher(self.create_new_driver(5005), path_mp4, path_cover, metadata, test_mode)
                    publishers.append((bilibili_publisher, 'Bilibili'))
                if publish_y2b:
                    y2b_publisher = YouTubePublisher(self.create_new_driver(9222), path_mp4, path_cover, metadata_en, test_mode)
                    publishers.append((y2b_publisher, 'YouTube'))

                # with ThreadPoolExecutor(max_workers=len(publishers)) as executor:
                #     future_to_publisher = {executor.submit(publish_platform, publisher, name): name for publisher, name in publishers}
                #     for future in as_completed(future_to_publisher):
                #         future.result()

                for publisher, name in publishers:

                    if name == 'XiaoHongShu':
                        bring_to_front(["小红书", "你访问的页面不见了"])
                    elif name == 'Douyin':
                        bring_to_front(["抖音"])
                    elif name == 'Bilibili':
                        bring_to_front(["哔哩哔哩"])
                    elif name == 'YouTube':
                        bring_to_front(["YouTube"])

                    publisher.publish()

                self.write(json.dumps({"message": f"Published the content from {filename}"}))
            else:
                self.write(json.dumps({"error": f"Metadata JSON file not found in {transcription_dir}"}))
        except Exception as e:
            self.write(json.dumps({"error": f"An error occurred: {str(e)}"}))
            traceback.print_exc()

def make_app():
    # transcription_path = "/home/lachlan/Projects/auto-publish/transcription_data"
    # chromedriver_path = '/usr/lib/chromium-browser/chromedriver'
    return tornado.web.Application([
        (r"/publish", PublishHandler, dict(transcription_root=transcription_root, chromedriver_path=chromedriver_path)),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8081, max_body_size=10*1024 * 1024 * 1024)
    tornado.autoreload.start()
    tornado.ioloop.IOLoop.current().start()
