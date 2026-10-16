import customtkinter as ctk
import threading
import math
import time

from . import graph
from . import voice
from .graph import run_jarvis
from .voice import listen, speak


class JarvisGUI:

    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.app = ctk.CTk()
        self.app.title("JARVIS AI Assistant")
        self.app.geometry("800x600")
        self.app.minsize(700, 500)

        self.is_processing = False
        self.is_listening = False
        self.is_stopped = False
        self.is_speaking = False

        self.message_labels = []
        self.request_id = 0
        self.closing = False

        self.build_ui()
        self.animate_orb()

        self.add_message(
            "JARVIS online. How can I help you?",
            "jarvis"
        )

        self.app.protocol("WM_DELETE_WINDOW", self.close_app)

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):
        self.app.grid_columnconfigure(1, weight=1)
        self.app.grid_rowconfigure(0, weight=1)

        # SIDEBAR
        self.sidebar = ctk.CTkFrame(
            self.app,
            width=265,
            corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.logo = ctk.CTkLabel(
            self.sidebar,
            text="J.A.R.V.I.S",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.logo.pack(pady=(25, 5))

        self.logo_subtitle = ctk.CTkLabel(
            self.sidebar,
            text="PERSONAL AI OPERATING ASSISTANT",
            font=ctk.CTkFont(size=10)
        )
        self.logo_subtitle.pack(pady=(0, 15))

        # ORB
        self.orb = ctk.CTkCanvas(
            self.sidebar,
            width=180,
            height=180,
            bg="#1a1a1a",
            highlightthickness=0
        )
        self.orb.pack(pady=5)

        # STATUS
        self.status_card = ctk.CTkFrame(
            self.sidebar,
            corner_radius=12
        )
        self.status_card.pack(
            padx=18,
            pady=12,
            fill="x"
        )

        self.status_title = ctk.CTkLabel(
            self.status_card,
            text="SYSTEM STATUS",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.status_title.pack(pady=(10, 2))

        self.status_label = ctk.CTkLabel(
            self.status_card,
            text="● ONLINE",
            text_color="#00ff88",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.status_label.pack(pady=(0, 10))

        # TELEMETRY
        self.telemetry = ctk.CTkLabel(
            self.sidebar,
            text=(
                "CORE: ONLINE\n"
                "MEMORY: READY\n"
                "TOOLS: READY\n"
                "VOICE: READY"
            ),
            justify="left",
            font=ctk.CTkFont(size=11)
        )
        self.telemetry.pack(
            padx=25,
            pady=10,
            anchor="w"
        )

        # CLEAR CHAT
        self.sidebar_button = ctk.CTkButton(
            self.sidebar,
            text="CLEAR CHAT",
            command=self.clear_chat
        )
        self.sidebar_button.pack(
            padx=18,
            pady=(10, 5),
            fill="x"
        )

        # MAIN AREA
        self.main = ctk.CTkFrame(
            self.app,
            corner_radius=0
        )
        self.main.grid(row=0, column=1, sticky="nsew")

        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        # HEADER
        self.header = ctk.CTkFrame(
            self.main,
            height=65,
            corner_radius=0
        )
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.header_title = ctk.CTkLabel(
            self.header,
            text="JARVIS",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.header_title.grid(
            row=0,
            column=0,
            padx=20,
            pady=18,
            sticky="w"
        )

        self.header_status = ctk.CTkLabel(
            self.header,
            text="READY",
            text_color="#00ff88",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.header_status.grid(
            row=0,
            column=1,
            padx=20,
            pady=18
        )

        # CHAT
        self.chat_content = ctk.CTkScrollableFrame(
            self.main,
            corner_radius=0
        )
        self.chat_content.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=8,
            pady=5
        )
        self.chat_content.grid_columnconfigure(0, weight=1)

        # BOTTOM
        self.bottom = ctk.CTkFrame(
            self.main,
            corner_radius=0
        )
        self.bottom.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=10,
            pady=10
        )
        self.bottom.grid_columnconfigure(0, weight=1)

        self.input_box = ctk.CTkEntry(
            self.bottom,
            placeholder_text="Ask JARVIS anything..."
        )
        self.input_box.grid(
            row=0,
            column=0,
            padx=(0, 8),
            pady=5,
            sticky="ew"
        )
        self.input_box.bind("<Return>", self.send_message)

        self.send_button = ctk.CTkButton(
            self.bottom,
            text="SEND",
            width=75,
            command=self.send_message
        )
        self.send_button.grid(
            row=0,
            column=1,
            padx=4,
            pady=5
        )

        self.mic_button = ctk.CTkButton(
            self.bottom,
            text="🎤 MIC",
            width=85,
            command=self.start_voice_input
        )
        self.mic_button.grid(
            row=0,
            column=2,
            padx=(4, 0),
            pady=5
        )

        self.stop_button = ctk.CTkButton(
            self.bottom,
            text="■ STOP",
            width=85,
            fg_color="#d62828",
            hover_color="#9d0208",
            command=self.stop_jarvis
        )
        self.stop_button.grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        # PROCESSING LABEL
        self.processing_label = ctk.CTkLabel(
            self.main,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.processing_label.grid(
            row=3,
            column=0,
            pady=(0, 5)
        )

    # =====================================================
    # MESSAGE
    # =====================================================

    def add_message(self, message, sender="jarvis"):
        if self.closing:
            return

        message = str(message)

        message_frame = ctk.CTkFrame(
            self.chat_content,
            corner_radius=12
        )
        message_frame.grid(
            row=len(self.message_labels),
            column=0,
            padx=8,
            pady=6,
            sticky="ew"
        )
        message_frame.grid_columnconfigure(0, weight=1)

        if sender == "user":
            sender_text = "YOU"
            sender_color = "#4da6ff"
        else:
            sender_text = "JARVIS"
            sender_color = "#00ff88"

        sender_label = ctk.CTkLabel(
            message_frame,
            text=sender_text,
            text_color=sender_color,
            font=ctk.CTkFont(size=10, weight="bold")
        )
        sender_label.grid(
            row=0,
            column=0,
            padx=12,
            pady=(8, 2),
            sticky="w"
        )

        message_label = ctk.CTkLabel(
            message_frame,
            text=message,
            justify="left",
            anchor="w",
            wraplength=520,
            font=ctk.CTkFont(size=13)
        )
        message_label.grid(
            row=1,
            column=0,
            padx=12,
            pady=(2, 8),
            sticky="ew"
        )

        copy_button = ctk.CTkButton(
            message_frame,
            text="COPY",
            width=55,
            height=24,
            font=ctk.CTkFont(size=9),
            command=lambda m=message: self.copy_message(m)
        )
        copy_button.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=8
        )

        self.message_labels.append((message_label, sender))

        self.app.after(50, self.scroll_chat_bottom)

    # =====================================================
    # COPY
    # =====================================================

    def copy_message(self, message):
        try:
            self.app.clipboard_clear()
            self.app.clipboard_append(str(message))
            self.processing_label.configure(text="Message copied.")

            self.app.after(
                1200,
                lambda: self.safe_configure(
                    self.processing_label,
                    text=""
                )
            )
        except Exception as error:
            print(f"Copy error: {error}")

    # =====================================================
    # SAFE UI UPDATE
    # =====================================================

    def safe_configure(self, widget, **kwargs):
        if self.closing:
            return

        try:
            widget.configure(**kwargs)
        except Exception:
            pass

    # =====================================================
    # SCROLL
    # =====================================================

    def scroll_chat_bottom(self):
        if self.closing:
            return

        try:
            canvas = self.chat_content._parent_canvas
            canvas.update_idletasks()
            canvas.yview_moveto(1.0)
        except Exception:
            pass

    # =====================================================
    # CLEAR CHAT
    # =====================================================

    def clear_chat(self):
        if self.closing:
            return

        for widget in self.chat_content.winfo_children():
            widget.destroy()

        self.message_labels.clear()

        self.add_message(
            "Chat cleared. How can I help you?",
            "jarvis"
        )

    # =====================================================
    # BUTTON STATES
    # =====================================================

    def set_busy(self, busy):
        if self.closing:
            return

        self.is_processing = busy

        state = "disabled" if busy else "normal"

        self.send_button.configure(state=state)
        self.mic_button.configure(
            state="disabled" if busy or self.is_listening else "normal",
            text="🎤 LISTENING..." if self.is_listening else "🎤 MIC"
        )
        self.input_box.configure(state=state)

        if busy:
            self.status_label.configure(
                text="● PROCESSING",
                text_color="#ffaa00"
            )
            self.header_status.configure(
                text="PROCESSING",
                text_color="#ffaa00"
            )
        else:
            self.status_label.configure(
                text="● ONLINE",
                text_color="#00ff88"
            )
            self.header_status.configure(
                text="READY",
                text_color="#00ff88"
            )

    # =====================================================
    # SEND TEXT
    # =====================================================

    def send_message(self, event=None):
        if self.closing or self.is_processing or self.is_listening:
            return

        text = self.input_box.get().strip()

        if not text:
            return

        self.input_box.delete(0, "end")
        self.add_message(text, "user")

        self.process_request_async(
            text,
            speak_response=False
        )

    # =====================================================
    # VOICE INPUT
    # =====================================================

    def start_voice_input(self):
        if self.closing or self.is_processing or self.is_listening:
            return

        self.is_listening = True
        self.is_stopped = False

        self.mic_button.configure(
            text="🎤 LISTENING...",
            state="disabled"
        )
        self.send_button.configure(state="disabled")
        self.input_box.configure(state="disabled")

        self.status_label.configure(
            text="● LISTENING",
            text_color="#ffaa00"
        )
        self.header_status.configure(
            text="LISTENING",
            text_color="#ffaa00"
        )
        self.processing_label.configure(text="Speak now...")

        threading.Thread(
            target=self.voice_worker,
            args=(self.request_id,),
            daemon=True
        ).start()

    # =====================================================
    # VOICE WORKER
    # =====================================================

    def voice_worker(self, request_id):
        try:
            text = listen()

            if self.closing or self.is_stopped:
                return

            if not text:
                self.app.after(
                    0,
                    lambda rid=request_id: self.voice_finished(rid)
                )
                return

            self.app.after(
                0,
                lambda t=text, rid=request_id:
                self.handle_voice_text(t, rid)
            )

        except Exception as error:
            if not self.closing and not self.is_stopped:
                self.app.after(
                    0,
                    lambda e=error, rid=request_id:
                    self.show_voice_error(e, rid)
                )

    def handle_voice_text(self, text, request_id):
        if self.closing or self.is_stopped:
            return

        if request_id != self.request_id:
            return

        self.is_listening = False

        self.add_message(text, "user")

        self.process_request_async(
            text,
            speak_response=True
        )

    # =====================================================
    # VOICE FINISHED
    # =====================================================

    def voice_finished(self, request_id=None):
        if self.closing:
            return

        if request_id is not None and request_id != self.request_id:
            return

        self.is_listening = False

        self.mic_button.configure(
            text="🎤 MIC",
            state="normal"
        )
        self.send_button.configure(state="normal")
        self.input_box.configure(state="normal")

        if not self.is_processing:
            self.status_label.configure(
                text="● ONLINE",
                text_color="#00ff88"
            )
            self.header_status.configure(
                text="READY",
                text_color="#00ff88"
            )
            self.processing_label.configure(text="")

    # =====================================================
    # VOICE ERROR
    # =====================================================

    def show_voice_error(self, error, request_id=None):
        if self.closing or self.is_stopped:
            return

        if request_id is not None and request_id != self.request_id:
            return

        print(f"Voice GUI error: {error}")

        self.voice_finished(request_id)

        self.add_message(
            "I could not process the voice input. Please try again.",
            "jarvis"
        )

    # =====================================================
    # PROCESS REQUEST ASYNC
    # =====================================================

    def process_request_async(self, text, speak_response=False):
        if self.closing or self.is_processing:
            return

        self.is_stopped = False
        self.request_id += 1
        request_id = self.request_id

        self.set_busy(True)
        self.processing_label.configure(text="JARVIS is thinking...")

        threading.Thread(
            target=self.process_request,
            args=(text, speak_response, request_id),
            daemon=True
        ).start()

    # =====================================================
    # PROCESS REQUEST
    # =====================================================

    def process_request(self, text, speak_response=False, request_id=None):
        try:
            result = run_jarvis(text)

            if self.closing or self.is_stopped:
                return

            if request_id != self.request_id:
                return

            if isinstance(result, tuple) and len(result) > 1:
                if result[1] is not None:
                    graph.PENDING_ACTION = result[1]

            self.app.after(
                0,
                lambda r=result, sv=speak_response, rid=request_id:
                self.show_result(r, sv, rid)
            )

        except Exception as error:
            if self.closing or self.is_stopped:
                return

            self.app.after(
                0,
                lambda e=error, rid=request_id:
                self.show_error(e, rid)
            )

    # =====================================================
    # SHOW RESULT
    # =====================================================

    def show_result(self, result, speak_response=False, request_id=None):
        if self.closing or self.is_stopped:
            return

        if request_id is not None and request_id != self.request_id:
            return

        if isinstance(result, tuple):
            result_text = str(result[0])
        else:
            result_text = str(result)

        self.add_message(result_text, "jarvis")

        if speak_response:
            self.is_speaking = True

            threading.Thread(
                target=self.speak_response,
                args=(result_text, request_id),
                daemon=True
            ).start()
        else:
            self.finish_processing(request_id)

    # =====================================================
    # SPEAK RESPONSE
    # =====================================================

    def speak_response(self, text, request_id=None):
        try:
            if self.closing or self.is_stopped:
                return

            self.app.after(
                0,
                lambda: self.safe_configure(
                    self.processing_label,
                    text="JARVIS is speaking..."
                )
            )

            speak(text)

        except Exception as error:
            print(f"Speech error: {error}")

        finally:
            self.is_speaking = False

            if not self.closing:
                try:
                    self.app.after(
                        0,
                        lambda rid=request_id:
                        self.finish_processing(rid)
                    )
                except Exception:
                    pass

    # =====================================================
    # STOP
    # =====================================================

    def stop_jarvis(self):
        if self.closing:
            return

        # Invalidate pending results and callbacks.
        self.is_stopped = True
        self.request_id += 1

        self.is_processing = False
        self.is_listening = False
        self.is_speaking = False

        # Try stopping speech if voice.py exposes a stop function.
        try:
            stop_function = getattr(voice, "stop_speaking", None)

            if callable(stop_function):
                threading.Thread(
                    target=stop_function,
                    daemon=True
                ).start()
            else:
                engine = getattr(voice, "engine", None)

                if engine is not None and hasattr(engine, "stop"):
                    threading.Thread(
                        target=engine.stop,
                        daemon=True
                    ).start()
        except Exception as error:
            print(f"Stop speech error: {error}")

        self.is_processing = False
        self.is_listening = False

        self.send_button.configure(state="normal")
        self.mic_button.configure(
            text="🎤 MIC",
            state="normal"
        )
        self.input_box.configure(state="normal")

        self.status_label.configure(
            text="● STOPPED",
            text_color="#ff4444"
        )
        self.header_status.configure(
            text="STOPPED",
            text_color="#ff4444"
        )
        self.processing_label.configure(
            text="Stopped. You can send a new command."
        )

    # =====================================================
    # ERROR
    # =====================================================

    def show_error(self, error, request_id=None):
        if self.closing or self.is_stopped:
            return

        if request_id is not None and request_id != self.request_id:
            return

        self.add_message(f"Error: {error}", "jarvis")
        self.finish_processing(request_id)

    # =====================================================
    # FINISH PROCESSING
    # =====================================================

    def finish_processing(self, request_id=None):
        if self.closing or self.is_stopped:
            return

        if request_id is not None and request_id != self.request_id:
            return

        self.is_processing = False
        self.is_listening = False
        self.is_speaking = False

        self.send_button.configure(state="normal")
        self.mic_button.configure(
            text="🎤 MIC",
            state="normal"
        )
        self.input_box.configure(state="normal")

        self.status_label.configure(
            text="● ONLINE",
            text_color="#00ff88"
        )
        self.header_status.configure(
            text="READY",
            text_color="#00ff88"
        )
        self.processing_label.configure(text="")
        self.input_box.focus_set()

    # =====================================================
    # CONFIRMATION
    # =====================================================

    def confirm_action(self, answer):
        if self.is_processing or self.is_listening:
            return

        self.add_message(answer, "user")
        self.process_request_async(answer, speak_response=False)

    # =====================================================
    # QUICK COMMAND
    # =====================================================

    def quick_command(self, command):
        if self.is_processing or self.is_listening:
            return

        self.add_message(command, "user")
        self.process_request_async(command, speak_response=False)

    # =====================================================
    # ORB ANIMATION
    # =====================================================

    def animate_orb(self):
        if self.closing:
            return

        try:
            self.orb.delete("all")

            width = 180
            height = 180

            center_x = width / 2
            center_y = height / 2

            pulse = math.sin(time.time() * 3)
            radius = 42 + pulse * 2

            self.orb.create_oval(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                outline="#00aaff",
                width=3
            )

            self.orb.create_oval(
                center_x - 30,
                center_y - 30,
                center_x + 30,
                center_y + 30,
                fill="#0b2a3d",
                outline="#00ffcc",
                width=2
            )

            self.orb.create_text(
                center_x,
                center_y,
                text="J",
                fill="#00ffcc",
                font=("Arial", 28, "bold")
            )

        except Exception:
            pass

        if not self.closing:
            self.app.after(100, self.animate_orb)

    # =====================================================
    # CLOSE APP
    # =====================================================

    def close_app(self):
        self.closing = True
        self.is_stopped = True

        try:
            stop_function = getattr(voice, "stop_speaking", None)

            if callable(stop_function):
                threading.Thread(
                    target=stop_function,
                    daemon=True
                ).start()
        except Exception:
            pass

        try:
            self.app.destroy()
        except Exception:
            pass

    # =====================================================
    # RUN
    # =====================================================

    def run(self):
        self.app.mainloop()


# =========================================================
# LAUNCH
# =========================================================

def launch_gui():
    app = JarvisGUI()
    app.run()


if __name__ == "__main__":
    launch_gui()