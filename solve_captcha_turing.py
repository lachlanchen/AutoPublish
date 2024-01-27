import base64
import json
import requests
import os

# Function to download image from URL and save it locally
def download_image(url, local_path='./temp/'):
    response = requests.get(url)
    if response.status_code == 200:
        # Ensure the local path exists
        os.makedirs(local_path, exist_ok=True)
        # Extract the filename from the URL
        filename = url.split('/')[-1].split('?')[0]
        file_path = os.path.join(local_path, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path
    else:
        raise Exception(f"Error downloading image: Status code {response.status_code}")

# Function to call the API with base64 encoded image
def b64_api(username, password, img_path, ID):
    with open(img_path, 'rb') as f:
        b64_data = base64.b64encode(f.read())
    b64 = b64_data.decode()
    data = {"username": username, "password": password, "ID": ID, "b64": b64, "version": "3.1.1"}
    data_json = json.dumps(data)
    result = json.loads(requests.post("http://www.fdyscloud.com.cn/tuling/predict", data=data_json).text)
    return result

# Main execution
if __name__ == "__main__":
    # Image URL to be processed
    img_url = "https://static.geetest.com/captcha_v3/batch/v3/59519/2024-01-22T13/word/bbb917de95564135973a54727a29ebe9.jpg?challenge=7d2b6041c37bb56b95d223b525eee8e7"
    
    try:
        # Download image and get local path
        img_path = download_image(img_url)
        print(f"Image downloaded to: {img_path}")
        
        # Call API with downloaded image
        result = b64_api(username="lachlanchen", password="eG8h.YfnWMyd9QR", img_path=img_path, ID="08272733")
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")

