from dataclasses import dataclass
from typing import Optional

import pymupdf


@dataclass
class OCRResult:
    text: str
    extraction_method: str
    ocr_used: bool
    warning: Optional[str] = None


class OCRService:
    """Hybrid extractor for digital, scanned, and mixed PDF pages."""

    VALID_MODES = {"auto", "always", "off"}

    def __init__(
        self,
        language: str = "eng",
        dpi: int = 300,
        minimum_native_characters: int = 80,
        tessdata_path: Optional[str] = None,
    ) -> None:
        self.language = language
        self.dpi = dpi
        self.minimum_native_characters = minimum_native_characters
        self.tessdata_path = tessdata_path

    def extract_page_text(
        self,
        page: pymupdf.Page,
        mode: str = "auto",
    ) -> OCRResult:
        mode = mode.lower().strip()
        if mode not in self.VALID_MODES:
            raise ValueError("OCR mode must be auto, always, or off.")

        native_text = page.get_text("text", sort=True).strip()

        if mode == "off":
            return OCRResult(
                text=native_text,
                extraction_method="native_text",
                ocr_used=False,
            )

        if mode == "always":
            return self._perform_ocr(
                page=page,
                native_text=native_text,
                full_page=True,
            )

        if len(native_text) < self.minimum_native_characters:
            return self._perform_ocr(
                page=page,
                native_text=native_text,
                full_page=True,
            )

        if page.get_images(full=True):
            return self._perform_ocr(
                page=page,
                native_text=native_text,
                full_page=False,
            )

        return OCRResult(
            text=native_text,
            extraction_method="native_text",
            ocr_used=False,
        )

    def _perform_ocr(
        self,
        page: pymupdf.Page,
        native_text: str,
        full_page: bool,
    ) -> OCRResult:
        try:
            text_page = page.get_textpage_ocr(
                language=self.language,
                dpi=self.dpi,
                full=full_page,
                tessdata=self.tessdata_path,
            )
            extracted_text = page.get_text(
                "text",
                textpage=text_page,
                sort=True,
            ).strip()

            if not extracted_text:
                return OCRResult(
                    text=native_text,
                    extraction_method="native_text_fallback",
                    ocr_used=False,
                    warning="OCR did not detect readable text.",
                )

            method = (
                "full_page_ocr"
                if full_page
                else "native_text_and_image_ocr"
            )
            return OCRResult(
                text=extracted_text,
                extraction_method=method,
                ocr_used=True,
            )
        except Exception as error:
            return OCRResult(
                text=native_text,
                extraction_method="native_text_fallback",
                ocr_used=False,
                warning=f"OCR failed: {error}",
            )
