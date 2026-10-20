"""Check STT responsiveness and failure contracts without real audio/providers."""
import asyncio
import json
from pathlib import Path
import sys
import threading
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main


class Request:
    async def body(self):
        return b"synthetic fixture"


async def check():
    started, release, finished = threading.Event(), threading.Event(), threading.Event()

    def slow_transcription(*args):
        started.set()
        release.wait(timeout=2)
        finished.set()
        return "想听一首老歌"

    with patch.object(main, '_extract_audio_upload', return_value=('sample.webm', b'audio', 'audio/webm')):
        with patch.object(main, '_transcribe_with_whisper', slow_transcription):
            request = asyncio.create_task(main.transcribe_stt(Request()))
            try:
                assert await asyncio.to_thread(started.wait, 1), 'transcription did not start'
                assert not finished.is_set(), 'synchronous STT blocked the event loop'
            finally:
                release.set()
            assert await request == {'text': '想听一首老歌'}
        for result, status in [(RuntimeError('未配置语音识别'), 503), ('', 502)]:
            kwargs = {'side_effect': result} if isinstance(result, Exception) else {'return_value': result}
            with patch.object(main, '_transcribe_with_whisper', **kwargs):
                response = await main.transcribe_stt(Request())
                assert response.status_code == status
                assert json.loads(response.body)['text'] == ''
    started.clear()
    release.clear()
    finished.clear()
    with patch.object(main.tts_service, '_request_minimax_tts', slow_transcription):
        request = asyncio.create_task(main.tts_service.synthesize('测试朗读'))
        try:
            assert await asyncio.to_thread(started.wait, 1)
            assert not finished.is_set(), 'synchronous TTS blocked the event loop'
        finally:
            release.set()
        await request
    print('PASS: STT/TTS yield the event loop; unavailable/empty STT results remain actionable')


if __name__ == '__main__':
    asyncio.run(check())
