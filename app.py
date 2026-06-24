from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google.cloud import dialogflow_v2 as dialogflow
import sqlite3
import uuid
import os

app = Flask(__name__)
CORS(app)

# ==================================
# DIALOGFLOW CONFIG
# ==================================

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "dialogflow-key.json"

PROJECT_ID = "shachatbot-ifry"

# ==================================
# DATABASE
# ==================================


def init_db():

    conn = sqlite3.connect("smart_home.db")
    cursor = conn.cursor()

    # Conversations

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT,

        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Messages

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        conversation_id INTEGER,

        sender TEXT,

        message TEXT,

        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


init_db()

# ==================================
# HOME
# ==================================


@app.route("/")
def home():
    return render_template("index.html")

# ==================================
# CREATE NEW CHAT
# ==================================


@app.route("/new_chat", methods=["POST"])
def new_chat():

    conn = sqlite3.connect("smart_home.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO conversations(title)
    VALUES(?)
    """, ("New Chat",))

    conn.commit()

    chat_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "chat_id": chat_id
    })

# ==================================
# GET ALL CHATS
# ==================================


@app.route("/conversations")
def conversations():

    conn = sqlite3.connect("smart_home.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id,title
    FROM conversations
    ORDER BY id DESC
    """)

    chats = cursor.fetchall()

    conn.close()

    return jsonify(chats)

# ==================================
# LOAD CHAT MESSAGES
# ==================================


@app.route("/messages/<int:chat_id>")
def messages(chat_id):

    conn = sqlite3.connect("smart_home.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT sender,message
    FROM messages
    WHERE conversation_id=?
    ORDER BY id ASC
    """, (chat_id,))

    rows = cursor.fetchall()

    conn.close()

    return jsonify(rows)

# ==================================
# CHAT API
# ==================================


@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        user_message = data["message"]
        chat_id = data["chat_id"]

        session_client = dialogflow.SessionsClient()

        session = session_client.session_path(
            PROJECT_ID,
            str(uuid.uuid4())
        )

        text_input = dialogflow.TextInput(
            text=user_message,
            language_code="en"
        )

        query_input = dialogflow.QueryInput(
            text=text_input
        )

        response = session_client.detect_intent(
            request={
                "session": session,
                "query_input": query_input
            }
        )

        bot_reply = response.query_result.fulfillment_text

        conn = sqlite3.connect("smart_home.db")
        cursor = conn.cursor()

        # Save User Message

        cursor.execute("""
        INSERT INTO messages(
            conversation_id,
            sender,
            message
        )
        VALUES(?,?,?)
        """,
                       (
                           chat_id,
                           "user",
                           user_message
                       ))

        # Save Bot Message

        cursor.execute("""
        INSERT INTO messages(
            conversation_id,
            sender,
            message
        )
        VALUES(?,?,?)
        """,
                       (
                           chat_id,
                           "bot",
                           bot_reply
                       ))

        # Update title using first message

        cursor.execute("""
        SELECT title
        FROM conversations
        WHERE id=?
        """, (chat_id,))

        title = cursor.fetchone()[0]

        if title == "New Chat":

            cursor.execute("""
            UPDATE conversations
            SET title=?
            WHERE id=?
            """,
                           (
                               user_message[:30],
                               chat_id
                           ))

        conn.commit()
        conn.close()

        return jsonify({
            "reply": bot_reply
        })

    except Exception as e:

        return jsonify({
            "reply": str(e)
        })

# ==================================
# CLEAR ALL CHATS
# ==================================


@app.route("/clear", methods=["POST"])
def clear():

    conn = sqlite3.connect("smart_home.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM messages")
    cursor.execute("DELETE FROM conversations")

    conn.commit()
    conn.close()

    return jsonify({
        "message": "All chats deleted"
    })

# ==================================
# WHO AM I
# ==================================


@app.route("/whoami")
def whoami():

    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        "dialogflow-key.json"
    )

    return f"""
    Project: {creds.project_id}<br>
    Service Account: {creds.service_account_email}
    """

# ==================================
# DIALOGFLOW TEST
# ==================================


@app.route("/dialogtest")
def dialogtest():

    try:

        session_client = dialogflow.SessionsClient()

        session = session_client.session_path(
            PROJECT_ID,
            str(uuid.uuid4())
        )

        text_input = dialogflow.TextInput(
            text="turn on lights",
            language_code="en"
        )

        query_input = dialogflow.QueryInput(
            text=text_input
        )

        response = session_client.detect_intent(
            request={
                "session": session,
                "query_input": query_input
            }
        )

        return response.query_result.fulfillment_text

    except Exception as e:

        return str(e)

# ==================================
# RUN
# ==================================


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
