import os
import requests
from urllib.parse import urlparse
from pathlib import Path

# class VideoProcessor:
#     def __init__(self, server_url, video_path, transcription_path):
#         self.server_url = server_url
#         self.video_path = video_path
#         self.transcription_path = transcription_path
#         os.makedirs(self.transcription_path, exist_ok=True)

#     def process_video(self, use_cache=False):
#         # Extract the video file name without extension for the zip file name
#         video_name = Path(self.video_path).stem

#         # Define the path for the zip file
#         zip_file_root = os.path.join(self.transcription_path, video_name)
#         os.makedirs(zip_file_root, exist_ok=True)
#         zip_file_path = os.path.join(zip_file_root, f"{video_name}.zip")

#         # Open the file in binary mode
#         with open(self.video_path, 'rb') as f:
#             # Define the POST request's parameters
#             files = {'video': (os.path.basename(self.video_path), f)}
            
#             # Send the POST request
#             response = requests.post(self.server_url, files=files)

#         # Handle the response
#         if response.ok:
#             # Save the response content (assuming it's the zipped processed files)
#             with open(zip_file_path, 'wb') as f:
#                 f.write(response.content)
#             print(f'Success! Processed files are downloaded and saved to {zip_file_path}.')

#             return zip_file_path
#         else:
#             print(f'Failed. Status code: {response.status_code}, Message: {response.text}')

class VideoProcessor:
    def __init__(self, server_url, video_path, transcription_path):
        self.server_url = server_url
        self.video_path = video_path
        self.transcription_path = transcription_path
        os.makedirs(self.transcription_path, exist_ok=True)

    def process_video(self, use_cache=False):
        video_name = Path(self.video_path).stem
        zip_file_root = os.path.join(self.transcription_path, video_name)
        os.makedirs(zip_file_root, exist_ok=True)
        zip_file_path = os.path.join(zip_file_root, f"{video_name}.zip")

        # Check cache
        if use_cache:
            if os.path.isfile(zip_file_path):
                print(f"Cache hit! Returning the processed file from {zip_file_path}.")
                return zip_file_path
            else:
                print("Cache miss. Proceeding with video processing.")

        with open(self.video_path, 'rb') as f:
            files = {'video': (os.path.basename(self.video_path), f)}
            response = requests.post(self.server_url, files=files)

        if response.ok:
            with open(zip_file_path, 'wb') as f:
                f.write(response.content)
            print(f'Success! Processed files are downloaded and saved to {zip_file_path}.')
            return zip_file_path
        else:
            print(f'Failed. Status code: {response.status_code}, Message: {response.text}')

if __name__ == "__main__":
    # Usage
    video_path = '/Users/lachlan/Nutstore Files/Vlog/AutoPublish/IMG_5304.MOV'
    server_url = 'http://lachlanserver:8080/video-processing'
    transcription_path = "/Users/lachlan/Nutstore Files/Vlog/transcription_data"

    processor = VideoProcessor(server_url, video_path, transcription_path)
    processor.process_video()
