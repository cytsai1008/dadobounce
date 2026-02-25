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

# Detect if running as a compiled binary (Nuitka or PyInstaller)
_is_compiled = "__compiled__" in dir() or getattr(sys, "frozen", False)
# The real exe path (not the temp extraction dir)
_exe_path = os.path.abspath(sys.argv[0]) if _is_compiled else None

# Load GIF: __file__ works for both Nuitka and normal Python
_base = os.path.dirname(os.path.abspath(__file__))
gif_path = os.path.join(_base, "dado.gif")
img = Image.open(gif_path)
# Resample for crisp system tray display (16–32px typical)
TRAY_ICON_SIZE = 32
try:
    resample = Image.Resampling.LANCZOS
except AttributeError:
    resample = Image.LANCZOS
frames = []
for frame in ImageSequence.Iterator(img):
    f = frame.copy()
    if f.mode != "RGBA":
        f = f.convert("RGBA")
    f = f.resize((TRAY_ICON_SIZE, TRAY_ICON_SIZE), resample)
    frames.append(f)

delay = 0.05
frame_step = 1
global_stop = False

# --- Start with Windows (Startup folder shortcut) ---
def _startup_shortcut_path():
    """Return the path to the shortcut in the user's Startup folder."""
    startup_dir = os.path.join(
        os.environ["APPDATA"],
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
    )
    return os.path.join(startup_dir, "DadoBounce.lnk")

def _is_autostart_enabled():
    return os.path.exists(_startup_shortcut_path())

def _toggle_autostart():
    shortcut_path = _startup_shortcut_path()
    if _is_autostart_enabled():
        os.remove(shortcut_path)
    else:
        _create_shortcut(shortcut_path)

def _create_shortcut(shortcut_path):
    """Create a Windows .lnk shortcut pointing to the current executable."""
    if _is_compiled:
        target = _exe_path
        arguments = ""
    else:
        target = sys.executable  # python.exe
        arguments = f'"{os.path.abspath(__file__)}"'
    working_dir = os.path.dirname(target)

    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target
        shortcut.Arguments = arguments
        shortcut.WorkingDirectory = working_dir
        shortcut.Description = "DadoBounce CPU Monitor"
        shortcut.save()
    except ImportError:
        # Fallback: use PowerShell to create the shortcut
        ps_args = arguments.replace('"', '\\"') if arguments else ""
        ps_cmd = (
            f'$s=(New-Object -ComObject WScript.Shell).CreateShortcut(\'{shortcut_path}\');'
            f'$s.TargetPath=\'{target}\';'
            f'$s.Arguments=\'{ps_args}\';'
            f'$s.WorkingDirectory=\'{working_dir}\';'
            f'$s.Description=\'DadoBounce CPU Monitor\';'
            f'$s.Save()'
        )
        os.system(f'powershell -Command "{ps_cmd}"')

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
        pystray.MenuItem(
            "開機啟動",
            lambda: _toggle_autostart(),
            checked=lambda item: _is_autostart_enabled(),
        ),
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
