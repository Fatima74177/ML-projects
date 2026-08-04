import re


def clean_text(text: str) -> str:
    """Remove common PDF/OCR formatting artifacts."""
    if not text:
        return ""

    text = text.replace("\x00", "")
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
