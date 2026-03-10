import importlib.util
import unittest

from src.utils.text import split_text


HAS_AIOGRAM = importlib.util.find_spec("aiogram") is not None

if HAS_AIOGRAM:
    from aiogram.types import BufferedInputFile
    from src.config import settings
    from src.utils.responses import FormattedTextChunk, build_response_payloads


class TextSplitTests(unittest.TestCase):
    def test_split_text_prefers_boundaries(self) -> None:
        chunks = split_text("один два три четыре", 9)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(" ".join(chunks), "один два три четыре")


@unittest.skipUnless(HAS_AIOGRAM, "aiogram is not installed")
class ResponseTests(unittest.TestCase):
    def test_build_response_payloads_returns_chunks_for_normal_text(self) -> None:
        payload = build_response_payloads("**Привет**")
        self.assertIsInstance(payload, list)
        self.assertIsInstance(payload[0], FormattedTextChunk)
        self.assertIn("<b>Привет</b>", payload[0].html_text)

    def test_build_response_payloads_returns_file_for_long_text(self) -> None:
        long_text = "a" * settings.long_response_as_file_threshold
        payload = build_response_payloads(long_text)
        self.assertIsInstance(payload, BufferedInputFile)


if __name__ == "__main__":
    unittest.main()
