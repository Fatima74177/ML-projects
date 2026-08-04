import hashlib
from typing import Any

import pymupdf

from config.settings import settings
from core.ocr_service import OCRService
from core.text_cleaner import clean_text


class PDFLoader:
    def __init__(self) -> None:
        self.ocr_service = OCRService(
            language=settings.ocr_language,
            dpi=settings.ocr_dpi,
            minimum_native_characters=settings.ocr_min_native_characters,
            tessdata_path=settings.tessdata_prefix,
        )

    def load_pdf(
        self,
        file_bytes: bytes,
        document_name: str,
        ocr_mode: str = "auto",
    ) -> list[dict[str, Any]]:
        if not file_bytes:
            raise ValueError("The uploaded PDF is empty.")

        if len(file_bytes) > settings.max_file_size_mb * 1024 * 1024:
            raise ValueError(
                f"{document_name} exceeds the "
                f"{settings.max_file_size_mb} MB limit."
            )

        if b"%PDF" not in file_bytes[:1024]:
            raise ValueError(f"{document_name} is not a valid PDF file.")

        document_id = hashlib.sha256(file_bytes).hexdigest()[:20]
        extracted_pages: list[dict[str, Any]] = []

        try:
            with pymupdf.open(
                stream=file_bytes,
                filetype="pdf",
            ) as document:
                if document.page_count == 0:
                    raise ValueError("The PDF has no pages.")

                if document.needs_pass:
                    raise ValueError(
                        "Password-protected PDFs are not supported."
                    )

                for page_index in range(document.page_count):
                    page = document.load_page(page_index)
                    result = self.ocr_service.extract_page_text(
                        page=page,
                        mode=ocr_mode,
                    )
                    cleaned_text = clean_text(result.text)

                    if not cleaned_text:
                        continue

                    extracted_pages.append(
                        {
                            "document_id": document_id,
                            "document_name": document_name,
                            "page_number": page_index + 1,
                            "text": cleaned_text,
                            "ocr_used": result.ocr_used,
                            "extraction_method": result.extraction_method,
                            "ocr_warning": result.warning,
                            "character_count": len(cleaned_text),
                        }
                    )
        except ValueError:
            raise
        except Exception as error:
            raise RuntimeError(
                f"Could not process {document_name}: {error}"
            ) from error

        if not extracted_pages:
            raise ValueError(
                f"No readable text was found in {document_name}."
            )

        return extracted_pages
