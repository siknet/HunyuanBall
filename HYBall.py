import sys
import json
import os
import time
import subprocess
import threading
import webbrowser
import ctypes
import urllib.request
import socket
from datetime import datetime
from ctypes import wintypes

import pystray
from pystray import MenuItem as item
from PIL import Image

# -----------------------------
# Global Control
# -----------------------------
shutdown_event = threading.Event()

# -----------------------------
# Ctypes Windows Notification
# -----------------------------
class NOTIFYICONDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", ctypes.c_wchar * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", ctypes.c_wchar * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", ctypes.c_ubyte * 16),
        ("hBalloonIcon", wintypes.HICON),
    ]

NIM_ADD = 0
NIM_MODIFY = 1
NIM_DELETE = 2
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010
NIIF_INFO = 0x00000001
PM_REMOVE = 0x0001

def _toast_worker(title, msg):
    try:
        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32
        
        hwnd = user32.CreateWindowExW(0, "STATIC", "TempNotifyWindow", 0, 0, 0, 0, 0, 0, 0, 0, 0)
        if not hwnd: return

        nid = NOTIFYICONDATA()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
        nid.hWnd = hwnd
        nid.uID = 1
        nid.dwInfoFlags = NIIF_INFO
        nid.szInfoTitle = title[:63]
        nid.szInfo = msg[:255]
        nid.szTip = title[:127]
        nid.hIcon = user32.LoadIconW(0, 32512)

        # ---------------------------------------------------------
        # 核心修改：两步走策略
        # 1. 先把图标放上去，不带气泡，只带图标
        # ---------------------------------------------------------
        nid.uFlags = NIF_ICON | NIF_TIP
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
        
        # 给系统 100ms 反应时间，让图标“坐稳”
        time.sleep(0.1)

        # ---------------------------------------------------------
        # 2. 再发送修改命令，把气泡文字“注入”进去
        # 这会强制 Windows 刷新通知状态，大幅提高弹出成功率
        # ---------------------------------------------------------
        nid.uFlags = NIF_ICON | NIF_TIP | NIF_INFO
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))
        
        start_ts = time.time()
        msg_struct = wintypes.MSG()
        
        # 维持 5 秒
        while time.time() - start_ts < 5.0:
            if shutdown_event.is_set():
                break
            if user32.PeekMessageW(ctypes.byref(msg_struct), hwnd, 0, 0, PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(msg_struct))
                user32.DispatchMessageW(ctypes.byref(msg_struct))
            time.sleep(0.1)
            
    except Exception:
        pass
    finally:
        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
        user32.DestroyWindow(hwnd)

def show_native_toast(title, msg):
    t = threading.Thread(target=_toast_worker, args=(title, msg))
    t.daemon = False 
    t.start()

# -----------------------------
# Paths & Globals
# -----------------------------
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LLAMA_DIR = os.path.join(BASE_DIR, "llama")
WEBUI_DIR = os.path.join(BASE_DIR, "webui")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

STATE_STOPPED = "STOPPED"
STATE_STARTING = "STARTING"
STATE_RUNNING = "RUNNING"
STATE_ERROR = "ERROR"

proc = None
lock = threading.Lock()
app_state = STATE_STOPPED
tray_icon = None

start_token = 0
LOG_RETENTION_DAYS = 30

# -----------------------------
# Logging
# -----------------------------
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def launcher_log_path():
    return os.path.join(LOG_DIR, "launcher.log")

def server_log_path():
    return os.path.join(LOG_DIR, "llama-server.log")

def append_launcher_log(msg: str):
    try:
        with open(launcher_log_path(), "a", encoding="utf-8") as f:
            f.write(f"[{now()}] {msg}\n")
    except Exception:
        pass

# -----------------------------
# Maintenance
# -----------------------------
def cleanup_old_logs(log_dir: str, keep_days: int):
    try:
        if not os.path.isdir(log_dir): return
        now_ts = time.time()
        expire_sec = keep_days * 24 * 60 * 60
        for name in os.listdir(log_dir):
            path = os.path.join(log_dir, name)
            if not os.path.isfile(path): continue
            try:
                if now_ts - os.path.getmtime(path) > expire_sec: os.remove(path)
            except Exception: pass
    except Exception: pass

def cleanup_old_mei_dirs(keep_hours: int = 24):
    try:
        temp_dir = os.environ.get("TEMP")
        if not temp_dir or not os.path.isdir(temp_dir): return
        now_ts = time.time()
        expire_sec = keep_hours * 3600
        import shutil
        for name in os.listdir(temp_dir):
            if not name.startswith("_MEI"): continue
            path = os.path.join(temp_dir, name)
            if not os.path.isdir(path): continue
            try:
                if now_ts - os.path.getmtime(path) > expire_sec: shutil.rmtree(path, ignore_errors=True)
            except Exception: pass
    except Exception: pass

# -----------------------------
# Utils
# -----------------------------
def msgbox(title: str, text: str):
    try: ctypes.windll.user32.MessageBoxW(0, text, title, 0x40)
    except: pass

def load_config() -> dict:
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception: pass

    if "autostart" not in cfg and "auto_start" in cfg:
        cfg["autostart"] = bool(cfg["auto_start"])

    cfg.setdefault("autostart", False)
    cfg.setdefault("open_webui_on_ready", False)
    cfg.setdefault("show_tips", True)
    cfg.setdefault("model_path", "models\\model.gguf")
    cfg.setdefault("host", "127.0.0.1")
    cfg.setdefault("port", 58088)
    cfg.setdefault("threads", 2)
    cfg.setdefault("threads_batch", 2)
    cfg.setdefault("ctx", 2048)
    cfg.setdefault("batch", 256)
    cfg.setdefault("extra_args", [])
    return cfg

def notify(title: str, msg: str, cfg: dict | None = None):
    try:
        if cfg and not bool(cfg.get("show_tips", True)): return
    except: pass
    show_native_toast(title, msg)

def get_state():
    with lock: return app_state

def can_start(): return get_state() in (STATE_STOPPED, STATE_ERROR)
def can_stop(): return get_state() in (STATE_STARTING, STATE_RUNNING)

def is_running_process():
    global proc
    with lock: return proc is not None and proc.poll() is None

def _update_title_for_state(st: str):
    global tray_icon
    if tray_icon is None: return
    try:
        cfg = load_config()
        port = cfg.get("port", 58088)
        host = cfg.get("host", "127.0.0.1")
        if host == "0.0.0.0": host = "LAN"
        tray_icon.title = f"混元球 {st} [{host}:{port}]"
    except: pass

def set_state(st: str):
    global app_state, tray_icon
    with lock: app_state = st
    _update_title_for_state(st)
    try:
        if tray_icon: tray_icon.update_menu()
    except: pass

def resolve_model_path(cfg: dict) -> str:
    p = cfg["model_path"]
    return os.path.abspath(os.path.join(BASE_DIR, p)) if not os.path.isabs(p) else p

def build_args(cfg: dict):
    exe = os.path.join(LLAMA_DIR, "llama-server.exe")
    model_path = resolve_model_path(cfg)
    host = cfg.get("host", "127.0.0.1")
    port = str(cfg.get("port", 58088))
    args = [
        exe, "-m", model_path, "--host", host, "--port", port,
        "-t", str(cfg.get("threads", 2)), "-tb", str(cfg.get("threads_batch", 2)),
        "-c", str(cfg.get("ctx", 2048)), "-b", str(cfg.get("batch", 256)),
        "--path", WEBUI_DIR
    ]
    for a in cfg.get("extra_args", []):
        if "--no-webui" in a: continue
        args.append(a)
    return exe, args, model_path

# -----------------------------
# Checks
# -----------------------------
def is_port_open(host: str, port: int) -> bool:
    try:
        check_host = host
        if host == "0.0.0.0": check_host = "127.0.0.1"
        with socket.create_connection((check_host, port), timeout=0.5):
            return True
    except:
        return False

def is_server_ready(host: str, port: int) -> bool:
    check_host = host
    if check_host == "0.0.0.0": check_host = "127.0.0.1"
    try:
        url = f"http://{check_host}:{port}/v1/models"
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with opener.open(req, timeout=3.0) as r:
            if r.status == 200:
                append_launcher_log("Ready check: /v1/models returned 200 OK")
                return True
    except Exception: pass 
    try:
        url = f"http://{check_host}:{port}/index.html"
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request(url)
        with opener.open(req, timeout=3.0) as r:
            if r.status == 200:
                append_launcher_log("Ready check: index.html returned 200 OK")
                return True
    except Exception: pass
    return False

# -----------------------------
# Actions
# -----------------------------
def open_webui(_=None):
    try:
        cfg = load_config()
        host = cfg.get("host", "127.0.0.1")
        port = cfg.get("port", 58088)
        target = "127.0.0.1" if host == "0.0.0.0" else host
        url = f"http://{target}:{port}"
        webbrowser.open(url)
    except Exception as e:
        notify("混元球", "打开浏览器失败")

def open_logs(_=None):
    try: webbrowser.open("file:///" + os.path.abspath(LOG_DIR).replace("\\", "/"))
    except: pass

def about(_=None):
    msgbox("关于 混元球", "Tencent-HY-MT1.5-1.8B\nHTTP WebUI Mode\nHansah@V2ex 2026")

def start_server(_=None):
    global proc, start_token
    if not can_start(): return

    with lock:
        start_token += 1
        my_token = start_token

    try:
        cfg = load_config()
        host = cfg.get("host", "127.0.0.1")
        port = int(cfg.get("port", 58088))
    except Exception:
        notify("混元球", "配置读取失败")
        return

    exe, args, model_path = build_args(cfg)

    if not os.path.exists(exe):
        notify("混元球", "错误：找不到 llama-server.exe", cfg)
        return
    if not os.path.exists(model_path):
        notify("混元球", "错误：找不到模型文件", cfg)
        return

    if is_port_open(host, port):
        set_state(STATE_RUNNING)
        notify("混元球", "检测到服务已在运行", cfg)
        def late_ready():
            for i in range(10):
                if shutdown_event.is_set(): return
                with lock:
                    if my_token != start_token: return
                if is_server_ready(host, port):
                    notify("混元球", "服务已就绪 ✅", cfg)
                    if cfg.get("open_webui_on_ready", False):
                        open_webui()
                    return
                time.sleep(1.0)
        threading.Thread(target=late_ready, daemon=True).start()
        return

    set_state(STATE_STARTING)
    notify("混元球", "正在载入模型…", cfg)
    append_launcher_log("Starting llama-server...")

    try:
        out = open(server_log_path(), "a", encoding="utf-8", buffering=1)
        out.write(f"\n===== START {now()} =====\n")
        proc = subprocess.Popen(args, cwd=BASE_DIR, stdout=out, stderr=out, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        set_state(STATE_ERROR)
        append_launcher_log(f"Popen failed: {e}")
        notify("混元球", "启动失败：无法创建进程", cfg)
        return

    def wait_ready():
        try:
            stage1_deadline = time.time() + 30.0
            while time.time() < stage1_deadline:
                if shutdown_event.is_set(): return
                with lock:
                    if my_token != start_token: return
                if not is_running_process():
                    set_state(STATE_ERROR)
                    notify("混元球", "启动失败：进程退出", cfg)
                    return
                if is_port_open(host, port):
                    set_state(STATE_RUNNING)
                    break
                time.sleep(0.5)
            else:
                set_state(STATE_ERROR)
                notify("混元球", "启动超时：端口无响应", cfg)
                return

            stage2_deadline = time.time() + 300.0
            while time.time() < stage2_deadline:
                if shutdown_event.is_set(): return
                with lock:
                    if my_token != start_token: return
                if not is_running_process():
                    set_state(STATE_ERROR)
                    notify("混元球", "服务异常退出", cfg)
                    return

                if is_server_ready(host, port):
                    set_state(STATE_RUNNING)
                    notify("混元球", "模型载入完成，随时待命 ✅", cfg)
                    if cfg.get("open_webui_on_ready", False):
                        open_webui()
                    return
                time.sleep(1.0)

            set_state(STATE_RUNNING)
            notify("混元球", "启动完成（API 检测超时，请手动测试）", cfg)
            
        except Exception as e:
            append_launcher_log(f"Critical error in wait_ready: {e}")

    threading.Thread(target=wait_ready, daemon=True).start()

def stop_server(_=None):
    global proc, start_token
    if not can_stop(): return
    with lock: start_token += 1

    cfg = load_config()
    notify("混元球", "正在停止服务…", cfg)
    
    with lock:
        p = proc
        proc = None

    if p and p.poll() is None:
        try:
            p.terminate()
            p.wait(timeout=3)
        except:
            try: p.kill()
            except: pass

    set_state(STATE_STOPPED)
    notify("混元球", "服务已停止", cfg)
    append_launcher_log("STOPPED")

def quit_app(icon, _=None):
    shutdown_event.set()
    try: stop_server()
    except: pass
    try: icon.stop()
    except: pass

def make_icon():
    icon_path = os.path.join(BASE_DIR, "icon.ico")
    return Image.open(icon_path) if os.path.exists(icon_path) else Image.new('RGB', (64, 64), 'blue')

def main():
    global tray_icon
    cleanup_old_logs(LOG_DIR, LOG_RETENTION_DAYS)
    cleanup_old_mei_dirs()

    menu = pystray.Menu(
        item("开启 API", start_server, enabled=lambda _: can_start()),
        item("关闭 API", stop_server, enabled=lambda _: can_stop()),
        pystray.Menu.SEPARATOR,
        item("打开翻译界面", open_webui),
        item("打开日志文件夹", open_logs),
        pystray.Menu.SEPARATOR,
        item("关 于", about),
        item("退 出", lambda icon: quit_app(icon)),
    )

    tray_icon = pystray.Icon("hy-mt", make_icon(), "HY-MT API", menu)
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), 0x4000)
    except: pass
    
    _update_title_for_state(get_state())

    try:
        cfg = load_config()
        if cfg.get("autostart", False):
            # 关键修改：延时改为 2.0 秒，确保图标就绪后再发通知
            threading.Thread(target=lambda: (time.sleep(2.0), start_server()), daemon=True).start()
    except: pass

    tray_icon.run()

if __name__ == "__main__":
    main()