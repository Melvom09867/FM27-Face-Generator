@echo off
REM Baut die FM27-FaceGenerator.exe lokal unter Windows (Python 3.10+ muss installiert sein).
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name FM27-FaceGenerator --collect-data cv2 --collect-all tkinterdnd2 --collect-all send2trash run.py
echo.
echo Fertig: dist\FM27-FaceGenerator.exe
pause
