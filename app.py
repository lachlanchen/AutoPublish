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
from pub_xhs import XiaoHongShuPublisher
from pub_bilibili import BilibiliPublisher
from pub_douyin import DouyinPublisher
from pub_y2b import YouTubePublisher
from pub_shipinhao import ShiPinHaoPublisher
from login_xiaohongshu import XiaoHongShuLogin
from login_douyin import DouyinLogin
from login_shipinhao import ShiPinHaoLogin
from selenium.webdriver.chrome.service import Service

import subprocess

from utils import bring_to_front

import argparse
import threading
import time
import random

import time

# Add this import
from load_env import load_env_from_bashrc

# Load environment variables at the very beginning
try:
    load_env_from_bashrc()
except Exception as e:
    print(f"WARNING: Failed to load environment variables: {e}")
    traceback.print_exc()




is_publishing = False
# Argument parsing for configurable refresh time and port
parser = argparse.ArgumentParser(description="Auto-publish application with browser refresh feature.")
parser.add_argument('--refresh-time', type=int, default=1800, help="Time in seconds between each browser refresh.")
parser.add_argument('--port', type=int, default=8081, help="Port to listen on for the web server.")
args = parser.parse_args()
refresh_time = args.refresh_time
port = args.port


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

def run_command(command):
    try:
        print(f"Executing: {command}")
        subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)  # Short delay to ensure the command initiates properly
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute command: {e}")

def stop_and_start_chromium_sessions(
            publish_xhs=False,
            publish_bilibili=False,
            publish_douyin=False,
            publish_shipinhao=False,
            publish_y2b=False
        ):
        password = "1"  # This should be secured
        try:
            # Commands to stop existing Chromium and ChromeDriver processes
            try:
                subprocess.run(f"echo {password} | sudo -S pkill chromium-browse", shell=True, check=True)
                subprocess.run(f"echo {password} | sudo -S pkill chromedriver", shell=True, check=True)
            except:
                pass
            
            # Start new Chromium sessions, replicating what the aliases would do
            # Note: The use of shell=True and passing commands as a single string due to the complexity of commands
            start_commands = {
                "xhs": "DISPLAY=:1 chromium-browser --hide-crash-restore-bubble --remote-debugging-port=5003 --user-data-dir=\"$HOME/chromium_dev_session_5003\" https://creator.xiaohongshu.com/creator/post > \"$HOME/chromium_dev_session_logs/chromium_xhs.log\" 2>&1 &",
                "douyin": "DISPLAY=:1 chromium-browser --hide-crash-restore-bubble --remote-debugging-port=5004 --user-data-dir=\"$HOME/chromium_dev_session_5004\" https://creator.douyin.com/creator-micro/content/upload > \"$HOME/chromium_dev_session_logs/chromium_douyin.log\" 2>&1 &",
                "bilibili": "DISPLAY=:1 chromium-browser --hide-crash-restore-bubble --remote-debugging-port=5005 --user-data-dir=\"$HOME/chromium_dev_session_5005\" https://member.bilibili.com/platform/upload/video/frame > \"$HOME/chromium_dev_session_logs/chromium_bilibili.log\" 2>&1 &",
                "shipinhao": "DISPLAY=:1 chromium-browser --hide-crash-restore-bubble --remote-debugging-port=5006 --user-data-dir=\"$HOME/chromium_dev_session_5006\" https://channels.weixin.qq.com/post/create > \"$HOME/chromium_dev_session_logs/chromium_shipinhao.log\" 2>&1 &",
                "y2b": "DISPLAY=:1 chromium-browser --hide-crash-restore-bubble --remote-debugging-port=9222 --user-data-dir=\"$HOME/chromium_dev_session_9222\" https://youtube.com/upload > \"$HOME/chromium_dev_session_logs/chromium_youtube.log\" 2>&1 &"
            }

            # for platform, command in start_commands.items():
            #     print(f"Starting browser for {platform}: ", command)


            #     subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
            #     time.sleep(3)
            

            # Check each platform flag and run the corresponding start command if True
            if publish_xhs:
                run_command(start_commands["xhs"])
            if publish_douyin:
                run_command(start_commands["douyin"])
            if publish_bilibili:
                run_command(start_commands["bilibili"])
            if publish_shipinhao:
                run_command(start_commands["shipinhao"])
            if publish_y2b:
                run_command(start_commands["y2b"])

            time.sleep(10)

        except subprocess.CalledProcessError as e:
            print(f"Failed to execute Chromium sessions management commands: {e}")




def refresh_browsers(ports_patterns):
    global is_publishing
    while True:
        if not is_publishing:

            stop_and_start_chromium_sessions(
                # publish_xhs=True,
                # publish_douyin=True,
                # publish_shipinhao=True,
            )

            for port, patterns in ports_patterns.items():
                if not is_publishing:
                
                    try:
                        bring_to_front(patterns)

                        # driver = create_new_driver(port)
                        # driver.refresh()

                        if port == 5003:
                            xhs_login = XiaoHongShuLogin(create_new_driver(port=port))
                            xhs_login.check_and_act()

                        elif port == 5004:
                            douyin_login = DouyinLogin(create_new_driver(port=port))
                            douyin_login.check_and_act()

                        elif port == 5006:
                            shi_pin_hao_login = ShiPinHaoLogin(create_new_driver(port=port))
                            shi_pin_hao_login.check_and_act()

                        else:
                            print("Not implemented. ")

                        print(f"Refreshed and brought to front browser on port {port}.")
                    except Exception as e:
                        print(f"Failed to refresh browser on port {port}: {e}")
                        traceback.print_exc()

                # time.sleep(3)
                # Short sleep between refreshing each browser, if needed
                time.sleep(max(3, random.normalvariate(mu=3, sigma=1)))

        # time.sleep(refresh_time)
        # Calculate sleep time as the mean plus an absolute value of a normal distribution centered at 0
        sleep_time = args.refresh_time + abs(random.normalvariate(mu=0, sigma=args.refresh_time / 4))
        print(f"Sleeping for {sleep_time:.2f} seconds before next refresh cycle.")
        time.sleep(sleep_time)


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

# def clean_title(title):
#     print("Original title: ", title)
#     # Define a regex pattern that matches Chinese characters, English letters, numbers, Japanese characters, and punctuation
#     pattern = r'[\u4e00-\u9fff\u0030-\u0039\u0041-\u005a\u0061-\u007a\u3000-\u303f\uff00-\uffef]+'

#     # Find all substrings that match the pattern
#     matches = re.findall(pattern, title)

#     # Join the matches to get the cleaned title
#     cleaned_title = ''.join(matches)
#     print("Cleaned title: ", cleaned_title)
    
#     return cleaned_title

def clean_title(title):
    print("Original title: ", title)
    # Define a regex pattern that matches Chinese characters, English letters, numbers, Japanese characters,
    # full-width and half-width punctuation, blank space, and specific punctuation like colon
    pattern = r'[\u4e00-\u9fff\u0030-\u0039\u0041-\u005a\u0061-\u007a\u3000-\u303f\uff00-\uffef ,.!?:]'

    # Find all substrings that match the pattern
    matches = re.findall(pattern, title)

    # Join the matches to get the cleaned title
    cleaned_title = ''.join(matches)
    print("Cleaned title: ", cleaned_title)
    
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

    def stop_and_start_chromium_sessions(self,
            publish_xhs=False,
            publish_bilibili=False,
            publish_douyin=False,
            publish_shipinhao=False,
            publish_y2b=False
        ):

        stop_and_start_chromium_sessions(
            publish_xhs=publish_xhs,
            publish_bilibili=publish_bilibili,
            publish_douyin=publish_douyin,
            publish_shipinhao=publish_shipinhao,
            publish_y2b=publish_y2b
        )

    def get(self):

        print("test")

        self.write("test")


    @staticmethod
    def check_ignore_file(flag_name, ignore_filename):
        """
        Check if the publishing flag should be true based on the presence of the ignore file.
        If the ignore file does not exist and the flag is set to true, return True.
        """
        return not os.path.exists(ignore_filename) and flag_name

    # @tornado.web.stream_request_body
    def post(self):
        global is_publishing
        is_publishing = True

        # Read publishing options from request
        publish_xhs = self.get_argument('publish_xhs', 'false').lower() == 'true'
        publish_bilibili = self.get_argument('publish_bilibili', 'false').lower() == 'true'
        publish_douyin = self.get_argument('publish_douyin', 'false').lower() == 'true'
        publish_shipinhao = self.get_argument('publish_shipinhao', 'false').lower() == 'true'
        publish_y2b = self.get_argument('publish_y2b', 'false').lower() == 'true'
        test_mode = self.get_argument('test', 'false').lower() == 'true'

        # Define ignore files
        ignore_files = {
            'xhs': 'ignore_xhs',
            'bilibili': 'ignore_bilibili',
            'douyin': 'ignore_douyin',
            'shipinhao': 'ignore_shipinhao',
            'y2b': 'ignore_y2b'
        }

        check_ignore_file = self.check_ignore_file

        # Check ignore files and adjust flags
        publish_xhs = check_ignore_file(publish_xhs, ignore_files['xhs'])
        publish_bilibili = check_ignore_file(publish_bilibili, ignore_files['bilibili'])
        publish_douyin = check_ignore_file(publish_douyin, ignore_files['douyin'])
        publish_shipinhao = check_ignore_file(publish_shipinhao, ignore_files['shipinhao'])
        publish_y2b = check_ignore_file(publish_y2b, ignore_files['y2b'])

        self.stop_and_start_chromium_sessions(
            publish_xhs=publish_xhs,
            publish_bilibili=publish_bilibili,
            publish_douyin=publish_douyin,
            publish_shipinhao=publish_shipinhao,
            publish_y2b=publish_y2b
        )

        # Extract filename from form fields or use current datetime as default
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = self.get_argument('filename')

        print("Received publish request: ", filename)
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
                    # metadata_en["title"] = clean_title(metadata_en["title"])
                    metadata_en["title"] = metadata_en["title"]
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
                    pub_xhslisher = XiaoHongShuPublisher(self.create_new_driver(5003), path_mp4, path_cover, metadata, test_mode)
                    publishers.append((pub_xhslisher, 'XiaoHongShu'))
                if publish_douyin:
                    pub_douyinlisher = DouyinPublisher(self.create_new_driver(5004), path_mp4, path_cover, metadata, test_mode)
                    publishers.append((pub_douyinlisher, 'Douyin'))
                if publish_bilibili:
                    pub_bilibililisher = BilibiliPublisher(self.create_new_driver(5005), path_mp4, path_cover, metadata, test_mode)
                    publishers.append((pub_bilibililisher, 'Bilibili'))
                if publish_shipinhao:
                    pub_shipinhaolisher = ShiPinHaoPublisher(self.create_new_driver(5006), path_mp4, path_cover, metadata, test_mode)
                    publishers.append((pub_shipinhaolisher, 'ShiPinHao'))
                if publish_y2b:
                    pub_y2blisher = YouTubePublisher(self.create_new_driver(9222), path_mp4, path_cover, metadata_en, test_mode)
                    publishers.append((pub_y2blisher, 'YouTube'))

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
                    elif name == 'ShiPinHao':
                        bring_to_front(["视频号助手"])
                    elif name == 'YouTube':
                        bring_to_front(["YouTube"])

                    publisher.publish()

                self.write(json.dumps({"message": f"Published the content from {filename}"}))
            else:
                self.write(json.dumps({"error": f"Metadata JSON file not found in {transcription_dir}"}))
        except Exception as e:
            self.write(json.dumps({"error": f"An error occurred: {str(e)}"}))
            traceback.print_exc()

        finally:
            is_publishing = False

def make_app():
    # transcription_path = "/home/lachlan/Projects/auto-publish/transcription_data"
    # chromedriver_path = '/usr/lib/chromium-browser/chromedriver'
    return tornado.web.Application([
        (r"/publish", PublishHandler, dict(transcription_root=transcription_root, chromedriver_path=chromedriver_path)),
    ])

if __name__ == "__main__":

    ports_patterns = {
        # 5003: ["小红书", "你访问的页面不见了"],
        # 5004: ["抖音"],
        # 5005: ["哔哩哔哩"],
        # 5006: ["视频号助手"],
        # 9222: ["YouTube"]
    }

    refresh_thread = threading.Thread(target=refresh_browsers, args=(ports_patterns,), daemon=True)
    refresh_thread.start()

    app = make_app()
    app.listen(port, max_body_size=10*1024 * 1024 * 1024)
    print("Listen on: ", f"http://lazyingart:{port}")
    tornado.autoreload.start()
    tornado.ioloop.IOLoop.current().start()
