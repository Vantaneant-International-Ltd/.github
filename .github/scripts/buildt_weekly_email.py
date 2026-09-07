#!/usr/bin/env python3
"""Send Andrew (BUILDT) his weekly site-status update, in VNTA's own visual
register. This is VNTA talking to a client about their site, not BUILDT
talking to its own customers, which already has its own separate sender
in client-buildt/scripts/buildt_email.py.

Checks buildt.ie itself right before sending, so the "your site is live"
line is a real fact checked moments ago, not a guess, then builds the
email with the same html_shell already used for the daily heartbeat.

TO/CC/BCC read from the environment so a manual test run can point the
email at reviewers instead of the real client; leaving any of them unset
(as the real weekly schedule always does) falls back to the real
production recipients below.

    RESEND_API_KEY=... python3 .github/scripts/buildt_weekly_email.py
"""

import json
import os
import subprocess
import sys

from vnta_email import html_shell

DEFAULT_FROM = "VNTA <studio@vnta.xyz>"
DEFAULT_TO = ["contact@buildt.ie"]
DEFAULT_CC = ["buildt.ireland@gmail.com"]
DEFAULT_BCC = ["studio@vnta.xyz"]

PORTAL_URL = "https://vnta.xyz/portal"


def addr_list(env_var, default):
    raw = os.environ.get(env_var, "")
    if not raw:
        return default
    return [addr.strip() for addr in raw.split(",") if addr.strip()]


def buildt_ie_is_up():
    try:
        result = subprocess.run(
            [
                "curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                "-L", "--max-time", "20", "https://buildt.ie",
            ],
            capture_output=True, text=True, timeout=30,
        )
        code = result.stdout.strip()
    except Exception:
        code = ""
    return code.startswith("2")


def build_payload():
    if buildt_ie_is_up():
        status_line = "We checked buildt.ie right before sending this. It is live and working."
    else:
        status_line = (
            "We checked buildt.ie right before sending this and it did not answer as "
            "expected. We are already looking into it."
        )

    body_text = (
        f"{status_line}\n\n"
        "We check it automatically every day behind the scenes, so if anything ever "
        "goes wrong you do not have to be the one to notice it first.\n\n"
        f"You can also look for yourself any time at {PORTAL_URL}."
    )
    body_html = f"""\
<p style="margin:0 0 16px;">{status_line}</p>
<p style="margin:0 0 16px;">We check it automatically every day behind the scenes, so if anything ever
goes wrong you do not have to be the one to notice it first.</p>
<p style="margin:0;">You can also look for yourself any time at
<a href="{PORTAL_URL}" style="color:inherit;">{PORTAL_URL}</a>.</p>
"""

    payload = {
        "from": os.environ.get("FROM", DEFAULT_FROM),
        "to": addr_list("TO", DEFAULT_TO),
        "subject": os.environ.get("SUBJECT", "Your weekly buildt.ie update"),
        "text": body_text,
        "html": html_shell("weekly update", "Your site, this week.", body_html, "Sent by VNTA Group."),
    }
    cc = addr_list("CC", DEFAULT_CC)
    bcc = addr_list("BCC", DEFAULT_BCC)
    if cc:
        payload["cc"] = cc
    if bcc:
        payload["bcc"] = bcc
    return payload


def send(payload):
    # curl, not a Python HTTP client: Resend sits behind Cloudflare, and a
    # library's default User-Agent can read as a bot signature there (hit
    # this exact wall building send_branded_email.py).
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
