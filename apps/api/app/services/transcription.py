from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status

from app.config import Settings
from app.domain.entities import RawEntry, TranscriptSegment
from app.providers.interfaces import STTProvider, TranscriptResult
from app.providers.local_stt import WhisperCppSTTProvider
from app.providers.stubs import LocalStubSTTProvider
from app.repositories.interfaces import ActivityEventRepository, RawEntryRepository, TranscriptSegmentRepository
from app.services.activity import log_activity
from app.services.common import generate_id, utcnow
from app.services.local_models import resolve_whisper_cpp_paths


def _pick_file_extension(file_name: str | None, content_type: str | None) -> str:
    if file_name and "." in file_name:
        return "." + file_name.rsplit(".", maxsplit=1)[-1].lower()
    if content_type == "audio/webm":
        return ".webm"
    if content_type == "audio/wav":
        return ".wav"
    if content_type == "audio/mpeg":
        return ".mp3"
    return ".webm"


def _audio_path_for_entry(settings: Settings, entry_id: str, file_name: str | None, content_type: str | None) -> Path:
    audio_dir = Path(settings.audio_storage_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    return audio_dir / f"{entry_id}{_pick_file_extension(file_name, content_type)}"


def build_stt_provider(settings: Settings) -> tuple[STTProvider, bool]:
    if settings.stt_provider == "local_stub":
        return LocalStubSTTProvider(), True
    executable_path, model_path = resolve_whisper_cpp_paths(settings)
    if settings.stt_provider == "whisper_cpp" and executable_path and model_path:
        provider = WhisperCppSTTProvider(executable_path, model_path)
        if provider.is_available:
            return provider, False
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Local transcription is not configured yet. Add a whisper.cpp executable and model path in Settings, or switch STT provider to local_stub for testing.",
    )


def _normalize_segments(entry_id: str, transcript: TranscriptResult) -> list[TranscriptSegment]:
    if transcript.segments:
        return [
            TranscriptSegment(
                id=generate_id(),
                raw_entry_id=entry_id,
                segment_index=segment.segment_index,
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                text=segment.text,
                speaker_label=segment.speaker_label,
            )
            for segment in transcript.segments
        ]
    return [
        TranscriptSegment(
            id=generate_id(),
            raw_entry_id=entry_id,
            segment_index=0,
            start_ms=None,
            end_ms=None,
            text=transcript.text,
            speaker_label=None,
        )
    ]


def transcribe_audio_entry(
    entry_id: str,
    *,
    audio_bytes: bytes,
    file_name: str | None,
    content_type: str | None,
    settings: Settings,
    raw_entries: RawEntryRepository,
    transcript_segments: TranscriptSegmentRepository,
    activity_events: ActivityEventRepository,
) -> tuple[RawEntry, list[TranscriptSegment]]:
    entry = raw_entries.get(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw entry not found.")
    if entry.source_type != "audio_transcript":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only audio-backed entries can be transcribed.")
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio upload was empty.")

    audio_path = _audio_path_for_entry(settings, entry.id, file_name, content_type)
    audio_path.write_bytes(audio_bytes)
    entry.audio_file_ref = str(audio_path)
    entry.updated_at = utcnow()
    raw_entries.update(entry)

    provider, used_fallback = build_stt_provider(settings)
    log_activity(
        activity_events,
        event_type="transcription_started",
        entity_type="raw_entry",
        entity_id=entry.id,
        metadata={
            "audio_file_ref": entry.audio_file_ref,
            "provider_name": provider.name,
            "used_fallback": used_fallback,
        },
        device_id=entry.device_id,
    )

    try:
        transcript = provider.transcribe(
            entry.audio_file_ref,
            options={"content_type": content_type, "file_name": file_name},
        )
    except Exception as exc:  # noqa: BLE001
        log_activity(
            activity_events,
            event_type="transcription_failed",
            entity_type="raw_entry",
            entity_id=entry.id,
            metadata={"provider_name": provider.name, "error": str(exc)},
            device_id=entry.device_id,
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Transcription failed: {exc}") from exc

    entry.raw_text = transcript.text.strip()
    entry.entry_status = "transcribed"
    entry.updated_at = utcnow()
    entry.transcript_provider_name = transcript.provider_name or provider.name
    entry.transcript_model_name = transcript.model_name or settings.stt_model
    entry.transcript_metadata = {
        **transcript.metadata,
        "file_name": file_name,
        "content_type": content_type,
        "audio_bytes": len(audio_bytes),
        "used_fallback": used_fallback,
    }
    updated_entry = raw_entries.update(entry)
    saved_segments = transcript_segments.replace_for_entry(entry.id, _normalize_segments(entry.id, transcript))

    log_activity(
        activity_events,
        event_type="transcription_completed",
        entity_type="raw_entry",
        entity_id=entry.id,
        metadata={
            "provider_name": updated_entry.transcript_provider_name,
            "model_name": updated_entry.transcript_model_name,
            "segment_count": len(saved_segments),
        },
        device_id=entry.device_id,
    )
    return updated_entry, saved_segments
