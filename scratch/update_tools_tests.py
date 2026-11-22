import glob

def replace_in_files(pattern):
    for f in glob.glob(pattern, recursive=True):
        try:
            with open(f, "r", encoding="utf-8") as file:
                content = file.read()
            if "ICT Sabri Malle" in content:
                new_content = content.replace("ICT Sabri Malle", "ICT")
                with open(f, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Updated {f} ({content.count('ICT Sabri Malle')} matches)")
        except Exception as e:
            print(f"Error updating {f}: {e}")

replace_in_files("tools/**/*.py")
replace_in_files("tests/**/*.py")
