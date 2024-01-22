import base64
import json
import requests

# 复制以下代码，只需填入自己的账号密码、待识别的图片路径即可。
# 关于ID：选做识别的模型ID。

def b64_api(username, password, img_path, ID):
    with open(img_path, 'rb') as f:
        b64_data = base64.b64encode(f.read())
    b64 = b64_data.decode()
    data = {"username": username, "password": password, "ID": ID, "b64": b64, "version": "3.1.1"}
    data_json = json.dumps(data)
    result = json.loads(requests.post("http://www.fdyscloud.com.cn/tuling/predict", data=data_json).text)
    return result

if __name__ == "__main__":
    img_url = r"https://static.geetest.com/captcha_v3/batch/v3/59519/2024-01-22T13/word/bbb917de95564135973a54727a29ebe9.jpg?challenge=7d2b6041c37bb56b95d223b525eee8e7"
    img_path = xxx
    result = b64_api(username="lachlanchen", password="eG8h.YfnWMyd9QR", img_path=img_path, ID="08272733")
    print(result)
