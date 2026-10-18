import urllib.request
import json
import re

video_ids = [
    ('J3qTJefkD-A', 'https://www.youtube.com/watch?v=J3qTJefkD-A'),
    ('zgpstRvSwhk', 'https://www.youtube.com/watch?v=zgpstRvSwhk'),
    ('GWn5LiOSBlA', 'https://www.youtube.com/watch?v=GWn5LiOSBlA'),
    ('f8sSwcP9KwQ', 'https://www.youtube.com/watch?v=f8sSwcP9KwQ'),
    ('Iq_MxtYvRww', 'https://www.youtube.com/watch?v=Iq_MxtYvRww'),
    ('QFvkAZjUnUE', 'https://www.youtube.com/watch?v=QFvkAZjUnUE'),
    ('R3sAS1J3_fE', 'https://www.youtube.com/watch?v=R3sAS1J3_fE&t=142s'),
    ('lGChZzNybGY', 'https://www.youtube.com/watch?v=lGChZzNybGY&t=7s'),
    ('EO8odUZNdjc', 'https://www.youtube.com/watch?v=EO8odUZNdjc&t=996s')
]

for vid, full_url in video_ids:
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"[{vid}] TITLE: {data.get('title')} | AUTHOR: {data.get('author_name')}")
    except Exception as e:
        print(f"[{vid}] ERROR: {e}")
