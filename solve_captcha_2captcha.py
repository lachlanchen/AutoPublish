# https://github.com/2captcha/2captcha-python

import sys
import os
import requests
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from twocaptcha import TwoCaptcha

api_key = os.getenv('APIKEY_2CAPTCHA', '35e6654df7be91eaf3a278d1671ebbde')

solver = TwoCaptcha(api_key)

# resp = requests.get("https://2captcha.com/api/v1/captcha-demo/gee-test/init-params")
# print(resp.content)
# data = json.loads(resp.content)
# challenge = data["challenge"]

try:
  result = solver.geetest(gt='ddf252035e784bada44ac15d331ee6ab',
                          apiServer='api.geetest.com',
                          challenge='4dd5e994a6378c4dd397d854bb6d1cd0',
                          url='https://static.geetest.com/captcha_v3/batch/v3/59515/2024-01-22T12/word/')

except Exception as e:
  sys.exit(e)

else:
  sys.exit('solved: ' + str(result))