#!/usr/bin/env python3
"""
Bulk Mailer Utility
-------------------
A professional-grade bulk email sender script for Python developers.

Features:
- Sends personalized emails to multiple recipients from a CSV file.
- Uses Markdown templates for email content (both text and HTML).
- Supports attachments.
- Uses threading for parallel email sending.
- Includes error handling, validation, logging, and .env configuration.

Author: OpenAI GPT-5
License: MIT
"""

import os
import csv
import re
import logging
import smtplib
import markdown
from tqdm import tqdm
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from concurrent.futures import ThreadPoolExecutor, as_completed


# =====================
# Configuration & Setup
# =====================

load_dotenv()  # Load .env if present

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
PASSWORD = os.getenv("PASSWORD")
DISPLAY_NAME = os.getenv("DISPLAY_NAME", "Python Mailer")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

LOG_FILE = "mailer.log"
ATTACH_DIR = "ATTACH"
DATA_FILE = "data.csv"
TEMPLATE_FILE = "compose.md"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


# =====================
# Helper Functions
# =====================

def is_valid_email(email: str) -> bool:
    """Validate an email address using regex."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))


def load_template(path: str) -> str:
    """Load the email template."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template file '{path}' not found.")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_recipients(path: str) -> list:
    """Load recipient data from a CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file '{path}' not found.")
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_attachments(directory: str) -> dict:
    """Confirm and load attachments from a directory."""
    attachments = {'names': [], 'contents': []}
    if not os.path.exists(directory):
        return attachments

    for filename in os.listdir(directory):
        confirm = input(f"Attach '{filename}'? (Y/n): ").strip().lower()
        if confirm in ('y', 'yes', ''):
            path = os.path.join(directory, filename)
            with open(path, "rb") as f:
                attachments['names'].append(filename)
                attachments['contents'].append(f.read())
    return attachments


def personalize_message(template: str, data: dict) -> str:
    """Replace placeholders in the template with CSV values."""
    message = template
    for key, value in data.items():
        message = message.replace(f"${key}", str(value))
    return message


def build_email(to_email: str, subject: str, body: str, attachments: dict) -> MIMEMultipart:
    """Build an email message with text, HTML, and attachments."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{DISPLAY_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to_email

    text_part = MIMEText(body, "plain")
    html_part = MIMEText(markdown.markdown(body), "html")
    msg.attach(text_part)
    msg.attach(html_part)

    for name, content in zip(attachments['names'], attachments['contents']):
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(content)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={name}")
        msg.attach(part)

    return msg


def send_email(server: smtplib.SMTP, to_email: str, msg: MIMEMultipart) -> bool:
    """Send an email and handle potential errors."""
    try:
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        logging.info(f"✅ Sent to {to_email}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to send to {to_email}: {e}")
        return False


# =====================
# Main Mailer Function
# =====================

def bulk_send():
    """Main execution flow for sending bulk emails."""
    print("🚀 Bulk Mailer Starting...")

    # --- Load resources
    template = load_template(TEMPLATE_FILE)
    recipients = load_recipients(DATA_FILE)
    attachments = get_attachments(ATTACH_DIR)

    # --- Prepare SMTP connection
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, PASSWORD)

        sent_count = 0
        futures = []

        # --- Parallel sending
        with ThreadPoolExecutor(max_workers=8) as executor:
            for person in recipients:
                email = person.get("EMAIL")
                if not is_valid_email(email):
                    logging.warning(f"Invalid email skipped: {email}")
                    continue

                msg_text = personalize_message(template, person)
                subject = msg_text.splitlines()[0] or "No Subject"
                message = build_email(email, subject, msg_text, attachments)
                futures.append(executor.submit(send_email, server, email, message))

            for f in tqdm(as_completed(futures), total=len(futures), desc="📨 Sending"):
                if f.result():
                    sent_count += 1

        print(f"\n✅ Successfully sent {sent_count}/{len(recipients)} emails.")
        logging.info(f"Completed: {sent_count}/{len(recipients)} emails sent.")


# =====================
# Entry Point
# =====================

if __name__ == "__main__":
    try:
        bulk_send()
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user.")
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
