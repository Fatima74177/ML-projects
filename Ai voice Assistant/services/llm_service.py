import os
from google import genai
from google.genai import errors, types


def get_gemini_client():
    """
    Create and return a Google Gemini API client.
    """

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Add your Google AI Studio API key "
            "to the .env file."
        )

    return genai.Client(api_key=api_key)


def prepare_conversation(conversation: list[dict]) -> list:
    """
    Convert the application's conversation format into Gemini's format.
    """

    if not conversation:
        raise ValueError("Conversation cannot be empty.")

    prepared_contents = []

    for message in conversation:
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()

        if not content:
            continue

        if role == "user":
            gemini_role = "user"
        elif role == "assistant":
            gemini_role = "model"
        else:
            continue

        prepared_contents.append(
            types.Content(
                role=gemini_role,
                parts=[
                    types.Part.from_text(text=content)
                ]
            )
        )

    if not prepared_contents:
        raise ValueError(
            "The conversation does not contain any valid messages."
        )

    return prepared_contents


def extract_response_text(response) -> str:
    """
    Safely extract text from the Gemini response.
    """

    response_text = getattr(response, "text", None)

    if response_text and response_text.strip():
        return response_text.strip()

    raise ValueError(
        "Gemini returned an empty response. Please try again."
    )


def generate_ai_response(
    conversation: list[dict],
    system_prompt: str
) -> str:
    """
    Send the conversation to Gemini and return the generated response.
    """

    if not system_prompt or not system_prompt.strip():
        raise ValueError("The system prompt cannot be empty.")

    client = get_gemini_client()

    prepared_contents = prepare_conversation(
        conversation
    )

    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.6-flash"
    ).strip()

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prepared_contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt.strip(),
                max_output_tokens=500
            )
        )

        return extract_response_text(response)

    except errors.APIError as error:
        error_code = getattr(error, "code", None)
        error_message = str(
            getattr(error, "message", error)
        )

        print(
            f"Gemini API error: "
            f"code={error_code}, "
            f"message={error_message}"
        )

        if error_code in [400, 401, 403]:
            if (
                "API key" in error_message
                or "API_KEY" in error_message
                or "key not valid" in error_message.lower()
            ):
                raise ValueError(
                    "The Gemini API key is invalid. "
                    "Check GEMINI_API_KEY in your .env file."
                )

            raise ValueError(
                "Gemini rejected the request. Check your API key "
                "and Google AI Studio project."
            )

        if error_code == 404:
            raise ValueError(
                f"The Gemini model '{model_name}' was not found. "
                "Check GEMINI_MODEL in your .env file."
            )

        if error_code == 429:
            raise ValueError(
                "The Gemini request limit has been reached. "
                "Please try again shortly."
            )

        if error_code in [500, 502, 503, 504]:
            raise ValueError(
                "The Gemini service is temporarily unavailable. "
                "Please try again."
            )

        raise ValueError(
            "Gemini returned an API error. Please try again."
        )

    except ValueError:
        raise

    except Exception as error:
        print(f"Unexpected Gemini error: {error}")

        raise ValueError(
            "An unexpected Gemini service error occurred."
        )