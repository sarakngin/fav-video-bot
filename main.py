from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import yt_dlp
import asyncio
import tempfile
import os
import subprocess

app = FastAPI()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    TOKEN = "YOUR_TELEGRAM_TOKEN_HERE"  # Replace with real token

application = Application.builder().token(TOKEN).build()

@app.get("/")
async def root():
    return {"status": "Bot is running! Watermark enabled."}

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.startswith("http"):
        await update.message.reply_text("📥 Send a social media video link!")
        return

    status = await update.message.reply_text("🔄 Downloading & adding watermark...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            download_path = f'{tmpdir}/video.mp4'
            ydl_opts = {
                'format': 'best[height<=720]',
                'outtmpl': download_path,
                'max_filesize': 48 * 1024 * 1024,
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])

            watermarked_path = f'{tmpdir}/final.mp4'
            watermark_text = "fav-video-bot"  # Change to your bot name

            subprocess.run([
                'ffmpeg', '-i', download_path,
                '-vf', f"drawtext=text='{watermark_text}':fontcolor=white:fontsize=28:box=1:boxcolor=black@0.6:x=10:y=10",
                '-codec:a', 'copy', '-y', watermarked_path
            ], check=True)

            with open(watermarked_path, 'rb') as video:
                await update.message.reply_video(video, caption="✅ Watermarked video ready!\n\nSend another link.")
            await status.delete()
    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)[:100]}")

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video))

@app.post("/webhook")
async def webhook(request: dict):
    update = Update.de_json(request, application.bot)
    asyncio.create_task(application.process_update(update))
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
