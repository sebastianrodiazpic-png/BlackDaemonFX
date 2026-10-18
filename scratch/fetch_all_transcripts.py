import json
from youtube_transcript_api import YouTubeTranscriptApi

videos = [
    ('J3qTJefkD-A', 'Alex Ruiz - La Estrategia De ICT Mas Facil De Usar (nunca se pierde)'),
    ('zgpstRvSwhk', 'Alex Ruiz - La Mejor Estrategia De Trading Con ICT En El Oro'),
    ('GWn5LiOSBlA', 'Alex Ruiz - Compruebo Si La Mejor Estrategia De Trading De ICT Funciona'),
    ('f8sSwcP9KwQ', 'Toni Maura - Esta Estrategia ICT Me Hizo Ganar +$47,000 y Vivir del Trading'),
    ('Iq_MxtYvRww', 'El Sensei - Copia Esta Estrategia de ICT en 2025, te Hara Rentable'),
    ('QFvkAZjUnUE', 'Fede Esses - La GUIA DEFINITIVA de ICT en Espanol | Explicado Simple'),
    ('R3sAS1J3_fE', 'Sabri Malle - Como Gano +500e al Dia con Esta Estrategia ICT (Facil)'),
    ('lGChZzNybGY', 'Sabri Malle - UNA ESTRATEGIA QUE ME GENERA +1000e/DIA EN 3 PASOS'),
    ('EO8odUZNdjc', 'Sabri Malle - Domina los Order Blocks y opera como los bancos')
]

ytt = YouTubeTranscriptApi()

for vid, title in videos:
    print(f"\n==========================================")
    print(f"Fetching transcript for: {vid} - {title}")
    try:
        t_list = ytt.list(vid)
        # find available languages
        available = [t.language_code for t in t_list]
        print(f"Available languages: {available}")
        
        # prefer es, then es-419, then en, or first available
        transcript = None
        for lang in ['es', 'es-419', 'en']:
            if lang in available:
                transcript = t_list.find_transcript([lang]).fetch()
                break
        if transcript is None:
            # try to get the first one
            for t in t_list:
                transcript = t.fetch()
                break
                
        out_path = f"scratch/transcript_{vid}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"TITLE: {title}\nURL: https://www.youtube.com/watch?v={vid}\n\n")
            for entry in transcript:
                start = int(entry.start if hasattr(entry, 'start') else entry['start'])
                m, s = divmod(start, 60)
                text = entry.text if hasattr(entry, 'text') else entry['text']
                f.write(f"[{m:02d}:{s:02d}] {text}\n")
        print(f"Successfully saved {len(transcript)} chunks to {out_path}")
    except Exception as e:
        print(f"Error fetching {vid}: {e}")
