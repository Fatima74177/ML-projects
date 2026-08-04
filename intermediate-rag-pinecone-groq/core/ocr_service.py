import io
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pymupdf
import pytesseract
from PIL import Image
from pytesseract import TesseractNotFoundError


@dataclass
class OCRResult:
    text: str
    extraction_method: str
    ocr_used: bool
    warning: Optional[str] = None


class OCRService:
    """
    OCR service for digital, scanned and mixed-content PDF pages.

    PyMuPDF renders the PDF page as an image.
    Pytesseract sends that image to the installed Tesseract command.
    """

    VALID_MODES = {
        "auto",
        "always",
        "off",
    }

    def __init__(
        self,
        language: str = "eng",
        dpi: int = 300,
        minimum_native_characters: int = 80,
        tessdata_path: Optional[str] = None,
    ) -> None:
        self.language = language
        self.dpi = dpi
        self.minimum_native_characters = (
            minimum_native_characters
        )

        self.tessdata_path = self._validate_tessdata_path(
            tessdata_path
        )

        self.tesseract_command = (
            self._configure_tesseract_command()
        )

        (
            self.ocr_available,
            self.ocr_status_message,
            self.available_languages,
        ) = self._check_tesseract()

    def extract_page_text(
        self,
        page: pymupdf.Page,
        mode: str = "auto",
    ) -> OCRResult:
        mode = mode.lower().strip()

        if mode not in self.VALID_MODES:
            raise ValueError(
                "OCR mode must be auto, always or off."
            )

        native_text = page.get_text(
            "text",
            sort=True,
        ).strip()

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
                combine_with_native=False,
            )

        # A page with very little selectable text is probably scanned.
        if (
            len(native_text)
            < self.minimum_native_characters
        ):
            return self._perform_ocr(
                page=page,
                native_text=native_text,
                combine_with_native=False,
            )

        # A mixed page may contain selectable text and images with text.
        if page.get_images(full=True):
            return self._perform_ocr(
                page=page,
                native_text=native_text,
                combine_with_native=True,
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
        combine_with_native: bool,
    ) -> OCRResult:
        if not self.ocr_available:
            return OCRResult(
                text=native_text,
                extraction_method="native_text_fallback",
                ocr_used=False,
                warning=self.ocr_status_message,
            )

        try:
            page_image = self._render_page(page)

            configuration = "--oem 3 --psm 3"

            if self.tessdata_path:
                configuration += (
                    f' --tessdata-dir "{self.tessdata_path}"'
                )

            ocr_text = pytesseract.image_to_string(
                page_image,
                lang=self.language,
                config=configuration,
                timeout=120,
            ).strip()

            if not ocr_text:
                return OCRResult(
                    text=native_text,
                    extraction_method="native_text_fallback",
                    ocr_used=False,
                    warning=(
                        "Tesseract ran successfully but did not "
                        "detect readable text on this page."
                    ),
                )

            if combine_with_native:
                final_text = self._merge_text(
                    native_text=native_text,
                    ocr_text=ocr_text,
                )

                extraction_method = (
                    "native_text_and_tesseract_ocr"
                )
            else:
                final_text = ocr_text
                extraction_method = "full_page_tesseract_ocr"

            return OCRResult(
                text=final_text,
                extraction_method=extraction_method,
                ocr_used=True,
            )

        except RuntimeError as error:
            return OCRResult(
                text=native_text,
                extraction_method="native_text_fallback",
                ocr_used=False,
                warning=(
                    "OCR processing timed out or failed: "
                    f"{error}"
                ),
            )

        except pytesseract.pytesseract.TesseractNotFoundError:
            return OCRResult(
                text=native_text,
                extraction_method="native_text_fallback",
                ocr_used=False,
                warning=(
                    "The Tesseract command is not installed or "
                    "is not available in PATH. Check packages.txt."
                ),
            )

        except Exception as error:
            return OCRResult(
                text=native_text,
                extraction_method="native_text_fallback",
                ocr_used=False,
                warning=f"OCR failed: {error}",
            )

    def _render_page(
        self,
        page: pymupdf.Page,
    ) -> Image.Image:
        """
        Render a PDF page at the configured DPI and return a PIL image.
        """
        scale = self.dpi / 72.0

        matrix = pymupdf.Matrix(
            scale,
            scale,
        )

        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )

        image_bytes = pixmap.tobytes("png")

        image = Image.open(
            io.BytesIO(image_bytes)
        ).convert("RGB")

        return image

    def _configure_tesseract_command(
        self,
    ) -> Optional[str]:
        """
        Locate Tesseract on Streamlit/Linux or Windows.
        """
        environment_command = os.getenv(
            "TESSERACT_CMD",
            "",
        ).strip()

        candidates = []

        if environment_command:
            candidates.append(environment_command)

        detected_command = shutil.which("tesseract")

        if detected_command:
            candidates.append(detected_command)

        candidates.extend(
            [
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
                (
                    "C:/Program Files/"
                    "Tesseract-OCR/tesseract.exe"
                ),
            ]
        )

        for candidate in candidates:
            candidate_path = Path(candidate)

            if candidate_path.is_file():
                command = str(candidate_path)

                pytesseract.pytesseract.tesseract_cmd = (
                    command
                )

                return command

        return None

    def _check_tesseract(
        self,
    ) -> tuple[bool, str, list[str]]:
        if not self.tesseract_command:
            return (
                False,
                (
                    "Tesseract executable was not found. "
                    "Ensure packages.txt is at the GitHub "
                    "repository root and contains "
                    "tesseract-ocr and tesseract-ocr-eng."
                ),
                [],
            )

        try:
            pytesseract.get_tesseract_version()

            languages = pytesseract.get_languages(
                config=""
            )

            required_languages = [
                item.strip()
                for item in self.language.split("+")
                if item.strip()
            ]

            missing_languages = [
                item
                for item in required_languages
                if item not in languages
            ]

            if missing_languages:
                return (
                    False,
                    (
                        "Tesseract is installed, but these OCR "
                        "languages are missing: "
                        + ", ".join(missing_languages)
                    ),
                    languages,
                )

            return (
                True,
                "Tesseract OCR is available.",
                languages,
            )

        except Exception as error:
            return (
                False,
                f"Tesseract validation failed: {error}",
                [],
            )

    @staticmethod
    def _validate_tessdata_path(
        tessdata_path: Optional[str],
    ) -> Optional[str]:
        """
        Ignore invalid paths such as a Windows path on Linux deployment.
        """
        if not tessdata_path:
            return None

        path = Path(tessdata_path)

        if not path.is_dir():
            return None

        return str(path)

    @staticmethod
    def _merge_text(
        native_text: str,
        ocr_text: str,
    ) -> str:
        """
        Avoid adding completely duplicated OCR text.
        """
        if not native_text:
            return ocr_text

        normalized_native = re.sub(
            r"\s+",
            " ",
            native_text,
        ).strip().lower()

        normalized_ocr = re.sub(
            r"\s+",
            " ",
            ocr_text,
        ).strip().lower()

        if normalized_ocr in normalized_native:
            return native_text

        if normalized_native in normalized_ocr:
            return ocr_text

        return (
            native_text
            + "\n\n"
            + ocr_text
        )

    def get_status(self) -> dict[str, object]:
        """
        Return safe deployment diagnostics.
        """
        return {
            "available": self.ocr_available,
            "command": self.tesseract_command,
            "language": self.language,
            "available_languages": (
                self.available_languages
            ),
            "message": self.ocr_status_message,
        }