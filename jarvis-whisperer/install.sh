#!/bin/bash
# Jarvis Whisperer – Installationsscript (Linux)
set -e

echo "=== Jarvis Whisperer – Installation ==="

# Systemabhängigkeiten
echo "[1/4] Systempakete prüfen..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    xclip \
    libxcb1 \
    libxcb-xinerama0 \
    python3-dev \
    ffmpeg

# Virtuelle Umgebung
echo "[2/4] Python-Umgebung erstellen..."
python3 -m venv venv
source venv/bin/activate

# Python-Pakete
echo "[3/4] Python-Pakete installieren..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Autostart (optional)
echo "[4/4] Autostart einrichten..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat > "$AUTOSTART_DIR/jarvis-whisperer.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Jarvis Whisperer
Comment=Lokales Diktierprogramm
Exec=$SCRIPT_DIR/start.sh
Icon=$SCRIPT_DIR/assets/icon.png
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo ""
echo "=== Installation abgeschlossen! ==="
echo ""
echo "Starten mit:  ./start.sh"
echo "Oder direkt:  source venv/bin/activate && python main.py"
echo ""
echo "Mittelmaus drücken = Aufnahme starten"
echo "Mittelmaus nochmal = stoppen + Text in Zwischenablage"
