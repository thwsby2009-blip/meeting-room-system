"""
WSGI 入口檔案 — 給 PythonAnywhere 使用
把這個檔案的路徑設定到 PythonAnywhere 的 WSGI configuration file 即可。

PythonAnywhere 設定步驟：
1. 開 Web 頁 -> Add a new web app -> Manual Configuration -> Python 3.x
2. 在 "Code" 區塊：
   - Source code: /home/你的帳號/meeting-room-system/backend
   - Working directory: /home/你的帳號/meeting-room-system/backend
   - WSGI configuration file: /var/www/你的帳號_pythonanywhere_com_wsgi.py
3. 點開 WSGI configuration file 連結，用以下內容取代：
"""
import sys

# 把後端目錄加入 Python 路徑
path = '/home/thwsby/meeting-room-system/backend'
if path not in sys.path:
    sys.path.insert(0, path)

# 修正資料庫路徑（PythonAnywhere 的 SQLite 要用絕對路徑）
import os
os.environ['DATABASE_PATH'] = os.path.join(path, 'meeting_room.db')

from main import app

# PythonAnywhere 需要 application 這個變數名稱
application = app
