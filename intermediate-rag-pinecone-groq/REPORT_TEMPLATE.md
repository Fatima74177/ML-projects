# Technical Report: Intermediate RAG System

## 1. Introduction

Explain the aim of answering questions strictly from uploaded PDF
documents, including scanned and mixed-content pages.

## 2. System architecture

Describe:

PDF validation → hybrid extraction/OCR → cleaning → chunking →
SentenceTransformer embeddings → Pinecone → retrieval → Groq →
answer and source attribution.

## 3. Design decisions

Discuss Streamlit, automatic OCR, page-specific chunks, overlap,
cosine similarity, metadata, and context-only answer generation.

## 4. Embedding model

Model:

`sentence-transformers/all-MiniLM-L6-v2`

Explain that the Pinecone index dimension must match the detected
SentenceTransformer embedding dimension.

## 5. Pinecone configuration

Discuss the serverless index, cosine metric, namespace strategy,
upserts, metadata fields, queries, and filters.

## 6. OCR integration

Explain Auto, Always, and Off modes, Tesseract language packs,
scan quality, and OCR processing time.

## 7. Hallucination prevention

Explain the threshold, fixed unavailable response, restricted prompt,
source markers, excerpts, and page-number display.

## 8. Performance analysis

Measure indexing time, query time, readable pages, OCR pages, chunks,
retrieval accuracy, and the effect of chunk size, top-k, and threshold.

## 9. Challenges

Possible challenges include OCR speed, scan quality, API limits,
Pinecone dimension mismatch, duplicate uploads, and threshold tuning.

## 10. Conclusion

Summarize the result, limitations, and future improvements.
