import hashlib
import re
from typing import Any


class TextChunker:
    """Sentence-aware overlapping page-level chunker."""

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size < 200:
            raise ValueError("Chunk size must be at least 200 characters.")
        if chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                "Chunk overlap must be smaller than chunk size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(
        self,
        pages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []

        for page in pages:
            page_chunks = self._chunk_text(page["text"])
            for index, chunk_text in enumerate(page_chunks, start=1):
                raw_id = (
                    f"{page['document_id']}|{page['page_number']}|"
                    f"{index}|{chunk_text}"
                )
                chunk_id = hashlib.sha1(
                    raw_id.encode("utf-8")
                ).hexdigest()

                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "document_id": page["document_id"],
                        "document_name": page["document_name"],
                        "page_number": page["page_number"],
                        "chunk_number": index,
                        "text": chunk_text,
                        "ocr_used": page["ocr_used"],
                        "extraction_method": page["extraction_method"],
                    }
                )

        return chunks

    def _chunk_text(self, text: str) -> list[str]:
        units = self._split_into_units(text)
        chunks: list[str] = []
        current = ""

        for unit in units:
            if len(unit) > self.chunk_size:
                if current.strip():
                    chunks.append(current.strip())
                    current = ""
                chunks.extend(self._split_long_unit(unit))
                continue

            candidate = f"{current} {unit}".strip()
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue

            if current.strip():
                chunks.append(current.strip())
                overlap = self._overlap_tail(current)
                current = f"{overlap} {unit}".strip()
            else:
                current = unit

        if current.strip():
            chunks.append(current.strip())

        return self._remove_duplicates(chunks)

    @staticmethod
    def _split_into_units(text: str) -> list[str]:
        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(r"\n{2,}", text)
            if paragraph.strip()
        ]
        units: list[str] = []

        for paragraph in paragraphs:
            sentences = re.split(
                r"(?<=[.!?۔])\s+",
                paragraph,
            )
            units.extend(
                sentence.strip()
                for sentence in sentences
                if sentence.strip()
            )

        return units or [text.strip()]

    def _split_long_unit(self, text: str) -> list[str]:
        parts: list[str] = []
        start = 0
        step = self.chunk_size - self.chunk_overlap

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            part = text[start:end].strip()
            if part:
                parts.append(part)
            if end >= len(text):
                break
            start += step

        return parts

    def _overlap_tail(self, text: str) -> str:
        if self.chunk_overlap == 0:
            return ""

        tail = text[-self.chunk_overlap :]
        first_space = tail.find(" ")
        if first_space != -1:
            tail = tail[first_space + 1 :]
        return tail.strip()

    @staticmethod
    def _remove_duplicates(chunks: list[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []

        for chunk in chunks:
            normalized = re.sub(r"\s+", " ", chunk).strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(normalized)

        return unique
