@echo off
.\venv\py311-cli\Scripts\python.exe -m nuitka --onefile --remove-output --output-dir=..\ThreadDownloader.Releases\ --show-progress --windows-icon-from-ico=.\icon.ico .\downloader.py
pause
cls
.\venv\py311-gui\Scripts\python.exe -m nuitka --onefile --remove-output --output-dir=..\ThreadDownloader.Releases\ --show-progress --windows-icon-from-ico=.\icon.ico .\downloader.GUI.py