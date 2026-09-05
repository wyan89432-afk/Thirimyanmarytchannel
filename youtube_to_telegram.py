import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

CHANNEL_URL = os.getenv("YOUTUBE_CHANNEL_URL", "https://www.youtube.com/@thirimyanmar007/videos")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "@happydayfor").strip() or "@happydayfor"
STATE_FILE = Path("sent_videos.json")
MAX_HISTORY = 500

def load_state():
    if not STATE_FILE.exists():
        return {"sent": []}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("sent"), list):
            return data
    except Exception:
        pass
    return {"sent": []}

def save_state(state):
    state["sent"] = state["sent"][-MAX_HISTORY:]
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def get_videos():
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--flat-playlist",
        "--playlist-end", "30",
        "--print", "%(id)s\t%(title)s",
        CHANNEL_URL,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    videos = []
    for line in result.stdout.splitlines():
        if "\t" not in line:
            continue
        video_id, title = line.split("\t", 1)
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            videos.append({"id": video_id, "title": title})
    return videos

def send_to_telegram(video):
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN GitHub Secret is not configured.")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    video_url = f"https://www.youtube.com/watch?v={video['id']}"
    text = f"🎬 {video['title']}\n\n▶️ Watch on YouTube:\n{video_url}"
    response = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False,
    }, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(payload)
    print(f"Sent: {video['id']}")

def main():
    state = load_state()
    sent = set(state["sent"])
    videos = get_videos()

    # yt-dlp usually returns newest first; send unseen videos oldest -> newest.
    new_videos = [v for v in videos if v["id"] not in sent]
    if not new_videos:
        print("No new videos.")
        return

    for video in reversed(new_videos):
        send_to_telegram(video)
        state["sent"].append(video["id"])
        sent.add(video["id"])
        save_state(state)

if __name__ == "__main__":
    main()
