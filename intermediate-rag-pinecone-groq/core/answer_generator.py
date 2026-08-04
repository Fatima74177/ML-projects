from typing import Any

from groq import (
    APIConnectionError,
    APIError,
    Groq,
    RateLimitError,
)

from config.settings import settings

FALLBACK_ANSWER = (
    "The answer is not available in the provided document."
)


class AnswerGenerator:
    """Generate answers strictly from retrieved PDF context using Groq."""

    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is missing from the .env file."
            )

        self.client = Groq(
            api_key=settings.groq_api_key,
            timeout=60.0,
            max_retries=2,
        )

    def generate(
        self,
        query: str,
        sources: list[dict[str, Any]],
    ) -> str:
        if not sources:
            return FALLBACK_ANSWER

        context_blocks: list[str] = []

        for number, source in enumerate(
            sources,
            start=1,
        ):
            metadata = source["metadata"]

            context_blocks.append(
                "\n".join(
                    [
                        f"[Source {number}]",
                        (
                            "Document: "
                            f"{metadata.get('document_name', 'Unknown')}"
                        ),
                        (
                            "Page: "
                            f"{metadata.get('page_number', 'Unknown')}"
                        ),
                        f"Similarity: {source['score']:.4f}",
                        "Content:",
                        str(metadata.get("text", "")),
                    ]
                )
            )

        context = "\n\n".join(context_blocks)

        system_prompt = f"""
You are a document-grounded question-answering assistant.

Follow these rules strictly:

1. Answer only from the provided document context.
2. Do not use outside knowledge.
3. Do not invent information.
4. Add source markers such as [Source 1].
5. If the answer is not clearly present, respond exactly:
{FALLBACK_ANSWER}
6. Keep the answer clear and direct.
""".strip()

        user_prompt = f"""
QUESTION:
{query}

DOCUMENT CONTEXT:
{context}

Answer using only the document context.
""".strip()

        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0.0,
                max_tokens=settings.groq_max_tokens,
            )

        except RateLimitError as error:
            raise RuntimeError(
                "Groq rate limit reached. Check your Groq API quota."
            ) from error

        except APIConnectionError as error:
            raise ConnectionError(
                "Could not connect to the Groq API."
            ) from error

        except APIError as error:
            raise RuntimeError(
                f"Groq API error: {error}"
            ) from error

        answer = (
            response.choices[0].message.content or ""
        ).strip()

        return answer or FALLBACK_ANSWER