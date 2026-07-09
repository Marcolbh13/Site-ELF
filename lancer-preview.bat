@echo off
rem Lance le site en localhost sur Windows puis ouvre Chrome
cd /d "%~dp0"
where py >nul 2>nul && (start http://localhost:8000/ & py -m http.server 8000 & goto :eof)
where python >nul 2>nul && (start http://localhost:8000/ & python -m http.server 8000 & goto :eof)
where npx >nul 2>nul && (start http://localhost:8000/ & npx --yes serve -l 8000 . & goto :eof)
echo Installez Python (python.org) ou Node.js (nodejs.org) puis relancez ce script.
pause
