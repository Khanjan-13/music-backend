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
        # Choose the first audio format URL explicitly
        audio_url = None
        for f in info["formats"]:
            if f.get("acodec") != "none":
                audio_url = f["url"]
                break

        if not audio_url:
            raise Exception("No audio format found.")

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
            "audio_url": audio_url,
            "thumbnail": info.get("thumbnail"),
            "related": related,
        }


@app.get("/download")
def download_audio(video_id: str):
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

        # Get the filename from postprocessing
        if "requested_downloads" in info and info["requested_downloads"]:
            downloaded_file = info["requested_downloads"][0]["filepath"]
        else:
            # Fallback
            downloaded_file = ydl.prepare_filename(info)
            downloaded_file = os.path.splitext(downloaded_file)[0] + ".mp3"

    return FileResponse(
        downloaded_file,
        media_type="audio/mpeg",
        filename=os.path.basename(downloaded_file)
    )
