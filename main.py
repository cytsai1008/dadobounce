import os
import sys
import psutil
import pystray
from PIL import Image, ImageSequence
import threading
import time

# Windows: Hide console window when running in background
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )  # 0 = SW_HIDE
    except Exception:
        pass

# Windows: For higher resolution timer
if sys.platform == "win32":
    try:
        import ctypes
        winmm = ctypes.windll.winmm
        winmm.timeBeginPeriod(1)  # 1ms resolution
    except Exception:
        pass

# Load GIF: Read from sys._MEIPASS when bundled as exe
if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.abspath(__file__))
gif_path = os.path.join(_base, "dado.gif")
img = Image.open(gif_path)
frames = [frame.copy() for frame in ImageSequence.Iterator(img)]

delay = 0.05
frame_step = 1
global_stop = False

def get_cpu_speed_delay():
    global delay, frame_step, global_stop
    while not global_stop:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        t = 1 - (cpu_usage / 100)
        # Linear: CPU 0% → delay 0.1, CPU 100% → delay 0.005
        delay = max(0.005, min(0.1, 0.1 - 0.00095 * cpu_usage))
        frame_step = 1 + int((1 - t) * 3)
        frame_step = min(frame_step, max(1, len(frames) // 6))
        
def update_title(icon):
    global global_stop
    while not global_stop:
        cpu_usage = psutil.cpu_percent(interval=1)
        icon.title = f"CPU 使用率: {cpu_usage}%"

def update_icon(icon):
    global global_stop, delay, frame_step
    frame_idx = 0
    while not global_stop:
        icon.icon = frames[frame_idx]
        frame_idx = (frame_idx + frame_step) % len(frames)
        time.sleep(delay)

def stop(icon):
    global global_stop
    global_stop = True
    if sys.platform == "win32":
        try:
            winmm.timeEndPeriod(1)
        except Exception:
            pass
    icon.stop()

def main():
    # Create notification icon
    icon = pystray.Icon("CPU_Monitor")
    icon.icon = frames[0]
    icon.title = "CPU 速度監控中"
    icon.menu = pystray.Menu(
        pystray.MenuItem("退出", lambda: stop(icon)),
    )

    get_cpu_thread = threading.Thread(target=get_cpu_speed_delay, daemon=True)
    get_cpu_thread.start()

    update_icon_thread = threading.Thread(target=update_icon, args=(icon,), daemon=True)
    update_icon_thread.start()

    update_title_thread = threading.Thread(target=update_title, args=(icon,), daemon=True)
    update_title_thread.start()

    icon.run()

if __name__ == "__main__":
    main()
