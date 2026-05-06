from openai import OpenAI
import tkinter as tk
from tkinter import scrolledtext
import random
import threading
import time

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

is_processing = False
typing_active = False
conversation_lock = threading.Lock()

def timestamp():
    return time.strftime("[%H:%M:%S]")

# Window setup
root = tk.Tk()
root.title("T-900 Interface")
root.geometry("600x500")
root.configure(bg="black")

status_label = tk.Label(root, text="STATUS: CONNECTING...", bg="black", fg="yellow")
status_label.pack()

# Chat display
chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="black", fg="lime", insertbackground="lime")
chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

chat_display.tag_config("user", foreground="cyan")
chat_display.tag_config("ai", foreground="lime")
chat_display.tag_config("system", foreground="red")

chat_display.insert(tk.END, f"{timestamp()} SYSTEM BOOT...\n", "system")
chat_display.insert(tk.END, f"{timestamp()} T-900 ONLINE\n\n", "system")

# Input field
prompt_frame = tk.Frame(root, bg="black")
prompt_frame.pack(fill=tk.X, padx=10)

prompt_label = tk.Label(prompt_frame, text="> ", bg="black", fg="lime")
prompt_label.pack(side=tk.LEFT)

user_input = tk.Entry(prompt_frame, bg="black", fg="lime", insertbackground="lime", borderwidth=0)
user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)

status_label.config(text="STATUS: READY", fg="lime")
    
def type_text(text, tag="ai", delay=5, on_complete=None):
    global typing_active
    typing_active = True

    def type_char(index=0):
        global typing_active
        
        if index < len(text) and typing_active:
            chat_display.insert(tk.END, text[index], tag)
            chat_display.see(tk.END)
            root.after(delay, type_char, index + 1)
        else:
            typing_active = False
            if on_complete:
                on_complete()
    type_char()   

def send_message():
    global typing_active
    typing_active = False
    
    global is_processing

    if is_processing:
        return
    
    message = user_input.get()
    if not message.strip():
        return
    
    if message.strip().lower() == "clear":
        chat_display.delete("1.0", tk.END)
        chat_display.insert(tk.END, f"{timestamp()} SYSTEM CLEARED\n\n", "system")
        user_input.delete(0, tk.END)
        
        user_input.focus()
        return
    
    is_processing = True
    root.unbind('<Return>')

    user_input.config(state="disabled")
    send_button.config(state="disabled")

    threading.Thread(target=process_message, args=(message,), daemon=True).start()

# Send function
def process_message(message):

    root.after(0, lambda: chat_display.insert(tk.END, f"{timestamp()} YOU: {message}\n", "user"))
    root.after(0, lambda: user_input.delete(0, tk.END))

    # Show processing message
    def insert_analyzing():
        analyzing_index["value"] = chat_display.index(tk.END)
        chat_display.insert(tk.END, f"{timestamp()} T-900: Analyzing...\n", ("system", "analyzing"))

    analyzing_index = {"value": None}
    root.after(0, insert_analyzing)
    
    time.sleep(0.15)
    for attempt in range(2):
        try:
            
            
            # Add user message to memory   
            with conversation_lock:
                conversation.append({"role": "user", "content": message})
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *conversation.copy()
                ]

            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages
            )

            raw_reply = response.choices[0].message.content

            # Save clean memory
            # Trim memory
            MAX_HISTORY = 10
            with conversation_lock:
                conversation.append({"role": "assistant", "content": raw_reply})
                conversation[:] = conversation[-MAX_HISTORY:]

            # Format for UI
            reply = f"""STATUS: ACTIVE \nREQUEST: UNDERSTOOD \nRESPONSE: \n>> {raw_reply}"""
            
            def update_response():
                if analyzing_index["value"]:
                    chat_display.delete(analyzing_index["value"], f"{analyzing_index['value']} lineend+1c")
                chat_display.insert(tk.END, f"{timestamp()} T-900:\n", "system")
                def done():
                    user_input.config(state="normal")
                    send_button.config(state="normal")
                    user_input.focus()
                    global is_processing
                    is_processing = False
                    root.bind('<Return>', on_enter)
                    global typing_active
                    typing_active = False
                    chat_display.see(tk.END)

                type_text(reply + "\n\n", "ai", delay = 2 if len(reply) < 200 else 1, on_complete=done)

            root.after(0, lambda: status_label.config(text="STATUS: ONLINE", fg="lime"))
            root.after(0, update_response)
            
            break

        except Exception as e:
            if attempt == 1:
                def handle_error():
                    chat_display.insert(tk.END, f"{timestamp()} ERROR: {str(e)}\n\n", "system")
                    chat_display.see(tk.END)
                    user_input.config(state="normal")
                    send_button.config(state="normal")
                    user_input.focus()
                    global is_processing
                    is_processing = False
                    global typing_active
                    typing_active = False
                    root.bind('<Return>', on_enter)

                root.after(0, handle_error)
                root.after(0, lambda: status_label.config(text="STATUS: OFFLINE", fg="red"))
            else:
                time.sleep(1)


# Send button
send_button = tk.Button(root, text="Send", bg="black", fg="lime", command=send_message)
send_button.pack(pady=5)

# Enter key support
def on_enter(event):
    if not is_processing:
        send_message()

root.bind('<Return>', on_enter)

user_input.focus()
# Run app
root.mainloop()
