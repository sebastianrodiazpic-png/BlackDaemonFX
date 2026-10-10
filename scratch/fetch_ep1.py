import urllib.request
import json
from youtube_transcript_api import YouTubeTranscriptApi

vid = "Bwktah4s79k"
url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    print("Video 1:", data.get("title"), "|", data.get("author_name"))

ytt = YouTubeTranscriptApi()
t_list = ytt.list(vid)
trans = None
for t in t_list:
    trans = t
    break
if trans:
    data = trans.fetch()
    text = " ".join([item.text if hasattr(item, 'text') else str(item) for item in data])
    with open(f"scratch/transcripts/{vid}.txt", "w", encoding="utf-8") as f:
        f.write(f"Title: {data}\nAuthor: MR.R\nVideo ID: {vid}\n\n{text}")
    print(f"Downloaded transcript for {vid} ({len(text)} chars)")
