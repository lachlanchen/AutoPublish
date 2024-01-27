import selenium
from selenium import webdriver
import pathlib
import time
from selenium.webdriver.common.keys import Keys

# 基本信息
# 视频存放路径
catalog_mp4 = r"C:\Users\Administrator\Desktop\视频发布"
# 视频描述
describe = "AI·热带亚马逊·奇幻星空 #视觉震撼 #旅行 #AI #星空 #大自然"
time.sleep(10)
options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options = options)

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
    
def publish_bilibili():
    '''
     作用：发布b站视频
    '''
    
    # 进入创作者页面，并上传视频
    driver.get("https://member.bilibili.com/platform/upload/video/frame")
    time.sleep(3)
    # 2023.3.5 注释
    # driver.switch_to.frame(driver.find_element_by_xpath('//iframe[@name="videoUpload"]'))
    print(path_mp4)
    driver.find_element_by_xpath('//input[@type="file" and contains(@accept,"mp4")]').send_keys(path_mp4)
    
    # 等待视频上传完成
    while True:
        time.sleep(3)
        try:
            driver.find_element_by_xpath('//*[text()="上传完成"]')
            break;
        except Exception as e:
            print("视频还在上传中···")
    
    print("视频已上传完成！")
    
    time.sleep(3)
    # 输入标题
    driver.find_element_by_xpath('//input[contains(@placeholder,"标题")]').clear()
    time.sleep(1)
    driver.find_element_by_xpath('//input[contains(@placeholder,"标题")]').send_keys(describe[:describe.index(" #")])

    # 输入描述
    driver.find_element_by_xpath('//*[@editor_id="desc_at_editor"]//br').send_keys(describe)

    # 选择分类
    time.sleep(1)
    driver.find_element_by_xpath('//*[contains(@class,"select-item-cont")]').click()
    time.sleep(1)
    driver.find_element_by_xpath('//*[text()="科技"]').click()
    time.sleep(1)
    driver.find_element_by_xpath('//*[@class="item-main" and text()="计算机技术"]').click()
    
    # 选择标签
    time.sleep(2)
    # 参与活动，根据实际活动来加
    # driver.find_element_by_xpath('//*[text()="参与活动："]/..//*[text()="科技猎手"]').click()
    time.sleep(3)
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys("视觉震撼")
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys(Keys.ENTER)
    time.sleep(1)
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys("自然")
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys(Keys.ENTER)
    time.sleep(1)
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys("奇观")
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys(Keys.ENTER)
    time.sleep(1)
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys("深度学习")
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys(Keys.ENTER)
    time.sleep(1)
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys("AI")
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys(Keys.ENTER)
    time.sleep(1)
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys("旅行")
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys(Keys.ENTER)
    time.sleep(1)
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys("美景")
    driver.find_element_by_xpath('//input[@placeholder="按回车键Enter创建标签"]').send_keys(Keys.ENTER)
    time.sleep(1)
    
    # 刚开始可以先注释掉发布，人工进行检查内容是否有问题
    time.sleep(3)
    # 点击发布
    driver.find_element_by_xpath('//*[text()="立即投稿"]').click()
    
# 开始执行b站视频发布
publish_bilibili()