import urllib.request
import re
import json

url = 'https://www.youtube.com/playlist?list=PLDzVTTgUrcNN1XkJgYok7SRyNxbXWpRaC'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='replace')
        m = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        uniq = []
        for x in m:
            if x not in uniq:
                uniq.append(x)
        print('Playlist videos:', uniq[:15])
except Exception as e:
    print('Err:', e)
