# VisionCrash AI

**VisionCrash AI** is an automated vehicle crash detection system for traffic and CCTV video feeds, powered by a trained **TensorFlow Object Detection** `SavedModel`. It includes both a **Gradio web interface** for cloud/browser deployment and a **Tkinter desktop application** with an incident records viewer, along with automated **Email** and **SMS** emergency alerts.

## About

Road traffic accidents often suffer from delayed emergency response when incidents go unnoticed on surveillance feeds. **VisionCrash AI** automates crash monitoring by running frame-by-frame object detection on CCTV/traffic videos to flag collisions in real time, capture annotated incident frames, log detection history, and dispatch instant Email and SMS alerts to emergency services (Hospital, Police, and RTO).

---

## Features

- **Automated Crash Detection:** Frame-by-frame inference using a TensorFlow Object Detection `SavedModel` (`inference_graph/saved_model`) with bounding-box overlays and confidence scores.
- **Gradio Web App (`app.py`):** Upload traffic/CCTV videos, tune the detection confidence threshold (`0.30`–`0.99`, default `0.90`), preview the annotated output video and first detected crash frame, or test with the included sample video.
- **Desktop Application (`main.py` / `vcd_ui.py`):** Full Tkinter GUI for running detection on video sources and browsing saved crash frames and history in the **Records** viewer (`image_data_viewer.py`).
- **Emergency Alerts (Optional):**
  - **Email Alerts (`email_alert.py`):** Sends incident details and captured frame attachments to configured Hospital, Police, and RTO addresses using templates in `messages/`.
  - **SMS Alerts (`sms_alert.py`):** Supports **Twilio** and **FAST2SMS** for instant SMS notifications.

---

## Project Structure

```text
VisionCrash-Ai/
├── app.py                      # Gradio web interface
├── main.py                     # Desktop application entry point
├── vcd_ui.py                   # Tkinter main UI
├── vehicle_crash_detection.py  # Core desktop detection pipeline
├── image_data_viewer.py        # Incident records & captured frame viewer
├── email_alert.py              # Gmail SMTP alert sender
├── sms_alert.py                # Twilio / FAST2SMS alert sender
├── alert_config.py             # Environment/secret configuration loader
├── label_map.pbtxt             # Model class label map
├── requirements.txt            # Python dependencies
├── .env.example                # Template for alert credentials
├── inference_graph/            # Trained TensorFlow SavedModel & checkpoint
├── messages/                   # Email alert message templates
├── object_detection/           # TensorFlow Object Detection API utilities
├── outputs/                    # Saved detection videos, frames, and history
├── resources/                  # Application icons
└── test_videos/                # Sample test video
```

---

## Installation & Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sakshamjain0/VisionCrash-Ai.git
   cd VisionCrash-Ai
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure alerts (optional):**
   Copy `.env.example` to `.env` and fill in your credentials if you want to enable Email/SMS alerts:
   ```bash
   cp .env.example .env
   ```

---

## Usage

### Web Interface (Gradio)
```bash
python app.py
```
Open the local URL printed in the terminal (typically `http://127.0.0.1:7860`) to upload a video or run the built-in sample video.

### Desktop Application (Tkinter)
```bash
python main.py
```

---

## Environment Variables (`.env`)

| Variable | Description |
| --- | --- |
| `VCD_EMAIL_ADDRESS` | Sender Gmail address for email alerts |
| `VCD_EMAIL_APP_PASSWORD` | Gmail App Password |
| `VCD_HOSPITAL_EMAIL` | Recipient email for hospital alerts |
| `VCD_POLICE_EMAIL` | Recipient email for police alerts |
| `VCD_RTO_EMAIL` | Recipient email for RTO alerts |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID (SMS option 1) |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_FROM_NUMBER` | Twilio sender phone number |
| `TWILIO_MESSAGING_SERVICE_SID` | Twilio Messaging Service SID (optional) |
| `TWILIO_TO_NUMBERS` | Comma-separated recipient phone numbers |
| `TWILIO_DEFAULT_COUNTRY_CODE` | Default country code (e.g. `+91`) |
| `TWILIO_SMS_MODE` | Twilio mode (default: `trial-safe`) |
| `FAST2SMS_API_KEY` | FAST2SMS API key (SMS option 2) |
| `FAST2SMS_NUMBERS` | Comma-separated recipient numbers for FAST2SMS |
| `FAST2SMS_ROUTE` | FAST2SMS route (default: `q`) |
