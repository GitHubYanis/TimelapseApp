from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import threading
import time
import uuid
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import imageio.v2 as iio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TIMELAPSES_DIR = Path("/app/timelapses")
VIDEO_TEMP_DIR = Path("/tmp")
DEFAULT_RESOLUTION = "640x480"

class TimelapseConfig(BaseModel):
    frequency: int  # seconds between captures
    duration: int   # total duration in seconds
    resolution: str  # resolution string

# Timelapse state
class TimelapseState:
    """Manages the current timelapse session state."""
    running: bool = False
    thread: threading.Thread | None = None
    frames_taken: int = 0
    latest_frame_path: Path | None = None
    latest_frame_time: int | None = None
    config: TimelapseConfig | None = None
    start_time: float | None = None
    id: str | None = None
    
    def reset(self) -> None:
        """Reset state to initial values."""
        self.running = False
        self.thread = None
        self.frames_taken = 0
        self.latest_frame_path = None
        self.latest_frame_time = None
        self.config = None
        self.start_time = None
        self.id = None

state = TimelapseState()


def capture_frame(output_path: Path, resolution: str) -> bool:
    try:
        width, height = resolution.split('x')
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "v4l2",
                "-input_format", "mjpeg",
                "-video_size", f"{width}x{height}",
                "-i", "/dev/video0",
                "-frames:v", "1",
                str(output_path)
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        return True
    except Exception as e:
        print(f"Error capturing frame: {e}")
        return False

def capture_timelapse_worker(config: TimelapseConfig, timelapse_id: str) -> None:
    global state
    
    state.frames_taken = 0
    start_time = time.time()
    end_time = start_time + config.duration
    next_capture = start_time
    
    # Create timelapse folder
    timelapse_folder = TIMELAPSES_DIR / timelapse_id
    timelapse_folder.mkdir(parents=True, exist_ok=True)
    
    while state.running and time.time() < end_time:        
        if time.time() >= next_capture:
            state.latest_frame_time = int(time.time())
            state.latest_frame_path = timelapse_folder / f"frame_{state.latest_frame_time}.jpg"
            
            if capture_frame(state.latest_frame_path, config.resolution):
                state.frames_taken += 1
                time.sleep(0.5)
            
            next_capture += config.frequency
        
        time.sleep(0.1)
    
    state.running = False


@app.get("/camera")
def camera():
    temp_image = VIDEO_TEMP_DIR / "camera.jpg"
    if capture_frame(temp_image, DEFAULT_RESOLUTION):
        return FileResponse(temp_image)
    raise HTTPException(status_code=500, detail="Failed to capture frame")


@app.post("/timelapse/start")
def start_timelapse(config: TimelapseConfig) -> dict:
    global state
    
    if state.running:
        raise HTTPException(status_code=400, detail="Timelapse already running")
    
    state.running = True
    state.config = config
    state.start_time = time.time()
    state.id = str(uuid.uuid4())
    state.thread = threading.Thread(
        target=capture_timelapse_worker,
        args=(config, state.id),
        daemon=True
    )
    state.thread.start()
    
    return {"status": "timelapse started", "config": config, "timelapse_id": state.id}


@app.post("/timelapse/stop")
def stop_timelapse() -> dict:
    global state
    
    if not state.running:
        raise HTTPException(status_code=400, detail="Timelapse not running")
    
    state.reset()
    return {"status": "timelapse stopped"}

@app.get("/timelapse/status")
def get_timelapse_status() -> dict:
    global state
    
    expected_frames = None
    end_date = None
    if state.config and state.start_time:
        expected_frames = state.config.duration // state.config.frequency
        end_date = state.start_time + state.config.duration
    
    return {
        "running": state.running,
        "config": state.config.dict() if state.config else None,
        "frames_taken": state.frames_taken,
        "expected_frames": expected_frames,
        "end_date": end_date,
        "latest_frame_time": state.latest_frame_time,
        "timelapse_id": state.id,
    }


@app.get("/timelapse/frame-info")
def timelapse_frame_info() -> dict:
    global state
    return {
        "frames_taken": state.frames_taken,
        "latest_frame_time": state.latest_frame_time,
    }


@app.get("/timelapse/latest-frame")
def get_latest_frame():
    global state
    if not state.latest_frame_path or not state.latest_frame_path.exists():
        raise HTTPException(status_code=404, detail="No frame available")
    return FileResponse(state.latest_frame_path)


@app.get("/timelapses")
def list_timelapses() -> dict:
    if not TIMELAPSES_DIR.exists():
        return {"timelapses": []}
    
    timelapses = []
    for timelapse_folder in TIMELAPSES_DIR.iterdir():
        if timelapse_folder.is_dir():
            frames = list(timelapse_folder.glob("*.jpg"))
            if frames:
                latest_frame = max(frames, key=lambda x: x.stat().st_mtime)
                mtime_timestamp = latest_frame.stat().st_mtime
                dt_utc = datetime.fromtimestamp(mtime_timestamp, tz=ZoneInfo("UTC"))
                dt_eastern = dt_utc.astimezone(ZoneInfo("America/New_York"))
                
                timelapses.append({
                    "id": timelapse_folder.name,
                    "date": dt_eastern.strftime("%Y-%m-%d %H:%M:%S"),
                    "frames": len(frames),
                    "name": f"Timelapse {timelapse_folder.name[:8]}"
                })
    
    timelapses.sort(key=lambda x: x["date"], reverse=True)
    return {"timelapses": timelapses}

@app.get("/timelapse/{timelapse_id}/download")
def download_timelapse(timelapse_id: str):
    timelapse_folder = TIMELAPSES_DIR / timelapse_id
    if not timelapse_folder.exists():
        raise HTTPException(status_code=404, detail="Timelapse not found")
    
    frames = sorted(
        timelapse_folder.glob("*.jpg"),
        key=lambda x: x.stat().st_mtime
    )
    
    if not frames:
        raise HTTPException(status_code=404, detail="No frames found")
    
    video_path = VIDEO_TEMP_DIR / f"{timelapse_id}.mp4"
    
    try:
        with iio.get_writer(
            str(video_path),
            format='FFMPEG',
            mode='I',
            fps=30,
            macro_block_size=8
        ) as writer:
            for frame_path in frames:
                image = iio.imread(frame_path)
                writer.append_data(image)
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=f"timelapse_{timelapse_id}.mp4"
        )
    except Exception as e:
        if video_path.exists():
            video_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error creating video: {str(e)}")

@app.delete("/timelapse/{timelapse_id}")
def delete_timelapse(timelapse_id: str) -> dict:
    timelapse_folder = TIMELAPSES_DIR / timelapse_id
    if not timelapse_folder.exists():
        raise HTTPException(status_code=404, detail="Timelapse not found")
    
    try:
        shutil.rmtree(timelapse_folder)
        return {"status": "timelapse deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting timelapse: {str(e)}")