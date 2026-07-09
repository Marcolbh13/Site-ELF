#!/bin/sh
# Lance le site en localhost (Mac / Linux) puis ouvre le navigateur
cd "$(dirname "$0")"
(sleep 1; open http://localhost:8000/ 2>/dev/null || xdg-open http://localhost:8000/ 2>/dev/null) &
python3 -m http.server 8000
