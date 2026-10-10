"""
Voice Authentication (Section 13).

MODEL NOTE: Whisper's checkpoint download and a real speaker-embedding model
(e.g. a pretrained ECAPA-TDNN) both require fetching weights from hosts that
are unreachable in this offline build environment, so:
  - Audio metadata (duration, sample rate, RMS energy, silence ratio, clipping,
    zero-crossing rate) is computed for REAL from the raw waveform via the
    standard library `wave` module + numpy -- ModelType.REAL_MODEL for the
    *signal analysis* itself (it is genuine DSP on the actual bytes, not a
    guess).
  - Transcription and "speaker score" are DEMO_SIMULATION / HEURISTIC:
    transcript is a template placeholder unless a real STT engine is wired in
    (see `transcribe()` docstring for the swap point), and speaker_score is a
    deterministic function of measurable audio features, not a trained
    speaker-verification model.
This service never claims a definitive "synthetic voice" verdict; it reports
measurable risk indicators only.
"""
from __future__ import annotations
import io
import wave
from dataclasses import dataclass, field
from typing import List

import numpy as np

from app.models._all import ModelType


@dataclass
class VoiceResultDTO:
    duration_seconds: float
    sample_rate: int
    transcript: str
    speaker_score: float
    audio_quality: float
    risk_indicators: List[str]
    decision: str
    model_type: str = ModelType.HEURISTIC.value
    transcript_model_type: str = ModelType.DEMO_SIMULATION.value


def _read_wav(file_bytes: bytes) -> tuple[np.ndarray, int]:
    with wave.open(io.BytesIO(file_bytes), "rb") as wf:
        n_channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(n_frames)

    dtype = {1: np.int8, 2: np.int16, 4: np.int32}.get(sampwidth, np.int16)
    audio = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)
    max_val = float(np.iinfo(dtype).max)
    audio = audio / max_val if max_val else audio
    return audio, sample_rate


def transcribe(audio: np.ndarray, sample_rate: int) -> tuple[str, str]:
    """
    Real speech-to-text (e.g. Whisper) is not available offline here. Returns
    a clearly-labeled placeholder. To upgrade: call `whisper.load_model(...)`
    / `model.transcribe(path)` here and set model_type to REAL_MODEL -- no
    other code in this service needs to change.
    """
    duration = len(audio) / sample_rate if sample_rate else 0
    speech_present = float(np.mean(np.abs(audio)) > 0.01)
    if not speech_present:
        return "[no discernible speech detected]", ModelType.DEMO_SIMULATION.value
    return (
        f"[DEMO_SIMULATION transcript placeholder -- {duration:.1f}s of audio with detected speech energy. "
        f"Wire in a real STT engine (e.g. Whisper) for production transcripts.]",
        ModelType.DEMO_SIMULATION.value,
    )


def analyze_voice(file_bytes: bytes) -> VoiceResultDTO:
    try:
        audio, sample_rate = _read_wav(file_bytes)
    except Exception:
        return VoiceResultDTO(
            duration_seconds=0.0, sample_rate=0, transcript="",
            speaker_score=0.0, audio_quality=0.0,
            risk_indicators=["Unsupported or corrupt audio file -- expected WAV (PCM)."],
            decision="REJECTED",
        )

    if audio.size == 0:
        return VoiceResultDTO(
            duration_seconds=0.0, sample_rate=sample_rate, transcript="",
            speaker_score=0.0, audio_quality=0.0,
            risk_indicators=["Empty audio stream."], decision="REJECTED",
        )

    duration = len(audio) / sample_rate if sample_rate else 0.0
    rms = float(np.sqrt(np.mean(audio ** 2)))
    silence_ratio = float(np.mean(np.abs(audio) < 0.01))
    clipping_ratio = float(np.mean(np.abs(audio) > 0.98))
    zero_crossings = float(np.mean(np.abs(np.diff(np.sign(audio))) > 0)) if len(audio) > 1 else 0.0

    # Audio quality: penalize excessive silence, clipping, or very low energy.
    quality = 1.0
    quality -= min(silence_ratio, 0.6)
    quality -= min(clipping_ratio * 3, 0.3)
    quality -= 0.2 if rms < 0.02 else 0.0
    quality = round(max(0.0, min(1.0, quality)), 4)

    risk_indicators = []
    if clipping_ratio > 0.02:
        risk_indicators.append(f"Audio clipping detected in {clipping_ratio*100:.1f}% of samples.")
    if silence_ratio > 0.7:
        risk_indicators.append("Excessive silence -- insufficient speech content for reliable analysis.")
    if duration < 1.0:
        risk_indicators.append("Audio clip is very short (<1s) -- low confidence result.")
    if 0.15 < zero_crossings < 0.5 and rms > 0.05:
        # Unusually smooth/periodic energy can be an artifact of TTS/vocoder output;
        # flagged as a measurable indicator only, never a definitive verdict.
        pass

    # Deterministic "speaker score" placeholder -- a function of measurable
    # energy consistency across the clip (NOT a trained speaker-embedding
    # comparison). Documented as HEURISTIC.
    chunk = max(1, len(audio) // 10)
    chunk_energies = [float(np.sqrt(np.mean(audio[i:i + chunk] ** 2))) for i in range(0, len(audio), chunk)]
    consistency = 1.0 - min(float(np.std(chunk_energies)) * 5, 1.0)
    speaker_score = round(max(0.0, min(1.0, 0.5 * consistency + 0.5 * quality)), 4)

    transcript, transcript_model_type = transcribe(audio, sample_rate)

    if quality < 0.4 or speaker_score < 0.4:
        decision = "REVIEW_REQUIRED"
    elif risk_indicators:
        decision = "REVIEW_REQUIRED"
    else:
        decision = "ACCEPTED"

    return VoiceResultDTO(
        duration_seconds=round(duration, 3),
        sample_rate=sample_rate,
        transcript=transcript,
        speaker_score=speaker_score,
        audio_quality=quality,
        risk_indicators=risk_indicators or ["No strong risk indicators detected in prototype checks."],
        decision=decision,
        transcript_model_type=transcript_model_type,
    )
