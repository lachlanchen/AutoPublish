import selenium
# from selenium import webdriver
# import pathlib
# import time
from selenium.webdriver.common.keys import Keys

from seleniumwire import webdriver  # Import from seleniumwire
import pathlib
import time

# Setup selenium-wire options to capture or control the browser traffic
sw_options = {
    'connection_timeout': None,  # It can be useful to increase the timeout when debugging
    # ... other options if needed
}

# 基本信息
# 视频存放路径
catalog_mp4 = r"videos"
# 视频描述
describe = "跑步 #搞笑 #电影 #视觉震撼"
time.sleep(10)
options = webdriver.FirefoxOptions()
options.add_argument("--remote-debugging-port=5003")
# options.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
# driver = webdriver.Firefox(options = options)
# Use selenium-wire's webdriver instead of selenium's webdriver
driver = webdriver.Firefox(seleniumwire_options=sw_options)


path = pathlib.Path(catalog_mp4)

# 视频地址获取
path_mp4 = ""
for i in path.iterdir():
    if(".mp4" in str(i)):
        path_mp4 = str(i);
        break;

if(path_mp4 != ""):
    print("检查到视频路径：" + path_mp4)
else:
    print("未检查到视频路径，程序终止！")
    exit()

# 封面地址获取
path_cover = ""
for i in path.iterdir():
    if(".png" in str(i) or ".jpg" in str(i)):
        path_cover = str(i);
        break;

if(path_cover != ""):
    print("检查到封面路径：" + path_cover)
else:
    print("未检查到封面路径，程序终止！")
    exit()

def publish_xiaohongshu():
    '''
     作用：发布小红书号短视频
    '''

    # 进入创作者页面，并上传视频
    driver.get("https://creator.xiaohongshu.com/creator/post")
    time.sleep(2)
    driver.find_element_by_xpath('//input[@type="file"]').send_keys(path_mp4)

    # 等待视频上传完成
    while True:
        time.sleep(3)
        try:
            driver.find_element_by_xpath('//*[contains(text(),"重新上传")]')
            break;
        except Exception as e:
            print("视频还在上传中···")

    print("视频已上传完成！")

    # 输入标题
    time.sleep(2)
    driver.find_element_by_xpath('//*[contains(@class,"titleInput")]//input').send_keys(describe)
    # 输入描述信息
    time.sleep(2)
    driver.find_element_by_xpath('//*[contains(@class,"topic-container")]//p').send_keys(describe)

    # 添加封面
    time.sleep(1)
    driver.find_element_by_xpath('//*[text()="编辑封面"]').click()
    time.sleep(1)
    driver.find_element_by_xpath('//*[text()="上传封面"]').click()
    time.sleep(1)
    driver.find_element_by_xpath('//*[@id="upload-cover-containner"]/..//input[@type="file"]').send_keys(path_cover)
    time.sleep(3)
    driver.find_element_by_xpath('//*[contains(text(),"上传封面")]/../../../../..//*[text()="确定"]').click()

    # 人工进行检查并发布
    # time.sleep(3)
    # # 点击发布
    # driver.find_element_by_xpath('//*[text()="发布"]').click()

# 开始执行视频发布
publish_xiaohongshu()
