import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pymupdf


@dataclass
class OCRResult:
    text: str
    extraction_method: str
    ocr_used: bool
    warning: Optional[str] = None


class OCRService:
    """
    Extract text from digital, scanned, and mixed PDF pages.

    The service automatically searches for the Tesseract language-data
    directory on Windows, Linux, and Streamlit Community Cloud.
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

        self.tessdata_path = self._find_tessdata(
            configured_path=tessdata_path
        )

    def extract_page_text(
        self,
        page: pymupdf.Page,
        mode: str = "auto",
    ) -> OCRResult:
        mode = mode.lower().strip()

        if mode not in self.VALID_MODES:
            raise ValueError(
                "OCR mode must be auto, always, or off."
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
                full_page=True,
            )

        # Auto mode:
        # Use full-page OCR when very little selectable text exists.
        if (
            len(native_text)
            < self.minimum_native_characters
        ):
            return self._perform_ocr(
                page=page,
                native_text=native_text,
                full_page=True,
            )

        # For a page containing normal text and images,
        # OCR only the areas that do not already contain text.
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
        if not self.tessdata_path:
            return OCRResult(
                text=native_text,
                extraction_method="native_text_fallback",
                ocr_used=False,
                warning=(
                    "OCR is unavailable because the Tesseract "
                    "language-data folder could not be located. "
                    "Check packages.txt in the GitHub repository root."
                ),
            )

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
                    warning=(
                        "Tesseract completed OCR but did not "
                        "detect readable text."
                    ),
                )

            extraction_method = (
                "full_page_ocr"
                if full_page
                else "native_text_and_image_ocr"
            )

            return OCRResult(
                text=extracted_text,
                extraction_method=extraction_method,
                ocr_used=True,
            )

        except Exception as error:
            return OCRResult(
                text=native_text,
                extraction_method="native_text_fallback",
                ocr_used=False,
                warning=f"OCR failed: {error}",
            )

    @staticmethod
    def _find_tessdata(
        configured_path: Optional[str],
    ) -> Optional[str]:
        """
        Find the directory containing Tesseract .traineddata files.

        Search order:
        1. Value supplied by settings.py
        2. TESSDATA_PREFIX environment variable
        3. PyMuPDF automatic detection
        4. Common Windows and Linux locations
        """

        candidates: list[Path] = []

        if configured_path:
            candidates.append(
                Path(configured_path)
            )

        environment_path = os.getenv(
            "TESSDATA_PREFIX",
            "",
        ).strip()

        if environment_path:
            environment_candidate = Path(
                environment_path
            )

            candidates.append(
                environment_candidate
            )

            # Some TESSDATA_PREFIX values point to the
            # parent folder rather than directly to tessdata.
            candidates.append(
                environment_candidate / "tessdata"
            )

        try:
            detected_path = pymupdf.get_tessdata()

            if detected_path:
                candidates.append(
                    Path(detected_path)
                )

        except Exception:
            pass

        # Common Streamlit/Linux locations.
        candidates.extend(
            [
                Path(
                    "/usr/share/tesseract-ocr/"
                    "5/tessdata"
                ),
                Path(
                    "/usr/share/tesseract-ocr/"
                    "4.00/tessdata"
                ),
                Path(
                    "/usr/share/tesseract-ocr/"
                    "tessdata"
                ),
                Path("/usr/share/tessdata"),
                Path("/usr/local/share/tessdata"),
            ]
        )

        # Common Windows location.
        candidates.append(
            Path(
                "C:/Program Files/"
                "Tesseract-OCR/tessdata"
            )
        )

        linux_tesseract_root = Path(
            "/usr/share/tesseract-ocr"
        )

        if linux_tesseract_root.exists():
            candidates.extend(
                linux_tesseract_root.glob(
                    "*/tessdata"
                )
            )

        checked_paths: set[str] = set()

        for candidate in candidates:
            normalized_path = str(candidate)

            if normalized_path in checked_paths:
                continue

            checked_paths.add(normalized_path)

            if not candidate.is_dir():
                continue

            required_language_files = [
                language.strip()
                for language in os.getenv(
                    "OCR_LANGUAGE",
                    "eng",
                ).split("+")
                if language.strip()
            ]

            all_languages_available = all(
                (
                    candidate
                    / f"{language}.traineddata"
                ).exists()
                for language in required_language_files
            )

            if all_languages_available:
                return str(candidate)

        return None