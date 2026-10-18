for vid, fpath in [
    ('J3qTJefkD-A', 'scratch/transcript_J3qTJefkD-A.txt'),
    ('zgpstRvSwhk', 'scratch/transcript_zgpstRvSwhk.txt'),
    ('GWn5LiOSBlA', 'scratch/transcript_GWn5LiOSBlA.txt')
]:
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()
    print("=" * 80)
    print(f"VIDEO {vid}")
    lines = [l for l in text.split("\n") if l.strip()]
    print("\n".join(lines[:40]))
    print("\n... MIDDLE ...\n")
    print("\n".join(lines[len(lines)//2 : len(lines)//2 + 40]))
