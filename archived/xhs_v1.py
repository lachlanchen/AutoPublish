from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pathlib
import time

# Specify the path to chromedriver.exe (download and save it on your system)
service = Service('/usr/local/bin/chromedriver')

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
# Uncomment the next line if you have a remote debugging session you want to connect to
# options.add_argument("--remote-debugging-port=9222")

options.headless = False  # Set headless mode here

# Initialize the driver
driver = webdriver.Chrome(service=service, options=options)

catalog_mp4 = r"videos"
describe = "跑步 #搞笑 #电影 #视觉震撼"
time.sleep(10)
path = pathlib.Path(catalog_mp4)

# Find the first .mp4 and image file in the directory
path_mp4 = next(path.glob('*.mp4'), None)
path_cover = next(path.glob('*.png'), None) or next(path.glob('*.jpg'), None)

if not path_mp4:
    print("未检查到视频路径，程序终止！")
    exit()

if not path_cover:
    print("未检查到封面路径，程序终止！")
    exit()

print(f"检查到视频路径：{path_mp4}")
print(f"检查到封面路径：{path_cover}")

# Function to publish video
def publish_xiaohongshu():
    driver.get("https://creator.xiaohongshu.com/creator/post")
    time.sleep(2)
    video_upload_element = driver.find_element(By.XPATH, '//input[@type="file"]')
    video_upload_element.send_keys(str(path_mp4))

    # Rest of your code for video uploading...

# Start the publishing process
publish_xiaohongshu()
