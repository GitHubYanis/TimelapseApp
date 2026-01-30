# from fastapi import FastAPI, Response
# import imageio.v3 as iio
# import io

# app = FastAPI()

# @app.get("/camera")
# def capture_image():
#     try:
#         frame = iio.imread("<video0>")  # capture from first camera
#         buf = io.BytesIO()
#         iio.imwrite(buf, frame, format="jpg")
#         return Response(content=buf.getvalue(), media_type="image/jpeg")
#     except Exception as e:
#         return Response(content=str(e), status_code=500)

# this works:
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import subprocess
from pathlib import Path

app = FastAPI()
IMAGE_PATH = Path("/app/test.jpg")

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
        if not IMAGE_PATH.exists():
            raise Exception("Image not created")
        return FileResponse(IMAGE_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# from fastapi import FastAPI, HTTPException
# from fastapi.responses import FileResponse
# import imageio.v3 as iio
# from pathlib import Path

# app = FastAPI()

# IMAGE_PATH = Path("/app/test.jpg")  # where snapshot will be saved

# @app.get("/camera")
# def camera():
#     """
#     Capture a single frame from /dev/video0 using imageio + ffmpeg
#     and return it as a FileResponse.
#     """
#     try:
#         # Capture frame from camera
#         frame = iio.imread("v4l2:///dev/video0", plugin="ffmpeg", size=(640, 480))

#         # Save to file
#         iio.imwrite(IMAGE_PATH, frame, format="jpg")

#         return FileResponse(IMAGE_PATH)

#     except Exception as e:
#         # Return HTTP 500 if capture fails
#         raise HTTPException(status_code=500, detail=f"Failed to capture image: {e}")

# from fastapi import FastAPI, HTTPException
# from fastapi.responses import StreamingResponse
# import imageio.v3 as iio
# import io

# app = FastAPI()

# @app.get("/camera")
# def camera():
#     try:
#         # Capture a single frame from the camera
#         frame = iio.imread(
#             "/dev/video0",
#             plugin="ffmpeg",
#             format_hint=".v4l2"
#         )
        
#         # Convert to JPEG in memory
#         img_bytes = iio.imwrite("<bytes>", frame, extension=".jpg")
        
#         return StreamingResponse(
#             io.BytesIO(img_bytes),
#             media_type="image/jpeg"
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))