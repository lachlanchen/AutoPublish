import json
import json5

json_string = """
{"title": "探索英语秘诀：发现每个音节的秘密",
 "brief_description": "一起揭秘每个音节背后的'N'，扩展你的英语词汇！",
 "middle_description": "你注意到过英语每个音节末尾的神秘"N"了吗？本视频带你深入了解，并学习一个特别的词汇：affinity。",
 "long_description": "通过有趣的方式学习英语，本视频将介绍一个非常有意思的现象：每个音节的末尾都带有一个"N"的声音。掌握这一点将帮助你更自然地掌握
英语发音。我们将深入讨论如何识别并正确发音诸如'affinity'等重要词汇。不仅如此，我们还会提供一些记忆技巧，帮助你将新学的词汇运用到实际对话中。不要错
过视频中的小测验，跟着我们一步步提升你的语言能力。标签你的朋友，一起加入这趟英语学习之旅吧！想知道更多就赶快点击视频，开始你的学习吧！",
 "tags": ["英语学习", "音节秘密", "发音技巧", "词汇记忆", "语言技能", "趣味教学", "affinity", "发音练习", "在线课程", "语言挑战"],
 "words_to_learn": [
     {"word": "interesting", "time_stamps": "00:00:00,250 --> 00:00:05,910"},
     {"word": "affinity", "time_stamps": "00:00:12,458 --> 00:00:14,750"},
     {"word": "Anaboi", "time_stamps": "00:00:15,546 --> 00:00:17,546"},
     {"word": "Min", "time_stamps": "00:00:19,546 --> 00:00:21,546"},
     {"word": "understands", "time_stamps": "00:00:33,850 --> 00:00:36,062"}
     ],
 "cover": "00:00:17,546"}
"""

import pprint
import re

pprint(json5.loads(json_string.replace('', "\"")))
