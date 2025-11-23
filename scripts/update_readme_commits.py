import subprocess
from pathlib import Path

USER = "Boburjon2142"
REPO = "artar"      # ← bu ARTAR uchun maxsus
N_COMMITS = 10       # nechta commit chiqsin

def get_commits():
    fmt = "%H|%h|%ad|%s|%an"
    out = subprocess.check_output(
        ["git", "log", f"-n{N_COMMITS}", "--date=short", f"--pretty=format:{fmt}"],
        text=True
    )
    commits = []
    for line in out.splitlines():
        full, short, date, msg, author = line.split("|", 4)
        commits.append({
            "full": full,
            "short": short,
            "date": date,
            "msg": msg,
            "author": author,
        })
    return commits

def make_card(c):
    url = f"https://github.com/{USER}/{REPO}/commit/{c['full']}"
    return f'''<a href="{url}" target="_blank">
  <div style="
      padding:12px 16px;
      margin:10px 0;
      border-radius:12px;
      border:1px solid #e1e4e8;
      background:#fafbfc;">
    <b>{c["msg"]}</b><br/>
    <sub>👤 {c["author"]} • 📅 {c["date"]} • <code>{c["short"]}</code></sub>
  </div>
</a>'''

def main():
    readme_path = Path("README.md")
    text = readme_path.read_text(encoding="utf-8")

    start = "<!-- COMMITS-START -->"
    end = "<!-- COMMITS-END -->"

    prefix, rest = text.split(start, 1)
    _, suffix = rest.split(end, 1)

    cards = "\n".join(make_card(c) for c in get_commits())

    new_text = prefix + start + "\n\n" + cards + "\n\n" + end + suffix
    readme_path.write_text(new_text, encoding="utf-8")

if __name__ == "__main__":
    main()
