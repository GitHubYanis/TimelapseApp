from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from services import timelapse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/camera")
def camera():
    temp_image = timelapse.VIDEO_TEMP_DIR / "camera.jpg"
    if timelapse.capture_frame(temp_image):
        return FileResponse(temp_image)
    raise HTTPException(status_code=500, detail="Failed to capture frame")


@app.post("/timelapse/start")
def start_timelapse(config: timelapse.TimelapseConfig) -> dict:
    try:
        return timelapse.start_timelapse(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/timelapse/stop")
def stop_timelapse() -> dict:
    try:
        return timelapse.stop_timelapse()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/timelapse/status")
def timelapse_status() -> dict:
    return timelapse.get_timelapse_status()


@app.get("/timelapse/frame-info")
def timelapse_frame_info() -> dict:
    return timelapse.get_timelapse_frame_info()


@app.get("/timelapse/latest-frame")
def get_latest_frame():
    try:
        frame_path = timelapse.get_latest_frame()
        return FileResponse(frame_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/timelapses")
def list_timelapses_endpoint() -> dict:
    timelapses = timelapse.list_timelapses()
    return {"timelapses": timelapses}

@app.get("/timelapse/{timelapse_id}/download")
def download_timelapse(timelapse_id: str):
    try:
        video_path = timelapse.download_timelapse(timelapse_id)
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=f"timelapse_{timelapse_id}.mp4"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/timelapse/{timelapse_id}")
def delete_timelapse(timelapse_id: str) -> dict:
    try:
        return timelapse.delete_timelapse(timelapse_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))