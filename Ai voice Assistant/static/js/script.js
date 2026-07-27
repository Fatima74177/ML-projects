const startCallButton = document.getElementById("startCallButton");
const endCallButton = document.getElementById("endCallButton");
const newConversationButton = document.getElementById(
    "newConversationButton"
);
const closeErrorButton = document.getElementById("closeErrorButton");

const textMessageForm = document.getElementById("textMessageForm");
const textMessageInput = document.getElementById("textMessageInput");
const sendMessageButton = document.getElementById("sendMessageButton");

const conversationMessages = document.getElementById(
    "conversationMessages"
);
const emptyConversation = document.getElementById("emptyConversation");
const typingIndicator = document.getElementById("typingIndicator");

const avatarContainer = document.getElementById("avatarContainer");
const statusBadge = document.getElementById("statusBadge");
const statusText = document.getElementById("statusText");
const instructionText = document.getElementById("instructionText");

const callTimer = document.getElementById("callTimer");
const timerText = document.getElementById("timerText");

const errorMessage = document.getElementById("errorMessage");
const errorText = document.getElementById("errorText");

const config = window.voiceAssistantConfig;

const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

let recognition = null;
let isCallActive = false;
let isListening = false;
let isProcessing = false;
let shouldRestartRecognition = false;

let timerInterval = null;
let callStartTime = null;

let currentSpeech = null;

function initializeSpeechRecognition() {
    if (!SpeechRecognition) {
        showError(
            "Speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge."
        );

        startCallButton.disabled = true;
        return;
    }

    recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = function () {
        isListening = true;
        setStatus("listening");
    };

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript.trim();

        isListening = false;

        if (!transcript) {
            showError("No speech was detected. Please try again.");
            restartListeningAfterDelay();
            return;
        }

        if (isExitCommand(transcript)) {
            addMessage("user", transcript);

            endCall();

            instructionText.textContent =
                "Voice command detected. The call has ended.";

            return;
        }

        handleUserMessage(transcript);
    };

    recognition.onerror = function (event) {
        isListening = false;

        if (event.error === "no-speech") {
            showError(
                "No speech was detected. Please speak clearly."
            );
        } else if (event.error === "audio-capture") {
            showError(
                "No microphone was detected. Please check your microphone."
            );
        } else if (event.error === "not-allowed") {
            showError(
                "Microphone permission was denied. Please allow microphone access in your browser."
            );

            endCall();
            return;
        } else if (event.error === "network") {
            showError(
                "Speech recognition could not connect to the network."
            );
        } else if (event.error !== "aborted") {
            showError(
                "Speech recognition failed. Please try again."
            );
        }
    };

    recognition.onend = function () {
        isListening = false;

        if (
            isCallActive &&
            shouldRestartRecognition &&
            !isProcessing &&
            !isSpeechPlaying()
        ) {
            restartListeningAfterDelay();
        }
    };
}

function isExitCommand(message) {
    const cleanedMessage = message
        .toLowerCase()
        .trim()
        .replace(/[.,!?]/g, "");

    const exitCommands = [
        "exit",
        "stop",
        "quit",
        "goodbye",
        "bye",
        "end",
        "end call",
        "stop call",
        "stop listening",
        "close assistant",
        "close the assistant",
        "end the call"
    ];

    return exitCommands.includes(cleanedMessage);
}

function startCall() {
    if (!recognition) {
        showError(
            "Speech recognition is unavailable. Please use the text input."
        );
        return;
    }

    hideError();

    isCallActive = true;
    shouldRestartRecognition = true;
    isProcessing = false;

    startCallButton.disabled = true;
    endCallButton.disabled = false;

    callTimer.classList.add("active");

    startTimer();
    startListening();
}

function endCall() {
    isCallActive = false;
    shouldRestartRecognition = false;
    isProcessing = false;

    startCallButton.disabled = false;
    endCallButton.disabled = true;

    callTimer.classList.remove("active");

    stopTimer();
    stopListening();
    stopSpeaking();
    hideTypingIndicator();

    setStatus("ended");

    instructionText.textContent =
        "The call has ended. Press Start Call to begin again.";
}

function startListening() {
    if (
        !recognition ||
        !isCallActive ||
        isListening ||
        isProcessing ||
        isSpeechPlaying()
    ) {
        return;
    }

    try {
        recognition.start();
    } catch (error) {
        console.error("Recognition start error:", error);
    }
}

function stopListening() {
    if (!recognition) {
        return;
    }

    try {
        recognition.abort();
    } catch (error) {
        console.error("Recognition stop error:", error);
    }

    isListening = false;
}

function restartListeningAfterDelay() {
    if (
        !isCallActive ||
        !shouldRestartRecognition ||
        isProcessing
    ) {
        return;
    }

    window.setTimeout(function () {
        startListening();
    }, 700);
}

async function handleUserMessage(message) {
    if (!message || isProcessing) {
        return;
    }

    if (isExitCommand(message)) {
        addMessage("user", message);
        endCall();

        instructionText.textContent =
            "Exit command detected. The call has ended.";

        return;
    }

    hideError();
    stopListening();

    isProcessing = true;
    shouldRestartRecognition = false;

    addMessage("user", message);

    setStatus("thinking");
    showTypingIndicator();
    setControlsLoading(true);

    try {
        const response = await fetch(config.chatUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message ||
                    "The assistant could not generate a response."
            );
        }

        hideTypingIndicator();

        addMessage("assistant", data.ai_response);

        await speakResponse(
            data.speech_text || data.ai_response
        );
    } catch (error) {
        hideTypingIndicator();

        console.error("Chat request error:", error);

        showError(
            error.message ||
                "The AI service is unavailable. Please try again."
        );

        if (isCallActive) {
            setStatus("ready");
        } else {
            setStatus("ended");
        }
    } finally {
        isProcessing = false;
        setControlsLoading(false);

        if (isCallActive) {
            shouldRestartRecognition = true;
            restartListeningAfterDelay();
        }
    }
}

function addMessage(role, message) {
    if (emptyConversation) {
        emptyConversation.classList.add("hidden");
    }

    const messageRow = document.createElement("div");

    const roleClass =
        role === "user"
            ? "user-message-row"
            : "ai-message-row";

    messageRow.className = `message-row ${roleClass}`;

    const avatar = document.createElement("div");

    avatar.className =
        role === "user"
            ? "message-avatar user-message-avatar"
            : "message-avatar ai-message-avatar";

    avatar.textContent = role === "user" ? "You" : "AI";

    const messageContent = document.createElement("div");
    messageContent.className = "message-content";

    const messageLabel = document.createElement("span");
    messageLabel.className = "message-label";
    messageLabel.textContent =
        role === "user" ? "You" : "AI Assistant";

    const messageBubble = document.createElement("div");
    messageBubble.className = "message-bubble";
    messageBubble.textContent = message;

    const messageTime = document.createElement("span");
    messageTime.className = "message-time";
    messageTime.textContent = getCurrentTime();

    messageContent.appendChild(messageLabel);
    messageContent.appendChild(messageBubble);
    messageContent.appendChild(messageTime);

    if (role === "user") {
        messageRow.appendChild(messageContent);
        messageRow.appendChild(avatar);
    } else {
        messageRow.appendChild(avatar);
        messageRow.appendChild(messageContent);
    }

    conversationMessages.appendChild(messageRow);

    scrollConversationToBottom();
}

function showTypingIndicator() {
    typingIndicator.classList.remove("hidden");
    scrollConversationToBottom();
}

function hideTypingIndicator() {
    typingIndicator.classList.add("hidden");
}

function setStatus(status) {
    statusBadge.classList.remove(
        "listening",
        "thinking",
        "speaking",
        "ended"
    );

    avatarContainer.classList.remove(
        "listening",
        "speaking"
    );

    if (status === "listening") {
        statusBadge.classList.add("listening");
        avatarContainer.classList.add("listening");

        statusText.textContent = "Listening";
        instructionText.textContent =
            "I am listening. Speak naturally.";
    } else if (status === "thinking") {
        statusBadge.classList.add("thinking");

        statusText.textContent = "Thinking";
        instructionText.textContent =
            "Generating an intelligent response...";
    } else if (status === "speaking") {
        statusBadge.classList.add("speaking");
        avatarContainer.classList.add("speaking");

        statusText.textContent = "Speaking";
        instructionText.textContent =
            "The assistant is responding.";
    } else if (status === "ended") {
        statusBadge.classList.add("ended");

        statusText.textContent = "Call Ended";
    } else {
        statusText.textContent = "Ready";
        instructionText.textContent =
            "Press Start Call and speak naturally.";
    }
}

function speakResponse(text) {
    return new Promise(function (resolve) {
        if (
            !("speechSynthesis" in window) ||
            typeof SpeechSynthesisUtterance === "undefined"
        ) {
            showError(
                "Text-to-speech is not supported in this browser."
            );

            resolve();
            return;
        }

        stopSpeaking();

        currentSpeech = new SpeechSynthesisUtterance(text);

        currentSpeech.lang = "en-US";
        currentSpeech.rate = 1;
        currentSpeech.pitch = 1;
        currentSpeech.volume = 1;

        const selectedVoice = getPreferredVoice();

        if (selectedVoice) {
            currentSpeech.voice = selectedVoice;
        }

        currentSpeech.onstart = function () {
            setStatus("speaking");
        };

        currentSpeech.onend = function () {
            currentSpeech = null;

            if (isCallActive) {
                setStatus("ready");
            } else {
                setStatus("ended");
            }

            resolve();
        };

        currentSpeech.onerror = function (event) {
            currentSpeech = null;

            if (event.error !== "interrupted") {
                showError(
                    "The assistant could not play the voice response."
                );
            }

            if (isCallActive) {
                setStatus("ready");
            } else {
                setStatus("ended");
            }

            resolve();
        };

        window.speechSynthesis.speak(currentSpeech);
    });
}

function stopSpeaking() {
    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
    }

    currentSpeech = null;

    avatarContainer.classList.remove("speaking");
}

function isSpeechPlaying() {
    if (!("speechSynthesis" in window)) {
        return false;
    }

    return (
        window.speechSynthesis.speaking ||
        window.speechSynthesis.pending
    );
}

function getPreferredVoice() {
    if (!("speechSynthesis" in window)) {
        return null;
    }

    const voices = window.speechSynthesis.getVoices();

    if (!voices.length) {
        return null;
    }

    const preferredVoiceNames = [
        "Google US English",
        "Microsoft Aria Online",
        "Microsoft Jenny Online",
        "Samantha"
    ];

    for (const voiceName of preferredVoiceNames) {
        const matchingVoice = voices.find(function (voice) {
            return voice.name.includes(voiceName);
        });

        if (matchingVoice) {
            return matchingVoice;
        }
    }

    return (
        voices.find(function (voice) {
            return voice.lang === "en-US";
        }) ||
        voices.find(function (voice) {
            return voice.lang.startsWith("en");
        }) ||
        voices[0]
    );
}

function startTimer() {
    stopTimer();

    callStartTime = Date.now();

    updateTimer();

    timerInterval = window.setInterval(
        updateTimer,
        1000
    );
}

function stopTimer() {
    if (timerInterval) {
        window.clearInterval(timerInterval);
        timerInterval = null;
    }
}

function resetTimer() {
    stopTimer();

    callStartTime = null;
    timerText.textContent = "00:00";
    callTimer.classList.remove("active");
}

function updateTimer() {
    if (!callStartTime) {
        timerText.textContent = "00:00";
        return;
    }

    const elapsedSeconds = Math.floor(
        (Date.now() - callStartTime) / 1000
    );

    const minutes = Math.floor(elapsedSeconds / 60);
    const seconds = elapsedSeconds % 60;

    timerText.textContent =
        `${formatNumber(minutes)}:${formatNumber(seconds)}`;
}

function formatNumber(number) {
    return String(number).padStart(2, "0");
}

function getCurrentTime() {
    return new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });
}

function setControlsLoading(isLoading) {
    sendMessageButton.disabled = isLoading;
    textMessageInput.disabled = isLoading;
    newConversationButton.disabled = isLoading;

    const buttonText = sendMessageButton.querySelector(
        "span:first-child"
    );

    if (buttonText) {
        buttonText.textContent = isLoading
            ? "Wait"
            : "Send";
    }
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.classList.remove("hidden");
}

function hideError() {
    errorMessage.classList.add("hidden");
    errorText.textContent = "";
}

function scrollConversationToBottom() {
    window.setTimeout(function () {
        conversationMessages.scrollTop =
            conversationMessages.scrollHeight;
    }, 50);
}

async function createNewConversation() {
    hideError();

    const callWasActive = isCallActive;

    endCall();
    setControlsLoading(true);

    try {
        const response = await fetch(
            config.newConversationUrl,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message ||
                    "Could not start a new conversation."
            );
        }

        clearConversationMessages();
        resetTimer();
        setStatus("ready");

        startCallButton.disabled = false;
        endCallButton.disabled = true;

        instructionText.textContent =
            "A new conversation is ready. Press Start Call to begin.";

        if (callWasActive) {
            instructionText.textContent =
                "Previous call ended. Press Start Call for a new conversation.";
        }
    } catch (error) {
        console.error(
            "New conversation error:",
            error
        );

        showError(
            error.message ||
                "Could not create a new conversation."
        );
    } finally {
        setControlsLoading(false);
    }
}

function clearConversationMessages() {
    const oldMessages =
        conversationMessages.querySelectorAll(
            ".message-row"
        );

    oldMessages.forEach(function (message) {
        message.remove();
    });

    if (emptyConversation) {
        emptyConversation.classList.remove("hidden");
    }

    hideTypingIndicator();
}

async function loadConversationHistory() {
    try {
        const response = await fetch(
            config.conversationUrl
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            return;
        }

        if (!Array.isArray(data.conversation)) {
            return;
        }

        data.conversation.forEach(function (message) {
            if (
                message.role === "user" ||
                message.role === "assistant"
            ) {
                addMessage(
                    message.role,
                    message.content
                );
            }
        });
    } catch (error) {
        console.error(
            "Conversation history error:",
            error
        );
    }
}

textMessageForm.addEventListener(
    "submit",
    function (event) {
        event.preventDefault();

        const message =
            textMessageInput.value.trim();

        if (!message) {
            showError(
                "Please enter a message first."
            );

            textMessageInput.focus();
            return;
        }

        textMessageInput.value = "";

        handleUserMessage(message);
    }
);

startCallButton.addEventListener(
    "click",
    startCall
);

endCallButton.addEventListener(
    "click",
    endCall
);

newConversationButton.addEventListener(
    "click",
    createNewConversation
);

closeErrorButton.addEventListener(
    "click",
    hideError
);

window.addEventListener(
    "beforeunload",
    function () {
        stopTimer();
        stopListening();
        stopSpeaking();
    }
);

window.addEventListener(
    "load",
    function () {
        initializeSpeechRecognition();
        loadConversationHistory();
        setStatus("ready");

        if ("speechSynthesis" in window) {
            window.speechSynthesis.getVoices();

            window.speechSynthesis.onvoiceschanged =
                function () {
                    window.speechSynthesis.getVoices();
                };
        }
    }
);