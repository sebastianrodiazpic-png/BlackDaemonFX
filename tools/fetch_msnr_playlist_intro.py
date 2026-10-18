"""Fetch public captions for the supplied course; no trading access."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import requests
from youtube_transcript_api import YouTubeTranscriptApi

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'storage/analysis/msnr_videos_20261013'
OUT.mkdir(parents=True,exist_ok=True)

def fetch(video_id):
    session=requests.Session()
    original=session.request
    session.request=lambda *a,**k:original(*a,**{'timeout':15,**k})
    result={'video_id':video_id,'url':'https://www.youtube.com/watch?v='+video_id}
    try:
        transcript=YouTubeTranscriptApi(http_client=session).fetch(video_id,languages=['es','en'])
        result.update(status='OK',language=transcript.language_code,
            snippets=[{'text':s.text,'start':s.start,'duration':s.duration} for s in transcript])
    except Exception as exc:
        result.update(status='UNAVAILABLE',error_type=type(exc).__name__,error=str(exc)[:400])
    finally:
        session.close()
    target=OUT/'captions';target.mkdir(parents=True,exist_ok=True)
    (target/(video_id+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    return {k:v for k,v in result.items() if k!='snippets'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--all',action='store_true');args=parser.parse_args()
    ids=['Bwktah4s79k']
    if args.all:
        ids += [r['vid'] for r in json.loads((ROOT/'scratch/transcripts_summary.json').read_text())]
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(fetch,ids))
    (OUT/'caption_fetch_summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
    for result in results:print(json.dumps(result),flush=True)
