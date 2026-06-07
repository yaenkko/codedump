@echo off
REM Erzeugt PersonalWiki.exe (Windows). Vorher einmalig: pip install pyinstaller
REM Ergebnis liegt danach unter dist\PersonalWiki.exe

pyinstaller --onefile --windowed --name PersonalWiki run.py

echo.
echo Fertig. Die EXE liegt unter: dist\PersonalWiki.exe
pause
