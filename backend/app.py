from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
from pathlib import Path
import threading
import time

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_PATH = Path("/app/test.jpg")

# Timelapse state
timelapse_running = False
timelapse_thread = None
frames_taken = 0
latest_frame_path: Path | None = None
latest_frame_time: int | None = None

class TimelapseConfig(BaseModel):
    frequency: int  # seconds between captures
    duration: int   # total duration in seconds
    resolution: str  # resolution string


def capture_timelapse(config: TimelapseConfig):
    """Background thread function to capture timelapse images"""
    global timelapse_running, frames_taken, latest_frame_time, latest_frame_path
    
    frames_taken = 0
    start_time = time.time()
    end_time = start_time + config.duration
    next_capture = start_time
    
    while timelapse_running and time.time() < end_time:        
        if time.time() >= next_capture:
            try:
                width, height = config.resolution.split('x')
                latest_frame_time = int(time.time())
                latest_frame_path = Path(f"/app/test_{latest_frame_time}.jpg")
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-f", "v4l2",
                        "-input_format", "mjpeg",
                        "-video_size", f"{width}x{height}",
                        "-i", "/dev/video0",
                        "-frames:v", "1",
                        str(latest_frame_path)
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
                frames_taken += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"Error capturing frame: {e}")
            
            next_capture += config.frequency
        
        # Sleep briefly to avoid busy-waiting
        time.sleep(0.1)
    
    timelapse_running = False


@app.get("/camera")
def camera():
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f", "v4l2",
                "-input_format", "mjpeg",
                "-video_size", "640x480",
                "-i", "/dev/video0",
                "-frames:v", "1",
                str(IMAGE_PATH)
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        print(str(IMAGE_PATH))
        if not IMAGE_PATH.exists():
            raise Exception("Image not created")
        return FileResponse(IMAGE_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/timelapse/start")
def start_timelapse(config: TimelapseConfig):
    """Start timelapse capture"""
    global timelapse_running, timelapse_thread
    
    if timelapse_running:
        raise HTTPException(status_code=400, detail="Timelapse already running")
    
    timelapse_running = True
    timelapse_thread = threading.Thread(target=capture_timelapse, args=(config,), daemon=True)
    timelapse_thread.start()
    
    return {"status": "timelapse started", "config": config}


@app.post("/timelapse/stop")
def stop_timelapse():
    """Stop timelapse capture"""
    global timelapse_running
    
    if not timelapse_running:
        raise HTTPException(status_code=400, detail="Timelapse not running")
    
    timelapse_running = False
    
    return {"status": "timelapse stopped"}

@app.get("/timelapse/frame-info")
def timelapse_frame_info():
    return {
        "frames_taken": frames_taken,
        "latest_frame_time": latest_frame_time,
    }

@app.get("/timelapse/latest-frame")
def get_latest_frame():
    if not latest_frame_path or not latest_frame_path.exists():
        raise HTTPException(status_code=404, detail="No frame available")
    if not latest_frame_path.exists():
        raise Exception("Image not created")
    return FileResponse(latest_frame_path)