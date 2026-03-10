import importlib.util
import unittest


HAS_CONTENT_DEPS = all(
    importlib.util.find_spec(module_name) is not None
    for module_name in ("fitz", "docx", "openpyxl")
)

if HAS_CONTENT_DEPS:
    from src.services.content import ContentExtractionError, extract_document, extract_image


@unittest.skipUnless(HAS_CONTENT_DEPS, "Document processing dependencies are not installed")
class ContentTests(unittest.TestCase):
    def test_extract_txt_document(self) -> None:
        document = extract_document("notes.txt", "Привет\nмир".encode("utf-8"), "Суммаризируй")
        self.assertEqual(document.media_type, "txt")
        self.assertIn("Привет", document.extracted_text)
        self.assertIn("Суммаризируй", document.model_text)

    def test_extract_document_rejects_unknown_extension(self) -> None:
        with self.assertRaises(ContentExtractionError):
            extract_document("archive.zip", b"123", "")

    def test_extract_image_encodes_data(self) -> None:
        image = extract_image("image.png", "image/png", b"abc", "Опиши")
        self.assertEqual(image.mime_type, "image/png")
        self.assertEqual(image.base64_data, "YWJj")
        self.assertEqual(image.prompt_text, "Опиши")


if __name__ == "__main__":
    unittest.main()
