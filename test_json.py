import json
import json5

def robust_json5_parse(json_str):
    # Attempt to handle unexpected newlines and unescaped double quotes
    # json_str = ''.join(line.strip() if not line.strip().startswith('"') else line for line in json_str.split('\n'))
    json_str = json_str.replace('\n', '')

    # Try to parse the JSON string using json5 for more flexibility
    try:
        parsed_json = json5.loads(json_str)
        return parsed_json
    except ValueError as e:
        print(f'JSON Decode Error: {e}')
        return None

# JSON string with error
json_str = '''
{"title": "Soaring High: Meet the Little Prodigy of the Sky",
 "brief_description": "Discover the fascinating world of flight with our 'little friend' who boasts impressive aerial skills. Watch and learn from
 nature's tiny aviator.",
 "middle_description": "Embark on an enchanting flight journey with a creature that may be small in size but is a giant in the sky.",
 "long_description": "Hello there and welcome to an awe-inspiring display of nature's mastery of the skies. In this video, we greet a 'little frie
nd,' whose proficiency in the air is nothing short of remarkable. The idiom 'size doesn't matter' comes to life as you watch our minute partner ma
neuver through the air, demonstrating a level of skill that rivals that of the most experienced flyers.

As viewers, you're invited to not only spectate but also to get insight into the marvels of flight. The scientific intricacies of wing beats, the
aerodynamics that underpins each graceful movement, and the evolutionary wonders that allow such deft flight, all unravel before your eyes as this
 tiny creature shows off its flying prowess.

We subtly draw connections between these wonders and aspects of daily human life, underscoring the values of agility, adaptation, and the pursuit
of excellence. In essence, we employ the metaphor of flight to inspire and entertain.

Without explicitly instructing you to engage, we hope this video will subconsciously motivate you to click 'Favorite', share it with friends who h
arbor a passion for nature, and follow us for more incredible content. After all, the most impactful lessons are often not shouted but whispered.

With tags that encompass both the poetic and scientific nature of our content, we cater to a diverse audience, from casual nature lovers to the mo
re academically inclined. So, without further ado, let's spread our digital wings and take off into the realm of the small but mighty flyers among
 us.",

"tags": ["Bird Flight", "Nature's Wonders", "Flying Mastery", "Aerial Agility", "Evolution of Flight", "Animal Behavior", "Inspiring Nature", "Avi
an Expert", "Scientific Marvel", "Winged Acrobatics"],

"words_to_learn": [
  {"word": "hello", "time_stamps": "00:00:00,000 --> 00:00:03,500"},
  {"word": "little friend", "time_stamps": "00:00:00,000 --> 00:00:03,500"},
  {"word": "soaring", "time_stamps": "00:00:03,500 --> 00:00:07,498"},
  {"word": "aerial", "time_stamps": "00:00:03,500 --> 00:00:07,498"},
  {"word": "prodigy", "time_stamps": "00:00:03,500 --> 00:00:07,498"}
],

"cover": "00:00:03,500"}
'''

# Try to parse the JSON string
try:
    # parsed_json = json5.loads(json_str)
    parsed_json = robust_json5_parse(json_str)

    print(parsed_json)
except json.JSONDecodeError as e:
    print(f'Failed on attempt: JSON Decode Error: {e}')

