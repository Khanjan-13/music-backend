from fastapi import FastAPI
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
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        related = []
        if "related" in info:
            for rel in info["related"]:
                related.append({
                    "id": rel["id"],
                    "title": rel["title"],
                    "url": f"https://www.youtube.com/watch?v={rel['id']}",
                    "thumbnail": rel.get("thumbnail"),
                    "duration": rel.get("duration"),
                    "uploader": rel.get("uploader"),
                })

        return {
            "title": info["title"],
            "audio_url": info["url"],
            "thumbnail": info.get("thumbnail"),
            "related": related,
        }

@app.get("/download")
def download_audio(video_id: str):
    # Define output path
    output_dir = "/tmp"
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "outtmpl": output_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
        filename = ydl.prepare_filename(info)
        mp3_filename = os.path.splitext(filename)[0] + ".mp3"

    # Return file response
    return FileResponse(
        mp3_filename,
        media_type="audio/mpeg",
        filename=os.path.basename(mp3_filename)
    )
