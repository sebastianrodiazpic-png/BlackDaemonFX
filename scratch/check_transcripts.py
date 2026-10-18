import sys
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print("youtube_transcript_api is available")
except ImportError:
    print("youtube_transcript_api NOT available")
