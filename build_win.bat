@echo off
REM Build PixelBear Windows executable
setlocal

echo === Cleaning previous build ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo === Installing dependencies ===
pip install -r requirements.txt
pip install pyinstaller

echo === Building PixelBear.exe ===
pyinstaller pixelbear.spec --noconfirm

if exist dist\PixelBear.exe (
    echo.
    echo ===================================
    echo Build complete: dist\PixelBear.exe
    echo ===================================
) else (
    echo.
    echo BUILD FAILED
    exit /b 1
)
