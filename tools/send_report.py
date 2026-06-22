#!/usr/bin/env python3
"""
Build (if needed) and email the daily Key List report.

Sends via SMTP. Credentials are read from ENVIRONMENT VARIABLES that YOU set —
this script never stores or prints your password.

Required env vars:
    MW_SMTP_USER   sending account (e.g. your Gmail / NYU Google address)
    MW_SMTP_PASS   app password for that account (NOT your normal password)
Optional env vars (sensible defaults):
    MW_SMTP_HOST   default smtp.gmail.com
    MW_SMTP_PORT   default 587  (STARTTLS)
    MW_MAIL_TO     recipient address (required to send)
    MW_MAIL_FROM   default = MW_SMTP_USER

Set them once (PowerShell, persists for your user):
    setx MW_SMTP_USER "youraddress@gmail.com"
    setx MW_SMTP_PASS "your-16-char-app-password"
    # then open a NEW shell so the vars are visible

Usage:  python tools/send_report.py
"""
import os, sys, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import build_report

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _env(name, default=None):
    """Read an env var; on Windows fall back to the User-scope registry so the
    daily routine works even if the shell didn't inherit a freshly-set var."""
    v = os.environ.get(name)
    if not v and sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                v = winreg.QueryValueEx(k, name)[0]
        except OSError:
            v = None
    return v if v else default


def main():
    user = (_env("MW_SMTP_USER") or "").strip()
    pwd = (_env("MW_SMTP_PASS") or "").replace(" ", "")  # Gmail app pw has no spaces
    host = _env("MW_SMTP_HOST", "smtp.gmail.com")
    port = int(_env("MW_SMTP_PORT", "587"))
    to_addr = (_env("MW_MAIL_TO") or "").strip()
    from_addr = _env("MW_MAIL_FROM", user or "")

    md_path, html_path = build_report.main()
    md_text = open(md_path, encoding="utf-8").read()
    html = open(html_path, encoding="utf-8").read()
    # subject = first H1 minus the leading '# '
    subject = md_text.splitlines()[0].lstrip("# ").strip()

    if not user or not pwd or not to_addr:
        print(
            "\nEmail NOT sent — not configured (this is expected until set up).\n"
            "Set MW_SMTP_USER, MW_SMTP_PASS, and MW_MAIL_TO (see this file's header), then re-run.\n"
            f"The report is ready at:\n  {md_path}\n  {html_path}")
        return  # clean exit; report files are still produced

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(md_text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, pwd)
        s.sendmail(from_addr, [a.strip() for a in to_addr.split(",")], msg.as_string())
    print(f"\nSent '{subject}' to {to_addr} (from {from_addr}).")


if __name__ == "__main__":
    main()
