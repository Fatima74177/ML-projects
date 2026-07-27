import re


SUPPORTED_LANGUAGES = {
    "english": "en-US",
    "urdu": "ur-PK",
    "hindi": "hi-IN"
}


def clean_text_for_speech(text: str) -> str:
    """
    Remove symbols and formatting that should not be spoken aloud.
    """

    if text is None:
        return ""

    text = str(text)

    # Remove Markdown headings
    text = re.sub(r"#{1,6}\s*", "", text)

    # Remove Markdown bold and italic symbols
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("*", "")
    text = text.replace("_", "")

    # Remove backticks used for code formatting
    text = text.replace("`", "")

    # Replace URLs with simple spoken text
    text = re.sub(
        r"https?://\S+",
        "link",
        text
    )

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Replace repeated spaces and line breaks
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def limit_speech_length(
    text: str,
    maximum_characters: int = 1500
) -> str:
    """
    Limit extremely long responses before text-to-speech playback.
    """

    if len(text) <= maximum_characters:
        return text

    shortened_text = text[:maximum_characters]

    # Try to stop at the end of a sentence
    sentence_end = max(
        shortened_text.rfind("."),
        shortened_text.rfind("?"),
        shortened_text.rfind("!")
    )

    if sentence_end > 200:
        shortened_text = shortened_text[:sentence_end + 1]
    else:
        shortened_text = shortened_text.rstrip() + "..."

    return shortened_text


def prepare_text_for_speech(text: str) -> str:
    """
    Prepare an AI response for browser text-to-speech.
    """

    cleaned_text = clean_text_for_speech(text)
    return limit_speech_length(cleaned_text)


def get_language_code(language: str = "english") -> str:
    """
    Return the browser speech language code.
    """

    language = language.lower().strip()

    return SUPPORTED_LANGUAGES.get(
        language,
        SUPPORTED_LANGUAGES["english"]
    )