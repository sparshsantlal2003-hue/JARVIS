"""
Stage 5: MicrophoneSelector — selects the best compatible audio input device.

Priority:
  1. WASAPI (best quality, native rate 48kHz, works reliably on Windows 10/11)
  2. MME Sound Mapper (follows Windows default device setting)
  3. Any other working input

The Bluetooth mic is handled automatically by Windows — simply set your
earbuds as the Default Recording Device in Windows Sound Settings and
JARVIS will use them automatically through the WASAPI or Sound Mapper.
"""
import logging
from typing import Optional, Tuple

logger = logging.getLogger("backend.voice.mic_selector")

# Native sample rates to try per host API
_HOSTAPI_RATES = {
    "Windows WASAPI": 48000,
    "MME": 16000,
    "Windows DirectSound": 44100,
}

_PREFERRED_HOSTAPI_ORDER = ["Windows WASAPI", "MME", "Windows DirectSound"]


def get_best_device() -> Tuple[Optional[int], str, int]:
    """
    Returns (device_index, device_name, sample_rate).
    Tries WASAPI first, then MME Sound Mapper, then anything that works.
    The caller should use the returned sample_rate when opening the stream.
    """
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        hostapis = [sd.query_hostapis(i) for i in range(len(sd.query_hostapis()))]

        candidates = []
        for i, d in enumerate(devices):
            if d.get("max_input_channels", 0) == 0:
                continue
            ha_name = hostapis[d["hostapi"]]["name"]
            if ha_name in _PREFERRED_HOSTAPI_ORDER:
                candidates.append((i, d["name"], ha_name))

        # Sort by preferred host API order
        def _sort_key(c):
            try:
                return _PREFERRED_HOSTAPI_ORDER.index(c[2])
            except ValueError:
                return 99

        candidates.sort(key=_sort_key)

        for idx, name, ha_name in candidates:
            rate = _HOSTAPI_RATES.get(ha_name, 48000)
            channels = 1 if ha_name != "Windows WASAPI" else 2
            try:
                # Quick open-close test to verify the device is actually usable
                with sd.InputStream(device=idx, samplerate=rate,
                                    channels=channels, dtype="int16",
                                    blocksize=int(rate * 0.1)):
                    pass
                logger.debug(f"[MIC] Selected device [{idx}] {name} via {ha_name} @ {rate}Hz")
                return idx, name, rate
            except Exception:
                continue

        # Ultimate fallback: system default (None = let sounddevice decide)
        logger.warning("[MIC] No tested device worked, using system default.")
        return None, "System Default", 16000

    except Exception as exc:
        logger.error(f"[MIC] Device query failed: {exc}")
        return None, "Unknown", 16000
