@echo off
.\venv\py311-cli\Scripts\python.exe -m nuitka --onefile --remove-output --output-dir=..\ThreadDownloader.Releases\ --show-progress --windows-icon-from-ico=.\icon.ico .\downloader.py