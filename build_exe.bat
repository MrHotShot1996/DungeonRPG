@echo off
rem Rebuilds dist\EchoesOfTheBoneKing.exe from the game files in this folder.
rem Close the game first if it is running, then double-click this file.
cd /d "%~dp0"
echo Building the exe, this takes a minute or two...
python -m PyInstaller --noconfirm EchoesOfTheBoneKing.spec
if errorlevel 1 py -m PyInstaller --noconfirm EchoesOfTheBoneKing.spec
if errorlevel 1 (
  echo.
  echo BUILD FAILED - read the messages above.
) else (
  echo.
  echo DONE - the new exe is in the dist folder.
)
pause
