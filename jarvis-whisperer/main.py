#!/usr/bin/env python3
"""
Jarvis Whisperer – Lokales Diktierprogramm
Mittelmaus drücken = Aufnahme starten/stoppen
Text landet automatisch in der Zwischenablage
"""

import sys
import threading
import queue
import time
import logging
import numpy as np
import sounddevice as sd
import pyperclip
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem
from pynput.mouse import Button, Listener as MouseListener

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("JarvisWhisperer")

# ──────────────────────────────────────────────
# Konfiguration
# ──────────────────────────────────────────────
SAMPLE_RATE = 16000          # Whisper erwartet 16 kHz
CHANNELS = 1
DTYPE = "float32"
WHISPER_MODEL = "tiny"       # tiny/base/small/medium – tiny = schnell, 75 MB
WHISPER_DEVICE = "cpu"       # "cuda" wenn GPU vorhanden
LANGUAGE = None              # None = automatisch (Deutsch + Englisch erkannt)

# Flüstermodus: Audioamplitude um diesen Faktor verstärken
WHISPER_BOOST = 4.0          # lauter machen ohne Hintergrundlärm zu verstärken

# ──────────────────────────────────────────────
# Globaler Zustand
# ──────────────────────────────────────────────
recording = False
audio_chunks = []
audio_lock = threading.Lock()
model = None
model_lock = threading.Lock()
tray_icon = None
status_queue = queue.Queue()  # "idle" | "recording" | "processing"

# ──────────────────────────────────────────────
# Whisper laden (beim ersten Start)
# ──────────────────────────────────────────────
def load_model():
    global model
    with model_lock:
        if model is None:
            log.info("Lade Whisper-Modell '%s'...", WHISPER_MODEL)
            from faster_whisper import WhisperModel
            model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type="int8")
            log.info("Modell geladen.")


# ──────────────────────────────────────────────
# Icon-Generierung (Equalizer-Animation)
# ──────────────────────────────────────────────
EQ_FRAMES: list[Image.Image] = []

def _build_eq_frames(size=64, frames=8, color_idle=(0, 200, 255), color_rec=(255, 80, 80)):
    """Erzeugt animierte Equalizer-Frames als PIL-Images."""
    images = []
    bars = 5
    bar_w = size // (bars * 2)
    max_h = size - 8

    for f in range(frames):
        img = Image.new("RGBA", (size, size), (20, 20, 30, 255))
        draw = ImageDraw.Draw(img)
        for b in range(bars):
            phase = (f + b * 2) % frames
            h = int(max_h * (0.3 + 0.7 * abs(np.sin(phase / frames * np.pi))))
            x0 = 4 + b * (bar_w * 2)
            y0 = size - 4 - h
            x1 = x0 + bar_w
            y1 = size - 4
            draw.rectangle([x0, y0, x1, y1], fill=color_idle)
        images.append(img)

    rec_images = []
    for f in range(frames):
        img = Image.new("RGBA", (size, size), (20, 20, 30, 255))
        draw = ImageDraw.Draw(img)
        for b in range(bars):
            phase = (f + b * 2) % frames
            h = int(max_h * (0.3 + 0.7 * abs(np.sin(phase / frames * np.pi))))
            x0 = 4 + b * (bar_w * 2)
            y0 = size - 4 - h
            x1 = x0 + bar_w
            y1 = size - 4
            draw.rectangle([x0, y0, x1, y1], fill=color_rec)
        rec_images.append(img)

    return images, rec_images


IDLE_FRAMES, REC_FRAMES = _build_eq_frames()


def get_icon_image(state: str, frame: int = 0) -> Image.Image:
    if state == "recording":
        return REC_FRAMES[frame % len(REC_FRAMES)]
    if state == "processing":
        # Blaue Pulse-Animation
        img = Image.new("RGBA", (64, 64), (20, 20, 30, 255))
        draw = ImageDraw.Draw(img)
        r = 20 + (frame % 6) * 2
        draw.ellipse([32 - r, 32 - r, 32 + r, 32 + r], outline=(100, 100, 255, 200), width=3)
        return img
    return IDLE_FRAMES[frame % len(IDLE_FRAMES)]


# ──────────────────────────────────────────────
# Aufnahme
# ──────────────────────────────────────────────
def audio_callback(indata, frames, time_info, status):
    if recording:
        with audio_lock:
            audio_chunks.append(indata.copy())


def start_recording():
    global recording, audio_chunks
    with audio_lock:
        audio_chunks = []
    recording = True
    status_queue.put("recording")
    log.info("Aufnahme gestartet")


def stop_and_transcribe():
    global recording
    recording = False
    status_queue.put("processing")
    log.info("Aufnahme gestoppt – transkribiere...")

    with audio_lock:
        chunks = list(audio_chunks)

    if not chunks:
        log.warning("Keine Audiodaten aufgenommen")
        status_queue.put("idle")
        return

    audio = np.concatenate(chunks, axis=0).flatten().astype(np.float32)

    # Flüstermodus: leise Stimme verstärken
    peak = np.abs(audio).max()
    if peak < 0.1:
        audio = audio * WHISPER_BOOST
        log.info("Flüstermodus aktiv – Signal um %.1fx verstärkt", WHISPER_BOOST)

    threading.Thread(target=_transcribe, args=(audio,), daemon=True).start()


def _transcribe(audio: np.ndarray):
    with model_lock:
        segments, info = model.transcribe(
            audio,
            language=LANGUAGE,
            beam_size=5,
            vad_filter=True,               # entfernt Stille automatisch
            vad_parameters={"min_silence_duration_ms": 300},
        )
        text = " ".join(s.text.strip() for s in segments).strip()

    if text:
        pyperclip.copy(text)
        log.info("Transkription: %s", text)
        log.info("→ In Zwischenablage kopiert")
    else:
        log.warning("Kein Text erkannt")

    status_queue.put("idle")


# ──────────────────────────────────────────────
# Maus-Listener (Mittelmaus)
# ──────────────────────────────────────────────
def on_click(x, y, button, pressed):
    if button == Button.middle and pressed:
        if not recording:
            start_recording()
        else:
            stop_and_transcribe()


def run_mouse_listener():
    with MouseListener(on_click=on_click) as listener:
        listener.join()


# ──────────────────────────────────────────────
# Systray
# ──────────────────────────────────────────────
def setup_tray():
    global tray_icon

    def on_quit(icon, item):
        icon.stop()
        sys.exit(0)

    def on_toggle(icon, item):
        if not recording:
            start_recording()
        else:
            stop_and_transcribe()

    menu = Menu(
        MenuItem("Aufnahme starten/stoppen", on_toggle),
        MenuItem("Beenden", on_quit),
    )

    tray_icon = Icon("JarvisWhisperer", get_icon_image("idle"), "Jarvis Whisperer", menu)

    def animate():
        frame = 0
        current_state = "idle"
        while True:
            try:
                new_state = status_queue.get_nowait()
                current_state = new_state
            except queue.Empty:
                pass

            tray_icon.icon = get_icon_image(current_state, frame)
            frame += 1
            time.sleep(0.1)

    threading.Thread(target=animate, daemon=True).start()
    tray_icon.run()


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    log.info("Jarvis Whisperer startet...")

    # Modell im Hintergrund vorladen
    threading.Thread(target=load_model, daemon=True).start()

    # Audiostrom dauerhaft offen halten
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        callback=audio_callback,
        blocksize=1024,
    )
    stream.start()

    # Maus-Listener starten
    threading.Thread(target=run_mouse_listener, daemon=True).start()

    log.info("Bereit. Mittelmaus drücken = Aufnahme starten/stoppen")
    log.info("Text wird in Zwischenablage kopiert")

    # Systray blockiert bis Beenden
    setup_tray()

    stream.stop()
    stream.close()


if __name__ == "__main__":
    main()
