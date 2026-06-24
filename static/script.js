// =====================================
// GLOBAL VARIABLES
// =====================================

let currentChatId = null;

// =====================================
// CREATE NEW CHAT
// =====================================

async function createNewChat() {

    try {

        const response = await fetch("/new_chat", {
            method: "POST"
        });

        const data = await response.json();

        currentChatId = data.chat_id;

        document.getElementById("chat-box").innerHTML = `
            <div class="bot-message">
                Hello 👋 <br><br>
                I am your Smart Home Assistant.
                How can I help you today?
            </div>
        `;

        loadConversations();

    } catch (error) {

        console.error(error);

    }

}

// =====================================
// LOAD CHAT LIST
// =====================================

async function loadConversations() {

    try {

        const response = await fetch("/conversations");

        const chats = await response.json();

        const historyBox =
            document.getElementById("history-box");

        historyBox.innerHTML = "";

        chats.forEach(chat => {

            const div =
                document.createElement("div");

            div.className =
                "chat-item";

            div.innerText =
                chat[1];

            div.onclick =
                () => loadMessages(chat[0]);

            historyBox.appendChild(div);

        });

    } catch (error) {

        console.error(error);

    }

}

// =====================================
// LOAD ONE CHAT
// =====================================

async function loadMessages(chatId) {

    currentChatId = chatId;

    try {

        const response =
            await fetch(`/messages/${chatId}`);

        const messages =
            await response.json();

        const chatBox =
            document.getElementById("chat-box");

        chatBox.innerHTML = "";

        messages.forEach(msg => {

            const div =
                document.createElement("div");

            if (msg[0] === "user") {

                div.className =
                    "user-message";

            } else {

                div.className =
                    "bot-message";

            }

            div.innerText =
                msg[1];

            chatBox.appendChild(div);

        });

        chatBox.scrollTop =
            chatBox.scrollHeight;

    } catch (error) {

        console.error(error);

    }

}

// =====================================
// SEND MESSAGE
// =====================================

async function sendMessage() {

    const input =
        document.getElementById("user-input");

    const message =
        input.value.trim();

    if (message === "") {
        return;
    }

    // create first chat automatically

    if (currentChatId === null) {

        await createNewChat();

    }

    const chatBox =
        document.getElementById("chat-box");

    // USER MESSAGE

    const userDiv =
        document.createElement("div");

    userDiv.className =
        "user-message";

    userDiv.innerText =
        message;

    chatBox.appendChild(userDiv);

    chatBox.scrollTop =
        chatBox.scrollHeight;

    input.value = "";

    try {

        const response =
            await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    message: message,

                    chat_id: currentChatId

                })

            });

        const data =
            await response.json();

        const botDiv =
            document.createElement("div");

        botDiv.className =
            "bot-message";

        botDiv.innerText =
            data.reply;

        chatBox.appendChild(botDiv);

        chatBox.scrollTop =
            chatBox.scrollHeight;

        loadConversations();

    }

    catch (error) {

        console.error(error);

        const errorDiv =
            document.createElement("div");

        errorDiv.className =
            "bot-message";

        errorDiv.innerText =
            "Unable to connect to Smart Home Assistant.";

        chatBox.appendChild(errorDiv);

    }

}

// =====================================
// NEW CHAT BUTTON
// =====================================

function clearChat() {

    createNewChat();

}

// =====================================
// ENTER KEY
// =====================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const input =
            document.getElementById(
                "user-input"
            );

        input.addEventListener(
            "keypress",
            function (event) {

                if (
                    event.key === "Enter"
                ) {

                    sendMessage();

                }

            }
        );

    }
);

// =====================================
// VOICE COMMAND
// =====================================

const voiceBtn =
    document.getElementById(
        "voice-btn"
    );

if (voiceBtn) {

    voiceBtn.addEventListener(
        "click",
        () => {

            if (
                !(
                    "webkitSpeechRecognition"
                    in window
                )
            ) {

                alert(
                    "Speech Recognition not supported."
                );

                return;

            }

            const recognition =
                new webkitSpeechRecognition();

            recognition.lang =
                "en-US";

            recognition.start();

            recognition.onresult =
                function (event) {

                    const speechText =
                        event.results[0][0]
                            .transcript;

                    document.getElementById(
                        "user-input"
                    ).value =
                        speechText;

                    sendMessage();

                };

        }
    );

}

// =====================================
// INITIAL LOAD
// =====================================

window.onload = async function () {

    await loadConversations();

};