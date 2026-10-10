"""
Document Intelligence (Section 7).

OCR note: PaddleOCR's model weights are hosted on endpoints unreachable from
this offline build environment. This service uses Tesseract OCR (a real,
open-source OCR engine -- REAL_MODEL for the text-extraction step itself),
combined with deterministic regex/heuristic field parsing (labeled HEURISTIC)
to pull structured fields out of raw OCR text. Swapping the OCR backend to
PaddleOCR later only requires replacing `run_ocr()`.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional

import pytesseract
import cv2
import numpy as np

from app.models._all import ModelType
from app.utils.image_utils import bytes_to_cv2, image_quality_score, sha256_hex

DATE_RE = re.compile(r"\b(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2})\b")
DOC_NUMBER_RE = re.compile(r"\b([A-Z]{1,3}[0-9]{5,10}|[0-9]{6,12})\b")
NAME_LINE_RE = re.compile(r"(?:name|full name)\s*[:\-]?\s*([A-Za-z ,.'-]{3,60})", re.IGNORECASE)
NATIONALITY_RE = re.compile(r"(?:nationality)\s*[:\-]?\s*([A-Za-z]{3,30})", re.IGNORECASE)


@dataclass
class DocumentAnalysisResult:
    ocr_text: str
    extracted_fields: dict
    ocr_confidence: float
    document_score: float
    anomalies: list = field(default_factory=list)
    model_type: str = ModelType.REAL_MODEL.value  # tesseract is a real OCR engine
    file_hash: str = ""
    quality_score: float = 0.0


def _preprocess_for_ocr(img_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11)
    return gray


def run_ocr(img_bgr: np.ndarray) -> tuple[str, float]:
    processed = _preprocess_for_ocr(img_bgr)
    data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
    words, confs = [], []
    for txt, conf in zip(data["text"], data["conf"]):
        txt = txt.strip()
        if not txt:
            continue
        try:
            c = float(conf)
        except (TypeError, ValueError):
            continue
        if c < 0:
            continue
        words.append(txt)
        confs.append(c)
    text = " ".join(words)
    avg_conf = (sum(confs) / len(confs) / 100.0) if confs else 0.0
    return text, round(avg_conf, 4)


def extract_fields(text: str) -> dict:
    fields = {}
    dates = DATE_RE.findall(text)
    if dates:
        fields["dates_found"] = dates
        fields["date_of_birth"] = dates[0]
        if len(dates) > 1:
            fields["issue_or_expiry_date"] = dates[1]
    doc_numbers = DOC_NUMBER_RE.findall(text)
    if doc_numbers:
        fields["document_number"] = doc_numbers[0]
    name_match = NAME_LINE_RE.search(text)
    if name_match:
        fields["name"] = name_match.group(1).strip()
    nat_match = NATIONALITY_RE.search(text)
    if nat_match:
        fields["nationality"] = nat_match.group(1).strip()
    return fields


def detect_anomalies(text: str, fields: dict, ocr_confidence: float, quality_score: float) -> list[str]:
    anomalies = []
    if ocr_confidence < 0.35:
        anomalies.append("Very low OCR confidence -- text may be unreadable or document is obscured.")
    if quality_score < 0.3:
        anomalies.append("Poor image quality (blur/lighting) detected.")
    if "document_number" not in fields:
        anomalies.append("No recognizable document number pattern found.")
    if "dates_found" in fields and len(fields["dates_found"]) >= 2:
        try:
            # crude expiry-before-issue sanity check on raw digit strings
            d1 = re.sub(r"\D", "", fields["dates_found"][0])
            d2 = re.sub(r"\D", "", fields["dates_found"][1])
            if d1 and d2 and d1 == d2:
                anomalies.append("Issue and expiry dates appear identical -- review recommended.")
        except Exception:
            pass
    if len(text.strip()) < 15:
        anomalies.append("Extracted text is unusually short for a government-style document.")
    return anomalies


def analyze_document(file_bytes: bytes) -> DocumentAnalysisResult:
    img = bytes_to_cv2(file_bytes)
    quality = image_quality_score(img)
    ocr_available = True
    try:
        text, ocr_conf = run_ocr(img)
    except pytesseract.TesseractNotFoundError:
        text, ocr_conf = "", 0.0
        ocr_available = False
    fields = extract_fields(text)
    anomalies = detect_anomalies(text, fields, ocr_conf, quality)
    if not ocr_available:
        anomalies.append("Tesseract OCR is not installed; document text extraction was skipped.")

    # Document score: blends OCR confidence, image quality, and field completeness.
    completeness = min(len(fields) / 4.0, 1.0)
    doc_score = round(0.45 * ocr_conf + 0.30 * quality + 0.25 * completeness, 4) * 100
    doc_score = max(0.0, min(100.0, doc_score))

    return DocumentAnalysisResult(
        ocr_text=text,
        extracted_fields=fields,
        ocr_confidence=ocr_conf,
        document_score=round(doc_score, 2),
        anomalies=anomalies,
        model_type=ModelType.REAL_MODEL.value if ocr_available else ModelType.HEURISTIC.value,
        file_hash=sha256_hex(file_bytes),
        quality_score=quality,
    )
