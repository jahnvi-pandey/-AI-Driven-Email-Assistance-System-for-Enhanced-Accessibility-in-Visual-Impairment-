import email
from email.message import EmailMessage
import imaplib
import os
import smtplib
import tempfile
import threading
import time

from gtts import gTTS
import pyglet
import speech_recognition as sr

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "")


def play_audio(text):
    """Play text-to-speech safely."""
    try:
        tts = gTTS(text=text, lang="en")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            temp_path = fp.name

        tts.save(temp_path)
        music = pyglet.media.load(temp_path, streaming=False)
        player = music.play()
        time.sleep(music.duration + 0.2)
        del music
        del player
        try:
            os.remove(temp_path)
        except OSError:
            pass
    except Exception as err:
        print(f"[TTS Error] {err}")


def capture_speech(prompt, status_callback=None):
    """Capture speech input with UI status updates."""
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            if status_callback:
                status_callback(f"Prompt: {prompt}")
            play_audio(prompt)

            if status_callback:
                status_callback("Listening... Speak now.")
            r.adjust_for_ambient_noise(source, duration=0.8)
            audio = r.listen(source, timeout=8, phrase_time_limit=15)

            if status_callback:
                status_callback("Transcribing...")
            text = r.recognize_google(audio)
            return text
    except sr.WaitTimeoutError:
        play_audio("No speech detected.")
        if status_callback:
            status_callback("Timed out: No speech detected.")
        return None
    except sr.UnknownValueError:
        play_audio("Sorry, I did not understand.")
        if status_callback:
            status_callback("Could not understand audio.")
        return None
    except Exception as e:
        print(f"[Mic/Recognition Error] {e}")
        if status_callback:
            status_callback(f"Error: {e}")
        return None


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=20, padding=40)

        self.label = Label(
            text="Voice Email Assistant",
            font_size=32,
            bold=True,
            size_hint=(1, 0.4),
        )
        layout.add_widget(self.label)

        self.compose_button = Button(
            text="Compose Email", font_size=22, size_hint=(1, 0.3)
        )
        self.compose_button.bind(on_release=lambda x: self.navigate_to("compose"))
        layout.add_widget(self.compose_button)

        self.inbox_button = Button(
            text="Check Inbox", font_size=22, size_hint=(1, 0.3)
        )
        self.inbox_button.bind(on_release=lambda x: self.navigate_to("inbox"))
        layout.add_widget(self.inbox_button)

        self.add_widget(layout)

    def navigate_to(self, screen_name):
        self.manager.current = screen_name


class ComposeEmailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=20, padding=40)

        self.status_label = Label(
            text="Initializing Compose Flow...",
            font_size=20,
            halign="center",
            valign="middle",
            size_hint=(1, 0.7),
        )
        self.status_label.bind(size=self.status_label.setter("text_size"))
        layout.add_widget(self.status_label)

        # Start listening button
        self.start_btn = Button(
            text="Start Voice Dictation", font_size=20, size_hint=(1, 0.15)
        )
        self.start_btn.bind(on_release=lambda x: self.start_flow())
        layout.add_widget(self.start_btn)

        # Manual back button so user isn't stuck
        self.back_button = Button(
            text="Back to Menu", font_size=18, size_hint=(1, 0.15)
        )
        self.back_button.bind(on_release=lambda x: self.return_to_menu())
        layout.add_widget(self.back_button)

        self.add_widget(layout)

    def on_enter(self):
        self.update_status("Tap 'Start Voice Dictation' to begin.")

    def update_status(self, text):
        Clock.schedule_once(lambda dt: setattr(self.status_label, "text", text), 0)

    def start_flow(self):
        self.start_btn.disabled = True
        threading.Thread(target=self._handle_compose_flow, daemon=True).start()

    def _handle_compose_flow(self):
        try:
            subject = capture_speech("What is the subject?", self.update_status)
            if not subject:
                self.update_status("No subject captured. Press Start to try again.")
                return

            self.update_status(f"Subject: {subject}")
            body = capture_speech("Please dictate the email body.", self.update_status)
            if not body:
                self.update_status("No body captured. Press Start to try again.")
                return

            self.update_status("Sending email...")
            self.send_email(subject, body)
        finally:
            Clock.schedule_once(lambda dt: setattr(self.start_btn, "disabled", False), 0)

    def send_email(self, subject, body):
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            self.update_status("Credentials missing in environment variables.")
            return

        msg = EmailMessage()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = subject
        msg.set_content(f"Dear Sir/Madam,\n\n{body}\n\nBest regards.")

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            self.update_status("Email sent successfully!")
            play_audio("Email sent successfully.")
        except Exception as e:
            self.update_status(f"SMTP Error: {e}")
            play_audio("Failed to send email.")

    def return_to_menu(self, *args):
        self.manager.current = "menu"


class CheckInboxScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=20, padding=40)

        self.status_label = Label(
            text="Inbox",
            font_size=20,
            halign="center",
            valign="middle",
            size_hint=(1, 0.7),
        )
        self.status_label.bind(size=self.status_label.setter("text_size"))
        layout.add_widget(self.status_label)

        self.fetch_btn = Button(
            text="Fetch Recent Emails", font_size=20, size_hint=(1, 0.15)
        )
        self.fetch_btn.bind(on_release=lambda x: self.start_fetch())
        layout.add_widget(self.fetch_btn)

        self.back_button = Button(
            text="Back to Menu", font_size=18, size_hint=(1, 0.15)
        )
        self.back_button.bind(on_release=lambda x: self.return_to_menu())
        layout.add_widget(self.back_button)

        self.add_widget(layout)

    def on_enter(self):
        self.update_status("Tap 'Fetch Recent Emails' to read inbox.")

    def update_status(self, text):
        Clock.schedule_once(lambda dt: setattr(self.status_label, "text", text), 0)

    def start_fetch(self):
        self.fetch_btn.disabled = True
        threading.Thread(target=self._fetch_inbox, daemon=True).start()

    def _fetch_inbox(self):
        try:
            if not SENDER_EMAIL or not SENDER_PASSWORD:
                self.update_status("Email credentials not configured.")
                return

            self.update_status("Connecting to IMAP...")
            with imaplib.IMAP4_SSL("imap.gmail.com") as mail:
                mail.login(SENDER_EMAIL, SENDER_PASSWORD)
                mail.select("inbox")

                status, messages = mail.search(None, "ALL")
                if status != "OK" or not messages[0]:
                    self.update_status("No emails found.")
                    play_audio("No emails found.")
                    return

                email_ids = messages[0].split()[-3:]
                for num in reversed(email_ids):
                    status, data = mail.fetch(num, "(RFC822)")
                    if status != "OK":
                        continue

                    msg = email.message_from_bytes(data[0][1])
                    sender = msg.get("From", "Unknown")
                    subject = msg.get("Subject", "No Subject")

                    self.update_status(f"From: {sender}\nSubject: {subject}")
                    play_audio(f"From: {sender}. Subject: {subject}")
        except Exception as e:
            self.update_status(f"IMAP Error: {e}")
            play_audio("Failed to fetch inbox.")
        finally:
            Clock.schedule_once(lambda dt: setattr(self.fetch_btn, "disabled", False), 0)

    def return_to_menu(self, *args):
        self.manager.current = "menu"


class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(ComposeEmailScreen(name="compose"))
        sm.add_widget(CheckInboxScreen(name="inbox"))
        sm.current = "menu"
        return sm

if __name__ == "__main__":
    MyApp().run()
