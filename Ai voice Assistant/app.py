from flask import Flask, jsonify, render_template, request, session
from dotenv import load_dotenv
from services.llm_service import generate_ai_response
from services.text_processor import prepare_message
from services.speech_service import prepare_text_for_speech
import os
import secrets

# Load values from the .env file.
# override=True prevents an old Windows environment variable
# from overriding the value stored in .env.
load_dotenv(override=True)

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    secrets.token_hex(32)
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

SYSTEM_PROMPT = """
You are a helpful AI voice assistant.

Follow these rules:
1. Give clear, accurate and natural answers.
2. Keep answers reasonably short because they will be spoken aloud.
3. Use simple language unless the user requests technical details.
4. Respond in a friendly and conversational style.
5. Avoid unnecessary headings, symbols and emojis.
6. Do not use Markdown tables.
7. Remember the recent conversation context.
8. If a question is unclear, politely ask the user to clarify it.
"""


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "message": "No request data was received."
            }), 400

        user_message = prepare_message(
            data.get("message", "")
        )

        conversation = session.get(
            "conversation",
            []
        )

        conversation.append({
            "role": "user",
            "content": user_message
        })

        ai_response = generate_ai_response(
            conversation=conversation,
            system_prompt=SYSTEM_PROMPT
        )

        speech_text = prepare_text_for_speech(
            ai_response
        )

        conversation.append({
            "role": "assistant",
            "content": ai_response
        })

        # Keep only the last 20 messages.
        session["conversation"] = conversation[-20:]
        session.modified = True

        return jsonify({
            "success": True,
            "user_message": user_message,
            "ai_response": ai_response,
            "speech_text": speech_text
        }), 200

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400

    except Exception as error:
        print(f"Chat API error: {error}")

        return jsonify({
            "success": False,
            "message": (
                "The Gemini AI service is currently unavailable. "
                "Please try again."
            )
        }), 500


@app.route("/api/new-conversation", methods=["POST"])
def new_conversation():
    try:
        session.pop("conversation", None)
        session.modified = True

        return jsonify({
            "success": True,
            "message": "A new conversation has been started."
        }), 200

    except Exception as error:
        print(f"New conversation error: {error}")

        return jsonify({
            "success": False,
            "message": "Could not start a new conversation."
        }), 500


@app.route("/api/conversation", methods=["GET"])
def get_conversation():
    try:
        conversation = session.get(
            "conversation",
            []
        )

        return jsonify({
            "success": True,
            "conversation": conversation
        }), 200

    except Exception as error:
        print(f"Conversation history error: {error}")

        return jsonify({
            "success": False,
            "message": "Could not load conversation history."
        }), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    gemini_api_key = os.getenv(
        "GEMINI_API_KEY",
        ""
    ).strip()

    gemini_model = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash"
    ).strip()

    return jsonify({
        "success": True,
        "status": "running",
        "application": "AI Voice Assistant",
        "ai_provider": "Google Gemini",
        "gemini_configured": bool(gemini_api_key),
        "gemini_model": gemini_model
    }), 200


@app.errorhandler(404)
def page_not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "message": "The requested API route was not found."
        }), 404

    return render_template("index.html"), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "message": "This request method is not allowed."
    }), 405


@app.errorhandler(500)
def internal_server_error(error):
    print(f"Internal server error: {error}")

    return jsonify({
        "success": False,
        "message": "An internal server error occurred."
    }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )