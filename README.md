# Secure File Storage (Flask + Fernet AES) - Modern Styled Frontend

## Overview
Simple demo that encrypts files (using Fernet symmetric encryption from the `cryptography` library) before saving to a local `uploads/` folder. The app returns the encryption key immediately after upload — **store it safely**. Files saved are encrypted (filename.ext.enc). You can later decrypt by providing the correct key.

## Tech stack
- Python 3.8+
- Flask (web UI)
- cryptography (Fernet symmetric encryption)

## How to run
1. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux / macOS
   venv\Scripts\activate  # Windows PowerShell
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Open `http://127.0.0.1:5000` in your browser.

## Notes & Security
- This is an educational/demo project. For production:
  - Use server-side secure key management (KMS) instead of showing raw keys to users.
  - Use HTTPS, enforce authentication, rate-limiting, logging, and strict file validation.
  - Consider encrypting with per-user keys and storing keys in a secure vault.
