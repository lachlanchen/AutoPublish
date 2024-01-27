import os
import requests
from urllib.parse import urlparse
from pathlib import Path
from requests_toolbelt import MultipartEncoder

import subprocess


# class VideoProcessor:
#     def __init__(self, server_url, video_path, transcription_path):
#         self.server_url = server_url
#         self.video_path = video_path
#         self.transcription_path = transcription_path
#         os.makedirs(self.transcription_path, exist_ok=True)

#     def process_video(self, use_cache=False):
#         video_name = Path(self.video_path).stem
#         zip_file_root = os.path.join(self.transcription_path, video_name)
#         os.makedirs(zip_file_root, exist_ok=True)
#         zip_file_path = os.path.join(zip_file_root, f"{video_name}.zip")

#         # Check cache
#         if use_cache:
#             if os.path.isfile(zip_file_path):
#                 print(f"Cache hit! Returning the processed file from {zip_file_path}.")
#                 return zip_file_path
#             else:
#                 print("Cache miss. Proceeding with video processing.")

#         with open(self.video_path, 'rb') as f:
#             files = {'video': (os.path.basename(self.video_path), f)}
#             response = requests.post(self.server_url, files=files)


#         if response.ok:
#             with open(zip_file_path, 'wb') as f:
#                 f.write(response.content)
#             print(f'Success! Processed files are downloaded and saved to {zip_file_path}.')
#             return zip_file_path
#         else:
#             print(f'Failed. Status code: {response.status_code}, Message: {response.text}')

class VideoProcessor:
    def __init__(self, upload_url, process_url, video_path, transcription_path):
        self.upload_url = upload_url
        self.process_url = process_url
        self.video_path = video_path
        self.transcription_path = transcription_path
        os.makedirs(self.transcription_path, exist_ok=True)

    def process_video(self, use_cache=False):
        video_name = Path(self.video_path).stem
        zip_file_root = os.path.join(self.transcription_path, video_name)
        os.makedirs(zip_file_root, exist_ok=True)
        zip_file_path = os.path.join(zip_file_root, f"{video_name}.zip")

        # Check cache
        if use_cache and os.path.isfile(zip_file_path):
            print(f"Cache hit! Returning the processed file from {zip_file_path}.")
            return zip_file_path

        # print("Cache miss. Uploading video for processing.")
        # with open(self.video_path, 'rb') as f:
        #     files = {'video': (os.path.basename(self.video_path), f)}

        #     if not self.upload_url.endswith("stream"):
        #         response = requests.post(self.upload_url, files=files, data={'filename': os.path.basename(self.video_path)})
        #     else:
        #         # Use PUT method for uploading the file
        #         response = requests.put(self.upload_url, files=files, params={'filename': os.path.basename(self.video_path)})
        print("Cache miss. Uploading video for processing.")
        if not self.upload_url.endswith("stream"):
            with open(self.video_path, 'rb') as f:
                files = {'video': (os.path.basename(self.video_path), f)}
                response = requests.post(self.upload_url, files=files, data={'filename': os.path.basename(self.video_path)})
        else:
            # Preprocess the file for streaming upload
            preprocessed_file_path = self.preprocess_for_streaming(self.video_path)
            with open(preprocessed_file_path, 'rb') as f:
                files = {'video': (os.path.basename(preprocessed_file_path), f)}
                response = requests.put(self.upload_url, files=files, params={'filename': os.path.basename(preprocessed_file_path)})
 


        if not response.ok:
            print(f'Failed to upload file. Status code: {response.status_code}, Message: {response.text}')
            return

        # Extract the file path from the response
        uploaded_file_path = response.json().get('file_path')
        if not uploaded_file_path:
            print("Failed to get the uploaded file path from the server response.")
            return

        # Request processing of the uploaded file
        process_response = requests.post(self.process_url, data={'file_path': uploaded_file_path})
        if process_response.ok:
            with open(zip_file_path, 'wb') as f:
                f.write(process_response.content)
            print(f'Success! Processed files are downloaded and saved to {zip_file_path}.')
            return zip_file_path
        else:
            print(f'Failed to process file. Status code: {process_response.status_code}, Message: {process_response.text}')
    
    def preprocess_for_streaming(self, file_path):
        output_file_path = os.path.join(os.path.dirname(file_path), 'preprocessed_' + os.path.basename(file_path))
        # Explicitly specify the video and audio codec along with copying the streams and moving the moov atom
        command = f"ffmpeg -y -i \"{file_path}\" -vcodec copy -acodec copy -movflags faststart \"{output_file_path}\""
        try:
            subprocess.run(command, shell=True, check=True)
            print(f"Successfully preprocessed {file_path} to {output_file_path}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to preprocess file with FFmpeg: {e}")
            return file_path  # Return original file path in case of failure
        return output_file_path



if __name__ == "__main__":
    # Usage
    video_path = '/Users/lachlan/Nutstore Files/Vlog/AutoPublish/IMG_5304.MOV'
    server_url = 'http://lachlanserver:8081/video-processing'
    transcription_path = "/Users/lachlan/Nutstore Files/Vlog/transcription_data"

    processor = VideoProcessor(server_url, video_path, transcription_path)
    processor.process_video()
