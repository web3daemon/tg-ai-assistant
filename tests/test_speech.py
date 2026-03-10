import importlib.util
import unittest


HAS_WHISPER = importlib.util.find_spec("faster_whisper") is not None

if HAS_WHISPER:
    from src.services.speech import SpeechToTextService


@unittest.skipUnless(HAS_WHISPER, "faster-whisper is not installed")
class SpeechTests(unittest.TestCase):
    def test_cuda_runtime_error_detection(self) -> None:
        self.assertTrue(SpeechToTextService._is_cuda_runtime_error(RuntimeError("cublas64_12.dll missing")))
        self.assertFalse(SpeechToTextService._is_cuda_runtime_error(RuntimeError("some other error")))


if __name__ == "__main__":
    unittest.main()
