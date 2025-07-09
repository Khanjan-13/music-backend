from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from yt_dlp import YoutubeDL
import os

app = FastAPI()

# Allow Flutter to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search")
def search(query: str):
    ydl_opts = {
        "quiet": True,
        "extract_flat": "in_playlist",
        "force_generic_extractor": True,
        "default_search": "ytsearch20",  # Search top 20
    }

    results = []
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        for entry in info.get("entries", []):
            results.append({
                "id": entry["id"],
                "title": entry["title"],
                "url": f"https://www.youtube.com/watch?v={entry['id']}",
                "thumbnail": entry.get("thumbnail"),
                "duration": entry.get("duration"),
                "uploader": entry.get("uploader"),
            })

    return {"results": results}

@app.get("/audio")
def get_audio(video_id: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "cookiefile": "cookies.txt",  # <== this line enables cookies
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=False
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YoutubeDL error: {str(e)}")

    audio_url = None
    for f in info["formats"]:
        if f.get("acodec") != "none":
            audio_url = f["url"]
            break

    if not audio_url:
        raise HTTPException(status_code=500, detail="No audio URL found")

    return {
        "title": info.get("title"),
        "audio_url": audio_url,
        "thumbnail": info.get("thumbnail"),
    }

@app.get("/download")
def download_audio(video_id: str):
    output_dir = "/tmp"
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + ".mp3"

            if not os.path.exists(mp3_filename):
                raise HTTPException(status_code=500, detail="MP3 file not found after download")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading audio: {str(e)}")

    return FileResponse(
        mp3_filename,
        media_type="audio/mpeg",
        filename=os.path.basename(mp3_filename)
    )
