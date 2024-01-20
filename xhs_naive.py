import selenium
from selenium import webdriver
import pathlib
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# from seleniumwire import webdriver  # Import from seleniumwire
# import pathlib
# import time

# Setup selenium-wire options to capture or control the browser traffic
# sw_options = {
#     'connection_timeout': None,  # It can be useful to increase the timeout when debugging
#     # ... other options if needed
# }

# 基本信息
# 视频存放路径
catalog_mp4 = r"/Users/lachlan/Documents/iProjects/auto-publish/videos"
# 视频描述
describe = "跑步 #搞笑 #电影 #视觉震撼"
time.sleep(10)
options = webdriver.ChromeOptions()
# options.add_argument("--remote-debugging-port=5003")
options.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
# options.add_argument("--remote-debugging-port=9222")
driver = webdriver.Chrome(options = options)
# Use selenium-wire's webdriver instead of selenium's webdriver
# driver = webdriver.Firefox(seleniumwire_options=sw_options)


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
    driver.find_element(By.XPATH, '//input[@type="file"]').send_keys(path_mp4)

    # 等待视频上传完成
    while True:
        time.sleep(3)
        try:
            driver.find_element(By.XPATH, '//*[contains(text(),"重新上传")]')
            break
        except Exception as e:
            print("视频还在上传中···")

    print("视频已上传完成！")

    # 输入标题
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[contains(@class,"titleInput")]//input').send_keys(describe)
    # 输入描述信息
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[contains(@class,"topic-container")]//p').send_keys(describe)

    # 添加封面
    time.sleep(2)
    # try:
    #     driver.find_element(By.XPATH, '//*[text()="编辑默认封面"]').click()
    # except Exception as e:
    #     driver.find_element(By.XPATH, '//*[text()="修改默认封面"]').click()

    # Wait for the pop-up to be visible and then click the upload cover button
    # The XPath checks for an element with text "编辑默认封面" or "修改默认封面"
    cover_button_xpath = '//*[text()="编辑默认封面" or text()="修改默认封面"]'

    # Use WebDriverWait and expected_conditions to wait until the element is clickable
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, cover_button_xpath))
    ).click()

    time.sleep(2)
    driver.find_element(By.XPATH, '//*[text()="上传封面"]').click()
    # WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.XPATH, '//*[contains(@class,"tab-item")][contains(text(),"上传封面")]'))
    # ).click()
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="upload-cover-containner"]/..//input[@type="file"]').send_keys(path_cover)
    time.sleep(3)
    driver.find_element(By.XPATH, '//*[contains(text(),"上传封面")]/../../../../..//*[text()="确定"]').click()

    # Add location
    # Click the dropdown to show options
    dropdown_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "single-input"))
    )
    dropdown_element.click()

    # Wait for the dropdown options to appear
    options_container = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "dropdown"))
    )

    # Click the option with the text "香港大学"
    university_option = options_container.find_element(By.XPATH, ".//span[contains(text(), '香港大学')]")
    university_option.click()

    # Add further steps as per your process
    # 人工进行检查并发布
    # time.sleep(3)
    # # 点击发布
    # driver.find_element_by_xpath('//*[text()="发布"]').click()


# 开始执行视频发布
publish_xiaohongshu()
