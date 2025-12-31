import os
import smtplib

SMTP_SERVER = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('EMAIL_PORT', '587'))
SMTP_USERNAME = os.getenv('EMAIL_USER', '')
SMTP_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
USE_SSL = os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true'

print({
    'server': SMTP_SERVER,
    'port': SMTP_PORT,
    'user': SMTP_USERNAME,
    'tls': USE_TLS,
    'ssl': USE_SSL,
})

if not SMTP_USERNAME or not SMTP_PASSWORD:
    print('Missing EMAIL_USER/EMAIL_PASSWORD; cannot test login.')
    raise SystemExit(1)

try:
    if USE_SSL:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print('SMTP SSL login success')
    else:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            if USE_TLS:
                server.starttls()
                server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print('SMTP TLS login success' if USE_TLS else 'SMTP login success')
except smtplib.SMTPAuthenticationError as e:
    print(f'Auth failed: code={getattr(e, "smtp_code", None)} msg={getattr(e, "smtp_error", e)}')
    print('Fix: use a provider App Password (Gmail requires 2FA + App Password).')
    raise
except Exception as e:
    print(f'SMTP error: {e}')
    raise
