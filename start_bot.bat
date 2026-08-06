@echo off
cd C:\Users\smipp\.gemini\antigravity\scratch\telegram_bot
git fetch origin
git reset --hard origin/main
C:\Users\smipp\AppData\Local\Programs\Python\Python311\python.exe C:\Users\smipp\.gemini\antigravity\scratch\telegram_bot\pc_bot.py > C:\Users\smipp\.gemini\antigravity\scratch\telegram_bot\start_bot_debug.txt 2>&1
