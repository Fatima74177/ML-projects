import re


MAX_MESSAGE_LENGTH = 1000


def clean_user_input(text: str) -> str:
    """
    Clean user input before sending it to the AI.
    """

    if text is None:
        return ""

    text = str(text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing spaces
    text = text.strip()

    return text


def validate_message(text: str):
    """
    Validate user message.
    """

    if not text:
        raise ValueError("Please say or enter a message.")

    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValueError(
            f"Message cannot exceed {MAX_MESSAGE_LENGTH} characters."
        )


def prepare_message(text: str) -> str:
    """
    Clean and validate the message.
    """

    cleaned_text = clean_user_input(text)

    validate_message(cleaned_text)

    return cleaned_text