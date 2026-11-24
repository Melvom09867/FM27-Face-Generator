@echo off
REM Baut den FM27 Face Generator lokal unter Windows (Python 3.10+ muss installiert sein).
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m fm27facegen.icon build\icon.ico
python tools\version_info.py build\version.txt
python -m PyInstaller --noconfirm --onedir --windowed --name FM27-FaceGenerator --icon build\icon.ico --version-file build\version.txt --collect-data cv2 --collect-all tkinterdnd2 --collect-all send2trash run.py
echo.
echo Fertig: dist\FM27-FaceGenerator\FM27-FaceGenerator.exe (ganzen Ordner weitergeben)
pause
