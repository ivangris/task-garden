from __future__ import annotations

import subprocess
import shutil
from pathlib import Path

from app.providers.interfaces import STTProvider, TranscriptResult


class WhisperCppSTTProvider(STTProvider):
    name = "whisper_cpp"

    def __init__(self, executable_path: str, model_path: str) -> None:
        self.executable_path = Path(executable_path)
        self.model_path = Path(model_path)

    @property
    def is_available(self) -> bool:
        return self.executable_path.exists() and self.model_path.exists()

    def _prepare_audio(self, audio_path: Path) -> Path:
        if audio_path.suffix.lower() == ".wav":
            return audio_path

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError(
                "Browser recordings need ffmpeg before whisper.cpp can read them. Install ffmpeg or record/upload WAV audio."
            )

        converted_path = audio_path.with_suffix(".whisper.wav")
        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(audio_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(converted_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0 or not converted_path.exists():
            detail = (result.stderr or result.stdout or "ffmpeg audio conversion failed.").strip()
            raise RuntimeError(f"Audio conversion failed before transcription: {detail}")
        return converted_path

    def transcribe(self, audio_ref: str, options: dict | None = None) -> TranscriptResult:
        if not self.is_available:
            raise RuntimeError("whisper.cpp executable or model path is not configured.")

        audio_path = Path(audio_ref)
        whisper_audio_path = self._prepare_audio(audio_path)
        output_prefix = whisper_audio_path.with_suffix("")
        command = [
            str(self.executable_path),
            "-m",
            str(self.model_path),
            "-f",
            str(whisper_audio_path),
            "-otxt",
            "-of",
            str(output_prefix),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "whisper.cpp transcription failed.").strip())

        transcript_path = Path(f"{output_prefix}.txt")
        if not transcript_path.exists():
            detail = (result.stderr or result.stdout or "whisper.cpp did not produce a transcript file.").strip()
            raise RuntimeError(f"whisper.cpp did not produce a transcript file: {detail}")

        text = transcript_path.read_text(encoding="utf-8").strip()
        if not text:
            raise RuntimeError("whisper.cpp returned an empty transcript.")

        return TranscriptResult(
            text=text,
            provider_name=self.name,
            model_name=self.model_path.name,
            metadata={
                "audio_ref": str(audio_path),
                "transcribed_audio_ref": str(whisper_audio_path),
                "engine": "whisper.cpp",
                "stdout": result.stdout.strip(),
            },
        )
