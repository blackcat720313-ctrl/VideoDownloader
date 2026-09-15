@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Installing/updating dependencies...
py -m pip install -U yt-dlp pyinstaller
if errorlevel 1 goto :error

echo [2/3] Building EXE...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name VideoDownloader video_downloader.py
if errorlevel 1 goto :error

echo [3/3] Copying FFmpeg folder...
if not exist "dist\ffmpeg" mkdir "dist\ffmpeg"
if exist "ffmpeg\ffmpeg.exe" copy /Y "ffmpeg\ffmpeg.exe" "dist\ffmpeg\ffmpeg.exe" >nul
if exist "ffmpeg\ffprobe.exe" copy /Y "ffmpeg\ffprobe.exe" "dist\ffmpeg\ffprobe.exe" >nul

echo.
echo Build complete: dist\VideoDownloader.exe
echo Put FFmpeg in dist\ffmpeg\ if it was not copied automatically.
pause
exit /b 0

:error
echo.
echo Build failed. Please read the error above.
pause
exit /b 1
