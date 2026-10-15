# AI-Powered Email Listening and Response System for the Visually Impaired

An accessible, hands-free email communication client engineered to provide independent email autonomy for visually impaired and low-vision individuals. 

The system leverages Speech-to-Text (STT) for voice command interpretation and email dictation, coupled with Text-to-Speech (TTS) for reading inbox contents aloud—bypassing traditional visual screen readers with a continuous conversational interface.

---

## Table of Contents

- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Voice Interaction Guide](#voice-interaction-guide)
- [Project Structure](#project-structure)
- [Limitations & Troubleshooting](#limitations--troubleshooting)
- [Future Roadmap](#future-roadmap)
- [License](#license)

---

## Key Features

- **Hands-Free Navigation:** Complete voice-driven menu navigation without requiring tactile mouse or keyboard input.
- **Guided Voice Email Composition:** Step-by-step interactive voice prompts capture recipient, subject line, and body message with audio review before transmission.
- **Audio Inbox Reader:** Retrieves incoming emails via secure IMAP, extracts plain-text bodies from complex MIME payloads, and reads sender, subject, and preview information aloud.
- **High-Contrast Dual Interface:** Simple, accessible visual interface with large touch/click targets and real-time textual status feedback for low-vision users and caregivers.
- **Zero-Disk Audio Pipeline:** Efficient TTS streaming designed to prevent temporary file locks and platform-specific audio driver conflicts.

---

## System Architecture

```
                       +-----------------------+
                       |  User (Voice Input)   |
                       +-----------------------+
                                   |
                                   v
                       +-----------------------+
                       | Speech-to-Text (STT)  |
                       | Google SR / PyAudio   |
                       +-----------------------+
                                   |
                     +-------------+-------------+
                     |                           |
                     v                           v
          [Command: "Compose"]          [Command: "Inbox"]
                     |                           |
                     v                           v
          +--------------------+      +--------------------+
          | Multi-Step Voice   |      | Secure IMAP Engine |
          | Dictation Pipeline |      | (Port 993 - TLS)   |
          +--------------------+      +--------------------+
                     |                           |
                     v                           v
          +--------------------+      +--------------------+
          | Secure SMTP Engine |      | Plaintext Payload  |
          | (Port 587 - TLS)   |      | Parser (RFC 822)   |
          +--------------------+      +--------------------+
                     |                           |
                     v                           v
          +--------------------+      +--------------------+
          |  Target Mailbox    |      | Text-to-Speech TTS |
          |  (Email Sent)      |      | (gTTS / Audio Out) |
          +--------------------+      +--------------------+
```

---

## Tech Stack

- **Core Runtime:** Python 3.10+
- **Graphical User Interface:** Kivy
- **Speech-to-Text (STT):** `SpeechRecognition` (Google Speech API backend)
- **Text-to-Speech (TTS):** `gTTS` (Google Text-to-Speech), `pyglet` / `pygame` audio playback
- **Audio I/O Driver:** `PyAudio`
- **Mail Protocols:** `smtplib` (SMTP STARTTLS), `imaplib` (IMAP SSL/TLS), Python `email` package

---

## Prerequisites

Before setting up the project, make sure you have:

1. **Python 3.10 or higher** installed on your system.
2. A working **microphone** and **speakers/headphones**.
3. A Gmail account with **2-Factor Authentication (2FA)** enabled to generate a **16-character App Password** (standard Gmail passwords will be rejected by Google's SMTP/IMAP servers).

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/voice-email-assistant.git
cd voice-email-assistant
```

### 2. Create and Activate a Virtual Environment
- **On Windows:**
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```
- **On macOS/Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Audio Dependencies

#### Windows:
```bash
pip install pyaudio
```
*(If `pip install pyaudio` fails, run `pip install pipwin && pipwin install pyaudio`)*

#### Linux (Debian/Ubuntu):
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev libasound2-dev
pip install pyaudio
```

#### macOS:
```bash
brew install portaudio
pip install pyaudio
```

### 4. Install Required Python Packages
```bash
pip install -r requirements.txt
```

*If you do not have a `requirements.txt` file yet, install directly:*
```bash
pip install kivy gtts speechrecognition pyglet pygame
```

---

## Configuration

Set your email credentials as environment variables. **Never commit sensitive passwords directly into source code.**

### Linux / macOS:
```bash
export SENDER_EMAIL="your_email@gmail.com"
export SENDER_APP_PASSWORD="xxxx xxxx xxxx xxxx"   # 16-character App Password
export RECIPIENT_EMAIL="recipient@gmail.com"
```

### Windows (Command Prompt):
```cmd
set SENDER_EMAIL=your_email@gmail.com
set SENDER_APP_PASSWORD=xxxx xxxx xxxx xxxx
set RECIPIENT_EMAIL=recipient@gmail.com
```

### Windows (PowerShell):
```powershell
$env:SENDER_EMAIL="your_email@gmail.com"
$env:SENDER_APP_PASSWORD="xxxx xxxx xxxx xxxx"
$env:RECIPIENT_EMAIL="recipient@gmail.com"
```

> **Note on Gmail App Passwords:** Go to your **Google Account > Security > 2-Step Verification > App passwords**, generate a password for "Mail", and paste the 16-character token into `SENDER_APP_PASSWORD`.

---

## Running the Application

Execute the main entry script:

```bash
python main.py
```

---

## Voice Interaction Guide

| Screen | System Prompt | Expected Spoken Input | Action |
| :--- | :--- | :--- | :--- |
| **Main Menu** | *"Say 'Compose Email' or 'Check Inbox'"* | `"Compose"` or `"Compose Email"` | Opens email composer |
| **Main Menu** | *"Say 'Compose Email' or 'Check Inbox'"* | `"Inbox"` or `"Check Inbox"` | Opens inbox reader |
| **Compose** | *"What is the subject of the email?"* | Any text (e.g., *"Project Update"*) | Sets email subject line |
| **Compose** | *"Please dictate the body of your email"* | Your desired message text | Sets message body & sends via SMTP |
| **Inbox** | Audio readout | None (automated playback) | Reads latest 3 emails sequentially |

---

## Project Structure

```plaintext
voice-email-assistant/
│
├── main.py                  # Core Kivy GUI and asynchronous event controller
├── requirements.txt         # Project dependencies
├── README.md                # System documentation
└── assets/                  # Icons, sound effects, or supplemental UI assets
```

---

## Limitations & Troubleshooting

- **Microphone Access Blocked (Windows):** Ensure desktop microphone access is allowed under *Windows Settings > Privacy & Security > Microphone*.
- **Ambient Noise Sensitivity:** In loud environments, Google Speech Recognition may fail or capture erroneous terms. The system recalibrates using ambient noise detection before each recording turn.
- **Complex HTML Email Bodies:** Marketing newsletters with large tables, CSS, and inline tracking scripts are filtered down to text-only segments to prevent synthesizer confusion.
- **Network Dependency:** Requires an active internet connection for Google STT and gTTS synthesis.

---

## Future Roadmap

- [ ] **Offline Voice Engine:** Integrate offline STT/TTS (e.g., Vosk, Whisper.cpp, `pyttsx3`) for local, private operation without internet.
- [ ] **AI-Powered Summarization:** Summarize lengthy incoming emails into 2-sentence conversational voice briefs using small language models.
- [ ] **Voice Biometrics:** Voiceprint authentication for secure hands-free login.
- [ ] **Wearable & Mobile Port:** Deploying to Android and iOS devices using Kivy/Buildozer.

---

