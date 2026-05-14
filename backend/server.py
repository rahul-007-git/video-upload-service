import os
import psycopg2

from typing import List
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

UPLOAD_FOLDER = "uploads"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://docker:docker@localhost:5432/exampledb")

class VideoModel(BaseModel):
    id: int
    video_title: str
    video_url: str

app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

@app.get("/status")
async def check_status():
    return "Hello World!"

@app.get("/videos", response_model=List[VideoModel])
async def get_videos():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT * FROM video ORDER BY id DESC")
    rows = cur.fetchall()
    formatted_videos = []
    for row in rows:
        formatted_videos.append(
            VideoModel(id=row[0], video_title=row[1], video_url=row[2])
        )
    cur.close()
    conn.close()
    return formatted_videos

@app.post("/videos", status_code=201)
async def add_video(file: UploadFile):
    file_location = f"{UPLOAD_FOLDER}/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    uploaded_file_url = f"http://127.0.0.1:8000/uploads/{file.filename}"
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO video (video_title, video_url) VALUES ('{file.filename}', '{uploaded_file_url}')"
    )
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)