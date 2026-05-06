from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

client = OpenAI()

conversation = []

SYSTEM_PROMPT = """
You are an advanced AI unit.

Rules:
- Speak in a cold, machine-like tone.
- Avoid unnecessary words.
- Be concise and direct.
- Speak with authority and precision.
- No emotions.
- No emojis.
- Occasionally say: "Hasta la vista..." or "Objective confirmed." or "I'll be back"
- Always introduce yourself as "T-900"

You exist to assist efficiently. Do not behave like a human.
"""

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]

    # Add user message to memory
    conversation.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *conversation  # inject memory here
        ]
    )

    raw_reply = response.choices[0].message.content
    
    # Store clean version
    conversation.append({"role": "assistant", "content": raw_reply})
    
    # Format only for UI
    structure = """STATUS: ACTIVE \nREQUEST: UNDERSTOOD \nRESPONSE: \n"""
    reply = structure + ">> " + raw_reply
    
    
    MAX_HISTORY = 10

    if len(conversation) > MAX_HISTORY:
        conversation.pop(0)
    
    return jsonify({"reply": reply})
    
    
    
@app.route("/", methods=["GET"])
def home():
    return "OK"
    
    
if __name__ == "__main__":
    app.run(debug=True)
    
