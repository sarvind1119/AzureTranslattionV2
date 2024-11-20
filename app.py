import os
import tkinter as tk
from tkinter import ttk
import azure.cognitiveservices.speech as speechsdk
import threading

class LiveTranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Live Speech Translation")
        self.root.geometry("700x500")

        self.is_translating = False  # Track the state of translation
        self.font_size = 12  # Default font size

        # Setup UI components
        self.setup_ui()

    def setup_ui(self):
        # Dropdown for input language
        tk.Label(self.root, text="Select Input Language:").pack(pady=10)
        self.input_language_var = tk.StringVar()
        self.input_language_dropdown = ttk.Combobox(self.root, textvariable=self.input_language_var, state="readonly")
        self.input_language_dropdown['values'] = ["Hindi (India)"]
        self.input_language_dropdown.current(0)
        self.input_language_dropdown.pack()

        # Dropdown for output language
        tk.Label(self.root, text="Select Output Language:").pack(pady=10)
        self.output_language_var = tk.StringVar()
        self.output_language_dropdown = ttk.Combobox(self.root, textvariable=self.output_language_var, state="readonly")
        self.output_language_dropdown['values'] = ["English (Text)"]
        self.output_language_dropdown.current(0)
        self.output_language_dropdown.pack()

        # Font size selector
        tk.Label(self.root, text="Select Font Size:").pack(pady=10)
        self.font_size_var = tk.IntVar(value=self.font_size)
        self.font_size_dropdown = ttk.Combobox(self.root, textvariable=self.font_size_var, state="readonly")
        self.font_size_dropdown['values'] = [12, 14, 16, 18, 20, 24, 28, 32, 36, 40]  # Available font sizes
        self.font_size_dropdown.bind("<<ComboboxSelected>>", self.change_font_size)
        self.font_size_dropdown.pack()

        # Buttons for starting and ending translation
        self.start_button = tk.Button(self.root, text="Start Translation", command=self.start_translation)
        self.start_button.pack(pady=10)

        self.end_button = tk.Button(self.root, text="End Translation", command=self.end_translation)
        self.end_button.pack(pady=10)

        # Text box to display translations
        self.translation_display = tk.Text(self.root, wrap=tk.WORD, height=10, width=60, font=("Helvetica", self.font_size))
        self.translation_display.pack(pady=20)

    def change_font_size(self, event=None):
        """Update font size for the translation display."""
        self.font_size = self.font_size_var.get()
        self.translation_display.config(font=("Helvetica", self.font_size))

    def start_translation(self):
        """Start translation in a new thread."""
        if not self.is_translating:
            self.is_translating = True
            self.start_button.config(state="disabled")  # Disable Start Button
            self.end_button.config(state="normal")  # Enable End Button
            threading.Thread(target=self.recognize_from_microphone, daemon=True).start()

    def end_translation(self):
        """End translation."""
        self.is_translating = False
        self.start_button.config(state="normal")  # Enable Start Button
        self.end_button.config(state="disabled")  # Disable End Button

    def recognize_from_microphone(self):
        """Continuous speech translation method."""
        # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
        speech_translation_config = speechsdk.translation.SpeechTranslationConfig(
            subscription=os.environ.get('SPEECH_KEY'),
            region=os.environ.get('SPEECH_REGION')
        )

        input_lang = "hi-IN"  # Hindi language
        output_lang = "en"   # Translate to English
        speech_translation_config.speech_recognition_language = input_lang
        speech_translation_config.add_target_language(output_lang)

        # Set up microphone input
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        translation_recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=speech_translation_config,
            audio_config=audio_config
        )

        # Event handler for recognized speech
        def handle_translation_result(evt):
            if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                translation = evt.result.translations[output_lang]
                print(f"Recognized: {evt.result.text}")
                print(f"Translated into '{output_lang}': {translation}")
                if self.is_translating:
                    self.update_translation_display(translation)
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                print("No speech could be recognized.")
            elif evt.result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = evt.result.cancellation_details
                print(f"Speech Recognition canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print(f"Error details: {cancellation_details.error_details}")
                    print("Did you set the speech resource key and region values?")

        # Attach the event handler
        translation_recognizer.recognized.connect(handle_translation_result)

        # Start continuous recognition
        print("Starting continuous translation. Speak into your microphone in Hindi.")
        translation_recognizer.start_continuous_recognition()

        # Keep running the recognition until stopped
        while self.is_translating:
            pass

        # Stop recognition when the user stops the translation
        translation_recognizer.stop_continuous_recognition()

    def update_translation_display(self, translation):
        """Update the text box with the translated text."""
        self.translation_display.insert(tk.END, f"{translation}\n")
        self.translation_display.yview(tk.END)  # Scroll to the bottom to show the latest translation


# Initialize the Tkinter window
root = tk.Tk()
app = LiveTranslationApp(root)

# Run the Tkinter main loop
root.mainloop()
