import os
import time
import smtplib
import imaplib
from gtts import gTTs
import pyglet
import speech_recognition as sr
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from email.parser import BytesParser
from email.policy import default

# Global email credentials
SENDER_EMAIL = "pandeyharshmohan3@gmail.com"
SENDER_PASSWORD = "vjax bais pzmu swmf"
RECIPIENT_EMAIL = "anmolnothing@gmail.com"


def play_audio(text):
    """Play text-to-speech."""
    tts = gTTS(text=text, lang='en')
    ttsname = "temp_audio.mp3"
    tts.save(ttsname)
    music = pyglet.media.load(ttsname, streaming=False)
    music.play()
    time.sleep(music.duration)
    os.remove(ttsname)


def capture_speech(prompt):
    """Capture speech input."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        play_audio(prompt)
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
        try:
            return r.recognize_google(audio)
        except sr.UnknownValueError:
            play_audio("Sorry, I did not understand.")
            return None
        except sr.RequestError:
            play_audio("Speech recognition service is unavailable.")
            return None


class MenuScreen(Screen):
    """Main menu screen."""

    def _init_(self, **kwargs):
        super()._init_(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=20)

        self.label = Label(text="Voice Email Assistant", font_size=30, bold=True, size_hint=(1, 0.3))
        self.layout.add_widget(self.label)

        self.compose_button = Button(text="Compose Email", font_size=24, size_hint=(1, 0.2))
        self.compose_button.bind(on_release=lambda x: self.navigate_to("compose"))
        self.layout.add_widget(self.compose_button)

        self.inbox_button = Button(text="Check Inbox", font_size=24, size_hint=(1, 0.2))
        self.inbox_button.bind(on_release=lambda x: self.navigate_to("inbox"))
        self.layout.add_widget(self.inbox_button)

        self.add_widget(self.layout)
        Clock.schedule_once(self.listen_for_action, 1)

    def listen_for_action(self, dt):
        action = capture_speech("Say 'Compose Email' or 'Check Inbox'.")
        if action:
            action = action.lower()
            if "compose" in action:
                self.navigate_to("compose")
            elif "inbox" in action:
                self.navigate_to("inbox")
            else:
                play_audio("Sorry, I didn't understand. Please try again.")
                self.listen_for_action(None)

    def navigate_to(self, screen_name):
        self.manager.current = screen_name


class ComposeEmailScreen(Screen):
    """Screen for composing an email."""

    def _init_(self, **kwargs):
        super()._init_(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=20)

        layout.add_widget(Label(text="Compose Email", font_size=30, bold=True, size_hint=(1, 0.2)))
        self.add_widget(layout)

    def on_enter(self):
        # Capture the subject of the email
        play_audio("Please dictate the subject of your email.")
        subject = capture_speech("What is the subject of the email?")
        if not subject:
            play_audio("No subject captured. Please try again.")
            return

        # Capture the body of the email
        play_audio("Please dictate the body of your email.")
        message = capture_speech("Start speaking your message.")
        if message:
            formatted_message = self.format_email(subject, message)
            self.send_email(subject, formatted_message)
        else:
            play_audio("No message captured. Please try again.")

    def format_email(self, subject, message):
        """Format the email with a subject, greeting, and regards."""
        greeting = "Dear Sir/Madam,\n\n"
        closing = "\n\nBest regards,\nHarsh Mohan Pandey"
        return f"Subject: {subject}\n\n{greeting}{message}{closing}"

    def send_email(self, subject, formatted_message):
        """Send the email with the subject and formatted message."""
        try:
            mail = smtplib.SMTP('smtp.gmail.com', 587)
            mail.starttls()
            mail.login(SENDER_EMAIL, SENDER_PASSWORD)
            mail.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, formatted_message)
            mail.close()
            play_audio("Email sent successfully.")
            # Wait for 5 seconds and return to main menu
            Clock.schedule_once(self.return_to_menu, 5)
        except Exception as e:
            play_audio("Failed to send the email.")
            print(f"Error: {e}")

    def return_to_menu(self, dt):
        """Navigate back to the main menu after task completion."""
        self.manager.current = "menu"


class CheckInboxScreen(Screen):
    """Screen for checking the inbox."""

    def _init_(self, **kwargs):
        super()._init_(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=20)

        layout.add_widget(Label(text="Check Inbox", font_size=30, bold=True, size_hint=(1, 0.2)))
        self.add_widget(layout)

    def on_enter(self):
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(SENDER_EMAIL, SENDER_PASSWORD)
            mail.select("inbox")

            status, messages = mail.search(None, 'ALL')
            if status != "OK":
                play_audio("Unable to fetch emails.")
                return

            emails = messages[0].split()[-5:]  # Get the last 5 emails
            for num in emails:
                status, data = mail.fetch(num, '(RFC822)')
                if status == "OK":
                    # Parse the email content
                    email_msg = BytesParser(policy=default).parsebytes(data[0][1])

                    # Get the 'From' and 'Subject'
                    from_email = email_msg["From"]
                    subject = email_msg["Subject"]

                    # Get the body of the email
                    body = ""
                    if email_msg.is_multipart():
                        for part in email_msg.iter_parts():
                            if part.get_content_type() == "text/plain":
                                body += part.get_payload(decode=True).decode()
                    else:
                        body = email_msg.get_payload(decode=True).decode()

                    play_audio(f"From: {from_email}")
                    play_audio(f"Subject: {subject}")
                    play_audio(f"Body: {body[:200]}")  # Read first 200 characters of the body

            mail.close()
            mail.logout()
            # Wait for 5 seconds and return to main menu
            Clock.schedule_once(self.return_to_menu, 5)
        except Exception as e:
            play_audio("Failed to check the inbox.")
            print(f"Error: {e}")

    def return_to_menu(self, dt):
        """Navigate back to the main menu after task completion."""
        self.manager.current = "menu"


class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(ComposeEmailScreen(name="compose"))
        sm.add_widget(CheckInboxScreen(name="inbox"))
        sm.current = "menu"
        return sm


if _name_ == "_main_":
    MyApp().run()