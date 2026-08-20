"""
Stage 5: MicrophoneSelector — smart auto-selection between Bluetooth
headset mic and system microphone.

Priority order (highest to lowest):
  1. Bluetooth / wireless headset microphone (if connected)
  2. Wired headset microphone
  3. System default microphone

Re-scans device list on every call to get_best_device() so it reacts
automatically when earbuds are connected or disconnected without
requiring a JARVIS restart.
"""
import logging
from typing import Optional, Tuple

logger = logging.getLogger("backend.voice.mic_selector")

# Keywords that indicate a Bluetooth or headset microphone (case-insensitive)
_BT_KEYWORDS = [
    "bluetooth", "btha2dp", "a2dp", "wireless",
    "headset", "headphone", "earphone", "earbud", "airpods",
    "buds", "zenith", "nirvana", "jabra", "sony", "bose",
    "samsung", "galaxy", "beats", "anker", "soundcore",
    "jbl", "sennheiser", "plantronics", "poly", "logitech",
]

_SYSTEM_KEYWORDS = [
    "sound mapper", "primary sound", "array", "realtek",
    "intel", "conexant", "cirrus", "microphone ("
]


def _get_all_input_devices() -> list:
    """Return list of (device_index, device_info) for all input-capable devices."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        return [
            (i, d) for i, d in enumerate(devices)
            if d.get("max_input_channels", 0) > 0
        ]
    except Exception as exc:
        logger.warning(f"[MIC] Could not query devices: {exc}")
        return []


def _score_device(name: str) -> int:
    """
    Score a device by desirability:
      100 = Bluetooth/wireless headset (highest priority)
       50 = Wired headset or generic headphone
        0 = System microphone / array (fallback)
      -10 = Stereo mix / loopback (avoid)
    """
    name_lower = name.lower()

    if "stereo mix" in name_lower or "loopback" in name_lower:
        return -10

    for kw in _BT_KEYWORDS:
        if kw in name_lower:
            return 100

    if "headset" in name_lower or "headphone" in name_lower:
        return 50

    return 0


def get_best_device() -> Tuple[Optional[int], str]:
    """
    Scan all available input devices and return the index + name of
    the best microphone to use right now.

    Returns:
        (device_index, device_name)
        device_index is None if no suitable device found (use system default).
    """
    devices = _get_all_input_devices()
    if not devices:
        return None, "No input devices found"

    best_idx = None
    best_score = -999
    best_name = "Unknown"

    for idx, info in devices:
        name = info.get("name", "")
        score = _score_device(name)
        if score > best_score:
            best_score = score
            best_idx = idx
            best_name = name

    if best_score < 0:
        # Only stereo-mix / loopback — return system default
        return None, "System Default"

    return best_idx, best_name
