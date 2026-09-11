# Jarvis Whisperer

Lokales Diktierprogramm – kein Abo, kein Internet, alles auf deinem PC.  
Basiert auf OpenAIs Whisper-Modell (open source).

## Was es macht

- Mittelmaus drücken → Aufnahme startet
- Mittelmaus nochmal → Aufnahme stoppt, Text wird transkribiert
- Text landet sofort in der **Zwischenablage** → Ctrl+V irgendwo einfügen
- **Flüstermodus**: Erkennt auch leise Sprache (nachts, ohne andere zu wecken)
- Systray-Icon mit Equalizer-Animation (türkis = bereit, rot = nimmt auf)
- Spracherkkennung: **Deutsch + Englisch** automatisch

## Installation

```bash
cd jarvis-whisperer
chmod +x install.sh start.sh
./install.sh
```

## Starten

```bash
./start.sh
```

Oder als Autostart: Die Installation richtet das automatisch ein.

## Modelle

In `main.py` Zeile `WHISPER_MODEL` anpassen:

| Modell | Größe | Qualität | Geschwindigkeit |
|--------|-------|----------|-----------------|
| `tiny` | 75 MB | ausreichend | sehr schnell |
| `base` | 145 MB | gut | schnell ← Standard |
| `small` | 466 MB | sehr gut | mittel |
| `medium` | 1.5 GB | exzellent | langsam |

## GPU-Beschleunigung

Falls du eine NVIDIA-GPU hast, in `main.py`:
```python
WHISPER_DEVICE = "cuda"
```
Dann läuft die Transkription in Sekunden statt ~10s.

## Troubleshooting

**Kein Audio:** `sudo apt install portaudio19-dev` → neu installieren  
**Kein Clipboard:** `sudo apt install xclip`  
**Pynput-Fehler:** `sudo apt install python3-dev`
