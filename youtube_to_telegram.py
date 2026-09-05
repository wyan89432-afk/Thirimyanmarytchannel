import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

CHANNEL_URL = os.getenv("YOUTUBE_CHANNEL_URL", "https://www.youtube.com/@thirimyanmar007/videos")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "@happydayfor").strip() or "@happydayfor"
STATE_FILE = Path("sent_videos.json")

def load_state():
    if not STATE_FILE.exists():
        return {"last_sent": None}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {"last_sent": data.get("last_sent")}
    except Exception:
        pass
    return {"last_sent": None}

def save_state(video_id):
    STATE_FILE.write_text(
        json.dumps({"last_sent": video_id}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def get_latest_video():
    # Fetch ONLY the newest video. Older videos are intentionally ignored.
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--flat-playlist",
        "--playlist-end", "1",
        "--print", "%(id)s\t%(title)s",
        CHANNEL_URL,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    for line in result.stdout.splitlines():
        if "\t" not in line:
            continue
        video_id, title = line.split("\t", 1)
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            return {"id": video_id, "title": title}

    raise RuntimeError("Could not find the latest YouTube video.")

def send_to_telegram(video):
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN GitHub Secret is not configured.")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    video_url = f"https://www.youtube.com/watch?v={video['id']}"
    text = f"🎬 {video['title']}\n\n▶️ Watch on YouTube:\n{video_url}"

    # Small retry for temporary Telegram rate limits.
    for attempt in range(3):
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "disable_web_page_preview": False,
            },
            timeout=30,
        )

        if response.status_code == 429:
            retry_after = response.json().get("parameters", {}).get("retry_after", 5)
            print(f"Telegram rate limit. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue

        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(payload)

        print(f"Sent latest video: {video['id']}")
        return

    raise RuntimeError("Telegram rate limit retry failed.")

def main():
    state = load_state()
    video = get_latest_video()

    if video["id"] == state.get("last_sent"):
        print("Latest video was already sent.")
        return

    # Send ONLY one video: the current newest upload.
    send_to_telegram(video)
    save_state(video["id"])

if __name__ == "__main__":
    main()
