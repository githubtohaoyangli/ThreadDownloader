@echo off
.\venv\py311-cli\Scripts\python.exe -m nuitka --onefile --remove-output --output-dir=..\ThreadDownloader.Releases\ --show-progress --windows-icon-from-ico=.\icon.ico .\downloader.py
signtool sign /f C:\Users\Piggeon\piggeon.pfx /p xiezichen! /fd sha256 /t http://timestamp.comodoca.com /v C:\Users\Piggeon\PycharmProjects\ThreadDownloader.Releases\downloader.exe
rem .\venv\py311-gui\Scripts\python.exe -m nuitka --onefile --remove-output --output-dir=..\ThreadDownloader.Releases\ --show-progress --windows-icon-from-ico=.\icon.ico .\downloader.GUI.py