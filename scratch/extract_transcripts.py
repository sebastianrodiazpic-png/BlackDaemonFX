import os
import json
from youtube_transcript_api import YouTubeTranscriptApi

vids = [
    ("L_vwb_jf6og", "Albert, Un Trader Mortal", "Malaysian SNR: La Estrategia que CAMBIO el Trading en USA"),
    ("sTRxqo4EwPU", "Pol Castella", "TradingForexSP | Nueva ESTRATEGIA mejor que CRT? MALAYSIAN SNR"),
    ("1x57n_5iRsU", "Nestor Santos", "Traders de la INDIA ESTRATEGIA Parte 1"),
    ("dGv5zwrK9vY", "Nestor Santos", "Traders de la INDIA ESTRATEGIA Parte 2"),
    ("YmK59hyKX0U", "Nestor Santos", "Traders de la INDIA ESTRATEGIA Parte 3"),
    ("qT-TWP2sUgA", "Nestor Santos", "Traders de la INDIA ESTRATEGIA Parte 4 (TAKE PROFIT)"),
    ("odvBj8IpZ74", "Nestor Santos", "Traders de la INDIA/MALASIA ESTRATEGIA Parte 5"),
    ("xYlpAr5pwXg", "MBA", "Estrategia MALAYSIAN SNR Bootcamp Dia 1"),
    ("9ZNPazzfDcU", "MBA", "Como Identificar la ESTRUCTURA del Precio Bootcamp Dia 2"),
    ("5oTQEdSV7p0", "MBA", "LIQUIDEZ del Mercado Bootcamp Dia 3"),
    ("wDK7qO4mf-E", "Albert, Un Trader Mortal", "La Nueva Estrategia de Trading Hecha en Malasia (+500% por Trade)"),
    ("lqlkspVKt7s", "MR.R Alchemist", "Alchemist snr part 2"),
    ("CH9iW5caHHk", "MR.R Alchemist", "Alchemist snr part 3"),
    ("QbyhRLF53RI", "MR.R Alchemist", "Alchemist snr part 4"),
    ("XvXWWv3gD8k", "MR.R Alchemist", "Alchemist snr part 5"),
    ("sxn-jP9St9I", "MR.R Alchemist", "Alchemist fx 2023"),
    ("FM0XkqUIrAI", "MR.R Alchemist", "Alchemist msnr 2024"),
    ("WLKh7JAcy34", "MR.R Alchemist", "Alchemist msnr 2026 Chart Analysis + Knowledge sharing part 1"),
    ("XFkktcM_srU", "MR.R Alchemist", "Alchemist msnr 2026 Chart Analysis + Knowledge sharing part 2"),
    ("qciNrYGZ5V8", "MR.R Alchemist", "Alchemist msnr 2026 Chart Analysis + Knowledge sharing part 3"),
    ("ip8z7AThH7Y", "MR.R Alchemist", "Alchemist msnr 2026 Chart Analysis + Knowledge sharing part 4"),
    ("bMxO8y4siSI", "MR.R Alchemist", "Alchemist msnr 2026 Chart Analysis + Knowledge sharing part 5")
]

os.makedirs("scratch/transcripts", exist_ok=True)
summary_info = []
ytt = YouTubeTranscriptApi()

for vid, author, title in vids:
    print(f"Fetching transcript for {vid}: {title}...")
    try:
        t_list = ytt.list(vid)
        trans = None
        # Try finding es, en, or first
        try:
            trans = t_list.find_transcript(['es', 'es-419', 'en'])
        except Exception:
            for t in t_list:
                trans = t
                break
                
        if trans:
            data = trans.fetch()
            # In new version, data is FetchedTranscript which has snippets or can be iterated
            text_lines = []
            for item in data:
                if isinstance(item, dict):
                    text_lines.append(item.get('text', ''))
                elif hasattr(item, 'text'):
                    text_lines.append(item.text)
                else:
                    text_lines.append(str(item))
            full_text = " ".join(text_lines)
            out_file = f"scratch/transcripts/{vid}.txt"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\nAuthor: {author}\nVideo ID: {vid}\nLanguage: {trans.language_code}\n\n{full_text}")
            print(f"  -> SUCCESS ({len(text_lines)} snippets, {len(full_text)} chars)")
            summary_info.append({"vid": vid, "author": author, "title": title, "status": "OK", "len": len(full_text)})
        else:
            print(f"  -> No transcript found for {vid}")
            summary_info.append({"vid": vid, "author": author, "title": title, "status": "NO_TRANSCRIPT"})
    except Exception as e:
        print(f"  -> ERROR: {e}")
        summary_info.append({"vid": vid, "author": author, "title": title, "status": f"ERROR: {e}"})

with open("scratch/transcripts_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary_info, f, indent=2, ensure_ascii=False)
