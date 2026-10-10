import urllib.request
import json
import re

vids = [
    ("L_vwb_jf6og", "Individual"),
    ("sTRxqo4EwPU", "Individual"),
    ("1x57n_5iRsU", "Individual"),
    ("dGv5zwrK9vY", "Individual"),
    ("YmK59hyKX0U", "Individual"),
    ("qT-TWP2sUgA", "Individual"),
    ("odvBj8IpZ74", "Individual"),
    ("xYlpAr5pwXg", "Individual"),
    ("9ZNPazzfDcU", "Individual"),
    ("5oTQEdSV7p0", "Individual"),
    ("wDK7qO4mf-E", "Individual"),
    ("lqlkspVKt7s", "Playlist Ep 2"),
    ("CH9iW5caHHk", "Playlist Ep 3"),
    ("QbyhRLF53RI", "Playlist Ep 4"),
    ("XvXWWv3gD8k", "Playlist Ep 5"),
    ("sxn-jP9St9I", "Playlist Ep 6"),
    ("FM0XkqUIrAI", "Playlist Ep 7"),
    ("WLKh7JAcy34", "Playlist Ep 8"),
    ("XFkktcM_srU", "Playlist Ep 9"),
    ("qciNrYGZ5V8", "Playlist Ep 10"),
    ("ip8z7AThH7Y", "Playlist Ep 11"),
    ("bMxO8y4siSI", "Playlist Ep 12")
]

results = []
for vid, tag in vids:
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            title = data.get("title", "")
            author = data.get("author_name", "")
            results.append({"vid": vid, "tag": tag, "author": author, "title": title})
            print(f"[{tag}] {vid} | {author} | {title}")
    except Exception as e:
        print(f"[{tag}] {vid} | ERROR: {e}")

with open("scratch/youtube_titles.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
