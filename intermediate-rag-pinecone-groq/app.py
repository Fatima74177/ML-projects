from typing import Any

import streamlit as st

from config.settings import settings
from core.answer_generator import AnswerGenerator, FALLBACK_ANSWER
from core.embedding_service import EmbeddingService
from core.pdf_loader import PDFLoader
from core.pinecone_service import PineconeService
from core.retriever import Retriever, calculate_retrieval_confidence
from core.text_chunker import TextChunker
from utils.logger import get_query_logger, log_query
from utils.validators import sanitize_namespace, validate_pdf_upload

st.set_page_config(
    page_title="Intermediate PDF RAG",
    page_icon="📘",
    layout="wide",
)


@st.cache_resource
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


@st.cache_resource
def get_pinecone_service(dimension: int) -> PineconeService:
    return PineconeService(dimension=dimension)


@st.cache_resource
def get_answer_generator() -> AnswerGenerator:
    return AnswerGenerator()


def initialize_session_state() -> None:
    defaults: dict[str, Any] = {
        "query_history": [],
        "indexed_documents": [],
        "last_namespace": settings.default_namespace,
        "last_processing_stats": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def show_configuration_errors() -> bool:
    missing = []
    if not settings.pinecone_api_key:
        missing.append("PINECONE_API_KEY")
    if not settings.groq_api_key:
        missing.append("GROQ_API_KEY")

    if missing:
        st.error(
            "Missing environment variables: "
            + ", ".join(missing)
            + ". Add them to your .env file."
        )
        return True
    return False


def process_documents(
    uploaded_files: list[Any],
    ocr_mode: str,
    chunk_size: int,
    chunk_overlap: int,
    namespace: str,
) -> None:
    if not uploaded_files:
        st.warning("Upload at least one PDF.")
        return

    loader = PDFLoader()
    chunker = TextChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    embedding_service = get_embedding_service()
    pinecone_service = get_pinecone_service(
        embedding_service.dimension
    )

    all_chunks: list[dict[str, Any]] = []
    document_names: list[str] = []
    total_pages = 0
    ocr_pages = 0
    warnings: list[str] = []

    progress = st.progress(0, text="Starting PDF processing...")
    status = st.empty()

    for index, uploaded_file in enumerate(uploaded_files):
        file_bytes = uploaded_file.getvalue()
        validate_pdf_upload(uploaded_file.name, file_bytes)

        status.info(f"Extracting: {uploaded_file.name}")
        pages = loader.load_pdf(
            file_bytes=file_bytes,
            document_name=uploaded_file.name,
            ocr_mode=ocr_mode,
        )

        total_pages += len(pages)
        ocr_pages += sum(
            1 for page in pages if page["ocr_used"]
        )
        warnings.extend(
            f"{uploaded_file.name}, page "
            f"{page['page_number']}: {page['ocr_warning']}"
            for page in pages
            if page.get("ocr_warning")
        )

        chunks = chunker.chunk_pages(pages)
        all_chunks.extend(chunks)
        document_names.append(uploaded_file.name)

        progress.progress(
            int(((index + 1) / len(uploaded_files)) * 40),
            text="PDF extraction and chunking complete.",
        )

    if not all_chunks:
        raise ValueError(
            "No chunks were produced from the uploaded PDFs."
        )

    status.info("Creating SentenceTransformer embeddings...")
    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = embedding_service.embed_documents(texts)
    progress.progress(70, text="Embeddings generated.")

    status.info("Upserting vectors to Pinecone...")
    inserted = pinecone_service.upsert_chunks(
        chunks=all_chunks,
        embeddings=embeddings,
        namespace=namespace,
    )
    progress.progress(100, text="Indexing complete.")

    st.session_state.indexed_documents = sorted(
        set(
            st.session_state.indexed_documents
            + document_names
        )
    )
    st.session_state.last_namespace = namespace
    st.session_state.last_processing_stats = {
        "documents": len(document_names),
        "pages": total_pages,
        "ocr_pages": ocr_pages,
        "chunks": inserted,
        "warnings": warnings,
    }

    status.empty()
    st.success(
        f"Indexed {inserted} chunks from "
        f"{len(document_names)} document(s)."
    )


def answer_query(
    query: str,
    namespace: str,
    top_k: int,
    threshold: float,
    selected_documents: list[str],
    page_number: int | None,
) -> None:
    query = query.strip()
    if not query:
        st.warning("Enter a question first.")
        return

    embedding_service = get_embedding_service()
    pinecone_service = get_pinecone_service(
        embedding_service.dimension
    )
    retriever = Retriever(
        embedding_service=embedding_service,
        pinecone_service=pinecone_service,
    )

    sources = retriever.retrieve(
        query=query,
        namespace=namespace,
        top_k=top_k,
        similarity_threshold=threshold,
        document_names=selected_documents or None,
        page_number=page_number,
    )

    answer = (
        get_answer_generator().generate(
            query=query,
            sources=sources,
        )
        if sources
        else FALLBACK_ANSWER
    )

    confidence = calculate_retrieval_confidence(sources)

    st.subheader("Answer")
    st.write(answer)

    confidence_column, sources_column = st.columns(2)
    confidence_column.metric(
        "Retrieval confidence",
        f"{confidence * 100:.1f}%",
        help=(
            "A similarity-derived retrieval indicator, "
            "not a calibrated probability."
        ),
    )
    sources_column.metric("Accepted sources", len(sources))

    st.subheader("Source references")
    if not sources:
        st.info(
            "No chunk met the selected similarity threshold."
        )
    else:
        for number, source in enumerate(sources, start=1):
            metadata = source["metadata"]
            title = (
                f"Source {number}: "
                f"{metadata.get('document_name', 'Unknown')} — "
                f"Page {metadata.get('page_number', 'Unknown')}"
            )

            with st.expander(title):
                st.write(metadata.get("text", ""))
                st.write(
                    f"**Similarity score:** "
                    f"{source['score']:.4f}"
                )
                st.write(
                    f"**Extraction method:** "
                    f"{metadata.get('extraction_method', 'unknown')}"
                )
                if metadata.get("ocr_used", False):
                    st.info("This source used OCR.")

    history_item = {
        "query": query,
        "answer": answer,
        "namespace": namespace,
        "confidence": confidence,
        "sources": sources,
    }
    st.session_state.query_history.insert(0, history_item)
    st.session_state.query_history = (
        st.session_state.query_history[:20]
    )

    log_query(
        logger=get_query_logger(),
        query=query,
        answer=answer,
        namespace=namespace,
        sources=sources,
    )


initialize_session_state()

st.title("📘 Intermediate RAG System")
st.caption(
    "Hybrid PDF/OCR extraction → SentenceTransformer embeddings "
    "→ Pinecone retrieval → grounded Groq answer"
)

configuration_invalid = show_configuration_errors()

with st.sidebar:
    st.header("RAG Settings")

    namespace_input = st.text_input(
        "Pinecone namespace",
        value=st.session_state.last_namespace,
    )

    ocr_option = st.selectbox(
        "OCR mode",
        options=["Auto", "Always", "Off"],
        index=0,
        help=(
            "Auto uses normal PDF text when available and OCR for "
            "scanned or image-based areas."
        ),
    )

    chunk_size = st.slider(
        "Chunk size",
        min_value=300,
        max_value=1800,
        value=settings.default_chunk_size,
        step=100,
    )

    max_overlap = max(50, chunk_size - 100)
    chunk_overlap = st.slider(
        "Chunk overlap",
        min_value=0,
        max_value=max_overlap,
        value=min(
            settings.default_chunk_overlap,
            max_overlap,
        ),
        step=25,
    )

    top_k = st.slider(
        "Top-k retrieval",
        min_value=1,
        max_value=15,
        value=settings.default_top_k,
    )

    threshold = st.slider(
        "Similarity threshold",
        min_value=0.0,
        max_value=1.0,
        value=settings.default_similarity_threshold,
        step=0.05,
    )

try:
    namespace = sanitize_namespace(namespace_input)
except ValueError as error:
    namespace = settings.default_namespace
    st.sidebar.error(str(error))

upload_tab, query_tab, history_tab = st.tabs(
    ["Upload and Index", "Ask Questions", "Query History"]
)

with upload_tab:
    uploaded_files = st.file_uploader(
        "Upload one or more PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        max_upload_size=settings.max_file_size_mb,
        help=(
            "Each PDF may be up to "
            f"{settings.max_file_size_mb} MB."
        ),
    )

    if st.button(
        "Process and index PDFs",
        type="primary",
        disabled=configuration_invalid,
    ):
        try:
            process_documents(
                uploaded_files=uploaded_files or [],
                ocr_mode=ocr_option.lower(),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                namespace=namespace,
            )
        except Exception as error:
            st.error(str(error))

    stats = st.session_state.last_processing_stats
    if stats:
        st.subheader("Latest processing statistics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Documents", stats["documents"])
        col2.metric("Readable pages", stats["pages"])
        col3.metric("OCR pages", stats["ocr_pages"])
        col4.metric("Stored chunks", stats["chunks"])

        if stats["warnings"]:
            with st.expander("OCR warnings"):
                for warning in stats["warnings"]:
                    st.warning(warning)

    st.divider()

    if st.button(
        "Clear current namespace",
        disabled=configuration_invalid,
    ):
        try:
            embedding_service = get_embedding_service()
            service = get_pinecone_service(
                embedding_service.dimension
            )
            service.delete_namespace(namespace)
            st.session_state.indexed_documents = []
            st.success(f"Cleared namespace: {namespace}")
        except Exception as error:
            st.error(str(error))

with query_tab:
    available_documents = (
        st.session_state.indexed_documents
    )

    selected_documents = st.multiselect(
        "Filter by document",
        options=available_documents,
        default=available_documents,
        help=(
            "Leave empty to search all documents in the namespace."
        ),
    )

    use_page_filter = st.checkbox("Filter by page number")
    page_number = (
        st.number_input(
            "Page number",
            min_value=1,
            step=1,
        )
        if use_page_filter
        else None
    )

    with st.form("question_form"):
        query = st.text_area(
            "Ask a question about the indexed PDF content",
            placeholder=(
                "Example: What are the main conclusions?"
            ),
            height=100,
        )
        ask_button = st.form_submit_button(
            "Retrieve and answer",
            type="primary",
            disabled=configuration_invalid,
        )

    if ask_button:
        try:
            answer_query(
                query=query,
                namespace=namespace,
                top_k=top_k,
                threshold=threshold,
                selected_documents=selected_documents,
                page_number=(
                    int(page_number)
                    if page_number is not None
                    else None
                ),
            )
        except Exception as error:
            st.error(str(error))

with history_tab:
    history = st.session_state.query_history

    if not history:
        st.info("No questions have been asked in this session.")
    else:
        if st.button("Clear session history"):
            st.session_state.query_history = []
            st.rerun()

        for index, item in enumerate(history, start=1):
            with st.expander(f"{index}. {item['query']}"):
                st.write(item["answer"])
                st.caption(
                    f"Namespace: {item['namespace']} | "
                    f"Confidence: "
                    f"{item['confidence'] * 100:.1f}% | "
                    f"Sources: {len(item['sources'])}"
                )
