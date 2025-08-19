import re
import asyncio
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

import yt_dlp
from telegram import Update, InputFile
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

# Telegram bot tokenini shu yerga yozing
BOT_TOKEN = "8303690654:AAHmEuVyFzyJxpgDZoUOCDaUgfQhoKBkbbo"

URL_REGEX = re.compile(r"(https?://[^\s]+)", re.IGNORECASE)

def extract_first_url(text: str) -> Optional[str]:
    m = URL_REGEX.search(text or "")
    return m.group(1) if m else None

def download_video(url: str, tmpdir: Path) -> Path:
    """
    Videoni 1080p (agar bo'lmasa best) sifatida yuklab, mp4 fayl yo'lini qaytaradi.
    """
    outtmpl = str(tmpdir / "%(title).200B [%(id)s].%(ext)s")
    ydl_opts: Dict[str, Any] = {
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "format": "bestvideo[height<=1080]+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
        "retries": 5,
        "concurrent_fragment_downloads": 4,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if "requested_downloads" in info and info["requested_downloads"]:
            fp = Path(info["requested_downloads"][-1]["filepath"]) 
        else:
            fp = Path(ydl.prepare_filename(info))
            if fp.suffix.lower() != ".mp4":
                fp = fp.with_suffix(".mp4")
    return fp

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Instagram, TikTok yoki YouTube videolaridan link yuboring. Bot faqat videoni jo'natadi 📹"
        )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    url = extract_first_url(update.message.text or "")
    if not url:
        await update.message.reply_text("Iltimos, haqiqiy URL yuboring.")
        return 

    try:
        with tempfile.TemporaryDirectory(prefix="tgvid-") as td:
            tdir = Path(td)
            loop = asyncio.get_running_loop()
            video_path = await loop.run_in_executor(None, download_video, url, tdir)

            with open(video_path, "rb") as vf:
                await update.message.reply_video(video=InputFile(vf, filename=video_path.name))
    except Exception as e:
        print("Download/send error:", e)
        await update.message.reply_text("Videoni yuklab bo‘lmadi ❌")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_url))
    app.run_polling()

if __name__ == "__main__":
    main()
