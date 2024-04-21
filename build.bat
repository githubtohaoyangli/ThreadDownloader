@echo off
.\.venv\Scripts\python.exe -m nuitka --onefile --remove-output --output-dir=..\ThreadDownloader.Releases\ --show-progress --windows-icon-from-ico=.\icon.ico .\downloader.py