#!/usr/bin/env python3
"""Send a one-off email in VNTA's visual register via Resend. For anything
that isn't the daily heartbeat (which has its own heartbeat_email.py): an
example report, a one-time notice, anything a person should read rather
than a script.

Reads everything from the environment so it can be driven from a
workflow_dispatch input or from a shell one-liner:

    TO=studio@vnta.xyz LABEL="example" HEADLINE="An example." \
    BODY_HTML='<p style="margin:0;">Body copy here.</p>' \
    SUBJECT="VNTA: an example" FOOTER_NOTE="Sent by hand." \
    RESEND_API_KEY=... python3 .github/scripts/send_branded_email.py

Prints the Resend response and exits non-zero on a non-2xx reply, so a
workflow step fails loudly rather than reporting green on a silent drop.
"""

import json
import os
import subprocess
import sys

from vnta_email import html_shell

FROM = "VNTA <heartbeat@vnta.xyz>"


def build_payload():
    to = [addr.strip() for addr in os.environ.get("TO", "studio@vnta.xyz").split(",") if addr.strip()]
    label = os.environ.get("LABEL", "notice")
    headline = os.environ.get("HEADLINE", "")
    body_html = os.environ.get("BODY_HTML", "")
    body_text = os.environ.get("BODY_TEXT") or body_html
    subject = os.environ.get("SUBJECT", headline or "VNTA")
    footer_note = os.environ.get("FOOTER_NOTE", "Sent by VNTA Group.")

    return {
        "from": FROM,
        "to": to,
        "subject": subject,
        "text": body_text,
        "html": html_shell(label, headline, body_html, footer_note),
    }


def send(payload):
    # Shells out to curl rather than urllib: Resend sits behind Cloudflare,
    # and urllib's default User-Agent ("Python-urllib/3.x") reads as a bot
    # signature to it, a real 403 hit on 2026-09-06 (Cloudflare error 1010).
    # curl's default User-Agent does not trip it; heartbeat_email.py's own
    # curl-based send already proved that twice before this script existed.
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        print("RESEND_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        [
            "curl", "-sS", "--max-time", "20",
            "-w", "\nHTTP_STATUS:%{http_code}",
            "-X", "POST", "https://api.resend.com/emails",
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    body, _, status = result.stdout.rpartition("HTTP_STATUS:")
    status = status.strip()
    print(f"Resend responded {status or '?'}")
    print(body.strip())
    if result.returncode != 0 or not status.startswith("2"):
        print(result.stderr, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    send(build_payload())
