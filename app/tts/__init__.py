"""TTS module for Romanian speech synthesis and text normalization.
Ref: docs/TASKS-WAVE2.md A8 & docs/CONTRACTS-WAVE2.md
"""
from app.tts.engine import synthesize_speech
from app.tts.normalize_ro import normalize_ro_speech, number_to_words_ro

__all__ = ["normalize_ro_speech", "number_to_words_ro", "synthesize_speech"]

