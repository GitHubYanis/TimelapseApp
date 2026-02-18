# WSL2 Ubuntu + USB Camera + Docker Backend Setup

This document summarizes the steps to set up a working environment for using a USB camera in WSL2 Ubuntu and mapping it to a Dockerized Python backend.

---

## 1. Install Ubuntu WSL2

Open PowerShell as Administrator and run:
```powershell
wsl --install -d Ubuntu-22.04
```
- Follow prompts to create a username and password.

Verify installed WSL distros:
```powershell
wsl -l -v
```

## 2. Set Ubuntu as default

```powershell
wsl --setdefault Ubuntu-22.04
```
- Verify:
```powershell
wsl -l -v
```
- The `*` should now be next to `Ubuntu-22.04`.

## 3. Shutdown all WSL instances

```powershell
wsl --shutdown
```

- This ensures clean restart of WSL2.

## 4. Start Ubuntu WSL

```powershell
wsl
```
- You should now be in the Ubuntu shell, not Docker Desktop VM.
- Check Ubuntu version:
```bash
lsb_release -a
```
- Check kernel version:
```bash
uname -r
```

## 5. Attach USB camera via USB/IP

**In Windows PowerShell:**
```powershell
usbipd wsl list
usbipd wsl attach --busid <busid>
```

**In Ubuntu WSL:**
```bash
ls /dev/video*
```
- You should now see `/dev/video0`.

> Note: Step 5 installs the camera in WSL. No extra build tools are required if `/dev/video0` appears.

## 6. Verify camera is accessible

```bash
ls /dev/video*
```
- `/dev/video0` should be listed.
- If it appears, WSL Ubuntu can access the USB camera.

---

## Notes

- The build-essential and kernel tools are only needed if you plan to build a custom WSL2 kernel.
- If `/dev/video0` works with USB/IP, you can skip installing build tools.
- Ensure Docker runs **inside Ubuntu WSL**, not Docker Desktop VM, to access `/dev/video0`.

---

This setup allows the FastAPI backend in Docker to capture images from the USB camera using `/dev/video0`.

