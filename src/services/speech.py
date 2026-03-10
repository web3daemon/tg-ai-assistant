import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from src.config import settings

logger = logging.getLogger(__name__)


class SpeechToTextError(Exception):
    pass


@dataclass(slots=True)
class TranscribedAudio:
    source_name: str
    transcript: str
    user_text: str
    duration_seconds: int | None = None

    @property
    def log_content(self) -> str:
        base = f"[voice] {self.source_name}"
        if self.duration_seconds is not None:
            base += f" ({self.duration_seconds}s)"
        if self.user_text:
            base += f"\nКомментарий: {self.user_text}"
        base += f"\nРасшифровка:\n{self.transcript}"
        return base

    @property
    def model_text(self) -> str:
        if self.user_text:
            return f"{self.user_text}\n\nТекст голосового сообщения:\n{self.transcript}"
        return f"Пользователь отправил голосовое сообщение. Текст расшифровки:\n{self.transcript}"


class SpeechToTextService:
    def __init__(self) -> None:
        self._model: WhisperModel | None = None

    def transcribe(
        self,
        file_name: str,
        data: bytes,
        user_text: str = "",
        duration_seconds: int | None = None,
    ) -> TranscribedAudio:
        if duration_seconds and duration_seconds > settings.max_audio_duration_seconds:
            raise SpeechToTextError(
                f"Голосовое слишком длинное. Лимит: {settings.max_audio_duration_seconds} секунд."
            )

        suffix = Path(file_name).suffix or ".ogg"
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(data)
                temp_path = Path(temp_file.name)

            transcript = self._transcribe_with_fallback(temp_path)
        except Exception as exc:
            logger.exception("Speech-to-text failed")
            raise SpeechToTextError("Не удалось распознать голосовое сообщение.") from exc
        finally:
            if "temp_path" in locals():
                temp_path.unlink(missing_ok=True)

        if not transcript:
            raise SpeechToTextError("Не удалось распознать речь в голосовом сообщении.")

        return TranscribedAudio(
            source_name=file_name,
            transcript=transcript,
            user_text=user_text,
            duration_seconds=duration_seconds,
        )

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            self._model = self._load_model(
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )
        return self._model

    def _transcribe_with_fallback(self, temp_path: Path) -> str:
        model = self._get_model()
        try:
            segments, _info = model.transcribe(
                str(temp_path),
                vad_filter=True,
                beam_size=1,
            )
            return " ".join(segment.text.strip() for segment in segments).strip()
        except RuntimeError as exc:
            if not self._is_cuda_runtime_error(exc):
                raise

            logger.warning("CUDA runtime is unavailable for Whisper, falling back to CPU")
            self._model = self._load_model(device="cpu", compute_type="int8")
            segments, _info = self._model.transcribe(
                str(temp_path),
                vad_filter=True,
                beam_size=1,
            )
            return " ".join(segment.text.strip() for segment in segments).strip()

    def _load_model(self, device: str, compute_type: str) -> WhisperModel:
        logger.info(
            "Loading Whisper model | size=%s device=%s compute_type=%s",
            settings.whisper_model_size,
            device,
            compute_type,
        )
        return WhisperModel(
            settings.whisper_model_size,
            device=device,
            compute_type=compute_type,
        )

    @staticmethod
    def _is_cuda_runtime_error(exc: RuntimeError) -> bool:
        message = str(exc).lower()
        return "cublas" in message or "cudnn" in message or "cuda" in message
