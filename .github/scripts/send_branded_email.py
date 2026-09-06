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
import sys
import urllib.error
import urllib.request

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
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        print("RESEND_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            print(f"Resend responded {res.status}")
            print(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Resend responded {e.code}", file=sys.stderr)
        print(e.read().decode("utf-8"), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    send(build_payload())
