from gradio_client import Client
from customtkinter import *
from tkinter import messagebox


def create_ai_frame(parent):
    frame = CTkFrame(parent)

    def send_request():
        user_input = request_entry.get().strip()
        if not user_input:
            messagebox.showerror("Ошибка", "Введите запрос для отправки.")
            return

        request_entry.delete(0, END)
        info_display.configure(state="normal")
        info_display.delete("1.0", END)
        info_display.insert(END, "ИИ думает...")
        info_display.configure(state="disabled")

        def process_response():
            try:
                response = AI(user_input)
                info_display.configure(state="normal")
                info_display.delete("1.0", END)
                info_display.insert(END, response + "\n\n")
                info_display.see(END)
                info_display.configure(state="disabled")
            except Exception as e:
                info_display.configure(state="normal")
                info_display.delete("1.0", END)
                info_display.insert(END, f"Ошибка: {e}\n\n")
                info_display.see(END)
                info_display.configure(state="disabled")

        parent.after(100, process_response)

    header_label = CTkLabel(frame, text="UFO AI", font=("Arial", 18, "bold"))
    header_label.pack(pady=5)

    info_display = CTkTextbox(frame, wrap="word", state="disabled", height=30)  
    info_display.pack(fill=BOTH, expand=True, padx=(0, 10), pady=(0, 5))

    scrollbar = CTkScrollbar(frame, command=info_display.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    info_display.configure(yscrollcommand=scrollbar.set)

    entry_frame = CTkFrame(frame)
    entry_frame.pack(fill=X, padx=10, pady=(0, 5))

    request_entry = CTkEntry(entry_frame, height=30)
    request_entry.pack(side=LEFT, fill=X, expand=True)

    send_button = CTkButton(entry_frame, text="Отправить", command=send_request)
    send_button.pack(side=RIGHT, padx=(5, 0))

    request_entry.bind("<Return>", lambda event: send_request())  

    return frame

def AI(topic):
    try:
        client = Client("Qwen/Qwen2.5")
        prompt = topic

        result = client.predict(
            prompt,
            [], "Ты ИИ который помогает отвечать на вопросы, ты отвечаешь на Русском", "72B",
            api_name="/model_chat_1"
        )

        if isinstance(result, tuple) and len(result) > 1:
            response_list = result[1]
            if response_list and isinstance(response_list, list) and len(response_list) > 0:
                if isinstance(response_list[0], list) and len(response_list[0]) > 1:
                    if 'text' in response_list[0][1]:
                        return response_list[0][1]['text']
                    else:
                        raise ValueError("Поле 'text' не найдено в ответе.")
        else:
            raise ValueError("Некорректный ответ от API.")
    except Exception as e:
        print(f"Ошибка API: {e}")
        return f"Ошибка при обращении к API: {e}"
