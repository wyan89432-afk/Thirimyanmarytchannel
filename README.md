# YouTube → Telegram Auto Sender

This GitHub Actions project checks the YouTube channel every 5 minutes and sends newly detected videos to Telegram.

## Configuration

Repository → **Settings → Secrets and variables → Actions → New repository secret**

Add:

- `TELEGRAM_BOT_TOKEN` = token from BotFather for @Thirimyanmar_bot
- `TELEGRAM_CHAT_ID` = optional. Default is `@happydayfor`

The bot must be added to the Telegram group/channel and allowed to send messages.

## YouTube

https://www.youtube.com/@thirimyanmar007/videos

## Duplicate protection

`sent_videos.json` stores sent YouTube video IDs. After a successful Telegram send, the workflow commits the ID back to GitHub so the same video is not sent again.

## Manual test

Open **Actions → YouTube to Telegram → Run workflow**.

> Note: GitHub scheduled workflows use a 5-minute cron expression, but actual execution can occasionally be delayed by GitHub Actions load.
