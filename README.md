# Telegram PC Remote Control Bot

This project is a powerful Telegram bot that allows you to remotely control, monitor, and manage your Windows PC via Telegram.

## Technologies Used

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram API](https://img.shields.io/badge/Telegram_API-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Windows API](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)

## Features

- **Security & Spying:**
  - `/intruder` - Lock PC, snap webcam, record audio.
  - `/keylog [on/off]` - Silently record all keystrokes.
  - `/mic [seconds]` - Secretly record microphone audio.
  - `/bluetooth [name]` - Auto-lock PC if a specified Bluetooth device (like your phone) disconnects.
- **System & Hacking:**
  - `/type [text]` - Remotely type text on your PC.
  - `/key [keys]` - Execute keyboard shortcuts.
  - `/tasks` & `/kill [PID]` - Manage running processes.
  - `/livescreen [on/off]` - Receive screenshots every 5 seconds.
  - `/stream [on/off]` - Start a live video stream of your screen.
  - `/location` - Get exact hardware GPS location.
  - `/jiggle` - Anti-sleep mouse jiggler.
- **Files & Media:**
  - `/ls` & `/cd` - Interactive file explorer.
  - `/get [path]` - Download files from your PC to your phone.
  - `/open [app/url]` - Open applications or websites.
  - `/close [app]` - Close applications.
- **Media Controls:**
  - Play, pause, volume up/down, mute.
- **Other Basics:**
  - Screenshots, webcam capture, screen recording, system stats, PC lock, and restart.

## How to Implement This on Your System

### Prerequisites

1. **Python 3.8+** installed on your Windows PC.
2. A **Telegram Bot Token** (Create a new bot via [@BotFather](https://t.me/BotFather) on Telegram and copy the API Token).
3. **Your Telegram Username** (without the `@` symbol).

### Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone <your-repository-url>
   cd telegram_bot
   ```

2. **Install Dependencies:**
   Install the required Python packages. If a `requirements.txt` is available, you can run:
   ```bash
   pip install -r requirements.txt
   ```
   *If some dependencies fail, you can manually install the main ones:*
   ```bash
   pip install python-telegram-bot pyautogui opencv-python pynput psutil pyperclip pyttsx3 plyer httpx yt-dlp sounddevice soundfile keyboard Flask numpy winsdk
   ```

3. **Configure the Bot:**
   Open `pc_bot.py` in any text editor and update the following variables at the top of the file with your credentials:
   ```python
   # Your Bot Token from BotFather
   TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
   
   # Your exact Telegram username (without the @)
   ALLOWED_USERNAME = "your_telegram_username"  
   ```
   *Note: `ALLOWED_USERNAME` is an essential security measure that ensures ONLY YOU can control your PC.*

4. **Run the Bot:**
   Execute the script to start the bot:
   ```bash
   python pc_bot.py
   ```
   *(Optional: You can double-click `start_bot.bat` or `start_bot.vbs` to run it silently in the background if configured).*

5. **Start Controlling:**
   Open your Telegram app, search for your bot, and send `/start`. You'll receive a welcome message and a menu of all available commands!

## Disclaimer

This tool is intended for **personal use and educational purposes only**. Do not use it on systems you do not own or have explicit permission to manage. The authors are not responsible for any misuse.
