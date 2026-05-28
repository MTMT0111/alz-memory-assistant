"""Voice orchestration for the conversation MVP with structured diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
from time import perf_counter

from app.config import load_local_env_file

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional in some local environments
    OpenAI = None  # type: ignore[assignment]


LOGGER = logging.getLogger(__name__)

load_local_env_file()

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_TTS_MODEL = "gpt-4o-mini-tts"
DEFAULT_TTS_VOICE = "sage"
DEFAULT_TTS_FORMAT = "mp3"
MAX_AUDIO_FILE_BYTES = 25 * 1024 * 1024

SUPPORTED_AUDIO_TYPES = {
    "audio/flac",
    "audio/m4a",
    "audio/mp3",
    "audio/mp4",
    "audio/mpeg",
    "audio/mpga",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "video/mp4",
}

CONTENT_TYPE_TO_EXTENSION = {
    "audio/flac": ".flac",
    "audio/m4a": ".m4a",
    "audio/mp3": ".mp3",
    "audio/mp4": ".mp4",
    "audio/mpeg": ".mp3",
    "audio/mpga": ".mp3",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/webm": ".webm",
    "video/mp4": ".mp4",
}

SUPPORTED_AUDIO_EXTENSIONS = set(CONTENT_TYPE_TO_EXTENSION.values())

VOICE_API_KEY_MISSING = "VOICE_API_KEY_MISSING"
VOICE_AUDIO_EMPTY = "VOICE_AUDIO_EMPTY"
VOICE_AUDIO_TOO_LARGE = "VOICE_AUDIO_TOO_LARGE"
VOICE_ASR_FAILED = "VOICE_ASR_FAILED"
VOICE_TTS_FAILED = "VOICE_TTS_FAILED"
VOICE_PROVIDER_TIMEOUT = "VOICE_PROVIDER_TIMEOUT"
VOICE_UNSUPPORTED_FORMAT = "VOICE_UNSUPPORTED_FORMAT"
VOICE_UNKNOWN_ERROR = "VOICE_UNKNOWN_ERROR"


@dataclass(slots=True)
class VoiceConfig:
    """Resolved runtime configuration for the audio MVP."""

    api_key: str
    base_url: str
    transcribe_model: str
    tts_model: str
    tts_voice: str
    tts_format: str = DEFAULT_TTS_FORMAT


@dataclass(slots=True)
class VoiceTranscriptionResult:
    """Speech-to-text result returned to the route layer."""

    success: bool
    stage: str
    error_code: str | None
    error_message: str | None
    user_friendly_message: str
    latency_ms: int
    provider: str
    model: str
    fallback_used: bool
    text: str
    confidence: float | None = None


@dataclass(slots=True)
class VoiceSpeechResult:
    """Text-to-speech result returned to the route layer."""

    success: bool
    stage: str
    error_code: str | None
    error_message: str | None
    user_friendly_message: str
    latency_ms: int
    provider: str
    model: str
    fallback_used: bool
    voice: str
    audio_bytes: bytes
    media_type: str


class VoiceServiceError(RuntimeError):
    """Raised when the voice MVP cannot complete one step cleanly."""

    def __init__(
        self,
        *,
        stage: str,
        error_code: str,
        error_message: str,
        user_friendly_message: str,
        status_code: int = 400,
        latency_ms: int = 0,
        provider: str = "openai",
        model: str = "",
        fallback_used: bool = False,
        debug_message: str = "",
    ) -> None:
        super().__init__(user_friendly_message)
        self.stage = stage
        self.error_code = error_code
        self.error_message = error_message
        self.user_friendly_message = user_friendly_message
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.provider = provider
        self.model = model
        self.fallback_used = fallback_used
        self.debug_message = debug_message or error_message

    def to_payload(self) -> dict[str, object]:
        """Return a JSON-friendly error payload for route handlers."""
        return {
            "success": False,
            "stage": self.stage,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "user_friendly_message": self.user_friendly_message,
            "debug_message": self.debug_message,
            "latency_ms": self.latency_ms,
            "provider": self.provider,
            "model": self.model,
            "fallback_used": self.fallback_used,
        }


def _env_first(*keys: str) -> str:
    """Return the first non-empty environment value."""
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""


def _normalize_content_type(content_type: str) -> str:
    """Strip codec suffixes from browser-provided MIME types."""
    return str(content_type or "").split(";", 1)[0].strip().lower()


def _sanitize_filename(filename: str, content_type: str) -> str:
    """Keep an extension OpenAI accepts even when the browser omits one."""
    candidate = Path(str(filename or "recording")).name
    suffix = Path(candidate).suffix.lower()
    if suffix in SUPPORTED_AUDIO_EXTENSIONS:
        return candidate

    detected_suffix = CONTENT_TYPE_TO_EXTENSION.get(_normalize_content_type(content_type), ".webm")
    stem = Path(candidate).stem or "recording"
    return f"{stem}{detected_suffix}"


def _resolve_voice_config() -> VoiceConfig:
    """Read the independent audio config without touching the text provider path."""
    return VoiceConfig(
        api_key=_env_first("OPENAI_API_KEY"),
        base_url=_env_first("OPENAI_AUDIO_BASE_URL", "OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE_URL,
        transcribe_model=_env_first("OPENAI_AUDIO_TRANSCRIBE_MODEL") or DEFAULT_TRANSCRIBE_MODEL,
        tts_model=_env_first("OPENAI_AUDIO_TTS_MODEL") or DEFAULT_TTS_MODEL,
        tts_voice=_env_first("OPENAI_AUDIO_VOICE") or DEFAULT_TTS_VOICE,
    )


def _elapsed_ms(started_at: float) -> int:
    """Convert a perf-counter start timestamp into rounded milliseconds."""
    return max(0, int(round((perf_counter() - started_at) * 1000)))


def _exception_debug_message(error: Exception) -> str:
    """Build a compact debug message from one provider exception."""
    message = str(error).strip()
    return f"{type(error).__name__}: {message}" if message else type(error).__name__


def _is_timeout_error(error: Exception) -> bool:
    """Detect timeout-like provider failures without depending on one SDK type."""
    debug_message = _exception_debug_message(error).lower()
    return "timeout" in debug_message or "timed out" in debug_message


class OpenAIVoiceService:
    """A thin wrapper around OpenAI audio endpoints for this MVP."""

    provider_name = "openai"

    def _get_client(self, config: VoiceConfig, *, stage: str, started_at: float):
        """Build a client only when the SDK and credentials are available."""
        if not config.api_key:
            raise VoiceServiceError(
                stage=stage,
                error_code=VOICE_API_KEY_MISSING,
                error_message="OpenAI API key missing for voice service",
                user_friendly_message="语音能力还没有配置好，先继续文字聊天也可以。",
                status_code=503,
                latency_ms=_elapsed_ms(started_at),
                provider=self.provider_name,
                model=config.transcribe_model if stage == "transcribe" else config.tts_model,
            )
        if OpenAI is None:
            raise VoiceServiceError(
                stage=stage,
                error_code=VOICE_UNKNOWN_ERROR,
                error_message="OpenAI SDK unavailable for voice service",
                user_friendly_message="当前环境还没有可用的语音能力，先继续文字模式也可以。",
                status_code=503,
                latency_ms=_elapsed_ms(started_at),
                provider=self.provider_name,
                model=config.transcribe_model if stage == "transcribe" else config.tts_model,
            )
        return OpenAI(api_key=config.api_key, base_url=config.base_url)

    def transcribe_audio(
        self,
        *,
        filename: str,
        audio_bytes: bytes,
        content_type: str,
        language: str = "zh",
    ) -> VoiceTranscriptionResult:
        """Turn one uploaded recording into text."""
        started_at = perf_counter()
        clean_bytes = bytes(audio_bytes or b"")
        if not clean_bytes:
            raise VoiceServiceError(
                stage="transcribe",
                error_code=VOICE_AUDIO_EMPTY,
                error_message="Uploaded audio payload is empty",
                user_friendly_message="这次没有录到声音，可以再试一次。",
                status_code=400,
                latency_ms=_elapsed_ms(started_at),
                provider=self.provider_name,
                model=_resolve_voice_config().transcribe_model,
            )
        if len(clean_bytes) > MAX_AUDIO_FILE_BYTES:
            raise VoiceServiceError(
                stage="transcribe",
                error_code=VOICE_AUDIO_TOO_LARGE,
                error_message=f"Uploaded audio exceeds size limit of {MAX_AUDIO_FILE_BYTES} bytes",
                user_friendly_message="这段录音有点长，先试一段更短的话吧。",
                status_code=400,
                latency_ms=_elapsed_ms(started_at),
                provider=self.provider_name,
                model=_resolve_voice_config().transcribe_model,
            )

        normalized_type = _normalize_content_type(content_type)
        safe_filename = _sanitize_filename(filename, normalized_type)
        safe_suffix = Path(safe_filename).suffix.lower()
        config = _resolve_voice_config()
        if normalized_type and normalized_type not in SUPPORTED_AUDIO_TYPES and safe_suffix not in SUPPORTED_AUDIO_EXTENSIONS:
            raise VoiceServiceError(
                stage="transcribe",
                error_code=VOICE_UNSUPPORTED_FORMAT,
                error_message=f"Unsupported audio format: {normalized_type or safe_suffix}",
                user_friendly_message="这段录音格式暂时还不支持，换一种浏览器录音格式再试试。",
                status_code=400,
                latency_ms=_elapsed_ms(started_at),
                provider=self.provider_name,
                model=config.transcribe_model,
            )

        client = self._get_client(config, stage="transcribe", started_at=started_at)

        try:
            transcription = client.audio.transcriptions.create(
                model=config.transcribe_model,
                file=(safe_filename, clean_bytes, normalized_type or "audio/webm"),
                language=language,
                response_format="json",
            )
        except Exception as error:  # pragma: no cover - depends on network/provider state
            LOGGER.warning("voice transcription failed: %s", error)
            raise VoiceServiceError(
                stage="transcribe",
                error_code=VOICE_PROVIDER_TIMEOUT if _is_timeout_error(error) else VOICE_ASR_FAILED,
                error_message="OpenAI speech-to-text request failed",
                user_friendly_message="网络有点慢，我们先用文字也可以。" if _is_timeout_error(error) else "这次没有顺利听清，我们再说一遍就好。",
                status_code=504 if _is_timeout_error(error) else 502,
                latency_ms=_elapsed_ms(started_at),
                provider=self.provider_name,
                model=config.transcribe_model,
                debug_message=_exception_debug_message(error),
            ) from error

        text = str(getattr(transcription, "text", "") or "").strip()
        if not text:
            raise VoiceServiceError(
                stage="transcribe",
                error_code=VOICE_ASR_FAILED,
                error_message="Speech-to-text response returned empty text",
                user_friendly_message="这次没有听清具体内容，我们再说一次。",
                status_code=502,
                latency_ms=_elapsed_ms(started_at),
                provider=self.provider_name,
                model=config.transcribe_model,
            )

        return VoiceTranscriptionResult(
            success=True,
            stage="transcribe",
            error_code=None,
            error_message=None,
            user_friendly_message="我听到了，正在整理。",
            latency_ms=_elapsed_ms(started_at),
            provider=self.provider_name,
            model=config.transcribe_model,
            fallback_used=False,
            text=text,
            confidence=None,
        )

    def synthesize_speech(self, *, text: str) -> VoiceSpeechResult:
        """Turn assistant text into a short audio reply."""
        started_at = perf_counter()
        normalized_text = str(text or "").strip()
        if not normalized_text:
            raise VoiceServiceError(
                stage="speak",
                error_code=VOICE_TTS_FAILED,
                error_message="No text provided for text-to-speech",
                user_friendly_message="现在没有可播报的内容。",
                status_code=400,
                latency_ms=_elapsed_ms(started_at),
                provider=self.provider_name,
                model=_resolve_voice_config().tts_model,
            )

        config = _resolve_voice_config()
        client = self._get_client(config, stage="speak", started_at=started_at)

        try:
            speech = client.audio.speech.create(
                model=config.tts_model,
                voice=config.tts_voice,
                input=normalized_text[:4096],
                response_format=config.tts_format,
            )
        except Exception as error:  # pragma: no cover - depends on network/provider state
            LOGGER.warning("voice speech failed: %s", error)
            raise VoiceServiceError(
                stage="speak",
                error_code=VOICE_PROVIDER_TIMEOUT if _is_timeout_error(error) else VOICE_TTS_FAILED,
                error_message="OpenAI text-to-speech request failed",
                user_friendly_message="网络有点慢，我们先用文字也可以。" if _is_timeout_error(error) else "这次没有顺利说出来，不过文字回复已经准备好了。",
                status_code=504 if _is_timeout_error(error) else 502,
                latency_ms=_elapsed_ms(started_at),
                provider=self.provider_name,
                model=config.tts_model,
                debug_message=_exception_debug_message(error),
            ) from error

        audio_bytes = bytes(speech.content or b"")
        if not audio_bytes:
            raise VoiceServiceError(
                stage="speak",
                error_code=VOICE_TTS_FAILED,
                error_message="Text-to-speech response returned empty audio bytes",
                user_friendly_message="这次没有顺利生成语音，不过文字回复已经准备好了。",
                status_code=502,
                latency_ms=_elapsed_ms(started_at),
                provider=self.provider_name,
                model=config.tts_model,
            )

        return VoiceSpeechResult(
            success=True,
            stage="speak",
            error_code=None,
            error_message=None,
            user_friendly_message="我准备好语音了。",
            latency_ms=_elapsed_ms(started_at),
            provider=self.provider_name,
            model=config.tts_model,
            fallback_used=False,
            voice=config.tts_voice,
            audio_bytes=audio_bytes,
            media_type="audio/mpeg",
        )


def get_voice_service() -> OpenAIVoiceService:
    """Return the voice service implementation used by this MVP."""
    return OpenAIVoiceService()
