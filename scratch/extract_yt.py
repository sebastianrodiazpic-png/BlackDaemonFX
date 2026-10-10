import urllib.request
import re
import json
import xml.etree.ElementTree as ET
import os

os.makedirs("scratch/captions", exist_ok=True)

video_ids = [
    'J3qTJefkD-A',
    'zgpstRvSwhk',
    'GWn5LiOSBlA',
    'f8sSwcP9KwQ',
    'Iq_MxtYvRww',
    'QFvkAZjUnUE',
    'R3sAS1J3_fE',
    'lGChZzNybGY',
    'EO8odUZNdjc'
]

results = {}

for vid in video_ids:
    url = f'https://www.youtube.com/watch?v={vid}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'})
    info = {"id": vid, "url": url}
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
        
        title_m = re.search(r'<title>(.*?)</title>', html)
        info["title"] = title_m.group(1).replace(" - YouTube", "") if title_m else ""
        
        desc_m = re.search(r'"shortDescription":"(.*?)"(?:,"isCrawlable"|,"thumbnail")', html)
        if desc_m:
            try:
                info["desc"] = json.loads('"' + desc_m.group(1) + '"')
            except Exception:
                info["desc"] = desc_m.group(1)
        else:
            info["desc"] = ""
            
        captions_m = re.search(r'"captionTracks":\s*(\[.*?\])', html)
        transcript_text = ""
        if captions_m:
            tracks = json.loads(captions_m.group(1))
            info["tracks"] = [t.get("languageCode") for t in tracks]
            # pick es or first
            chosen_track = None
            for t in tracks:
                if t.get("languageCode") == "es":
                    chosen_track = t
                    break
            if not chosen_track and tracks:
                chosen_track = tracks[0]
                
            if chosen_track:
                c_url = chosen_track.get("baseUrl")
                c_req = urllib.request.Request(c_url, headers={'User-Agent': 'Mozilla/5.0'})
                xml_data = urllib.request.urlopen(c_req, timeout=10).read().decode('utf-8', errors='ignore')
                root = ET.fromstring(xml_data)
                lines = []
                for elem in root.findall(".//text"):
                    t_text = elem.text or ""
                    start = elem.attrib.get("start", "0")
                    lines.append(f"[{start}s] {t_text}")
                transcript_text = "\n".join(lines)
        info["transcript"] = transcript_text
        results[vid] = info
        
        # save transcript to file
        with open(f"scratch/captions/{vid}.txt", "w", encoding="utf-8") as f:
            f.write(f"Title: {info['title']}\n")
            f.write(f"Description:\n{info['desc']}\n\n")
            f.write(f"Transcript:\n{transcript_text}\n")
        print(f"Saved {vid}: {info['title']} - Transcript lines: {len(transcript_text.splitlines())}")
    except Exception as e:
        print(f"Failed {vid}: {e}")

with open("scratch/captions_summary.json", "w", encoding="utf-8") as f:
    json.dump({k: {"title": v.get("title"), "has_transcript": bool(v.get("transcript")), "length": len(v.get("transcript", ""))} for k, v in results.items()}, f, indent=2)
