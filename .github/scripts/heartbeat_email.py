#!/usr/bin/env python3
"""Build the Resend payload for the daily heartbeat digest, in VNTA's own
visual and verbal register: monochrome, hairline dividers, Marcellus/Manrope,
short declarative sentences, no en dashes, no hype.

A separate file rather than an inline workflow script on purpose: a
multi-line script embedded in a YAML block scalar is one bad indent away
from silently corrupting the whole workflow file (it happened once already
on 2026-09-06). This is plain Python, checked in, testable on its own:

    FAIL=0 REPORT_PATH=/path/to/report.md ISSUES_URL=https://example.com/issues \
        python3 .github/scripts/heartbeat_email.py

Reads FAIL ("0" or "1"), REPORT_PATH (the probe step's report.md) and
ISSUES_URL from the environment. Prints the JSON body for POST
https://api.resend.com/emails to stdout. Never touches the network itself.

Shows every property checked, not just the ones that failed: a report that
only speaks up when something is wrong reads as silence the rest of the
time, and silence is not the same as "I checked and it's fine."
"""

import json
import os
import re

from vnta_email import html_shell

FROM = "VNTA Heartbeat <heartbeat@vnta.xyz>"
TO = ["studio@vnta.xyz"]

# Internal probe names, mapped to how a reader outside engineering would
# name the same thing. Anything not listed falls back to its raw name.
FRIENDLY_NAMES = {
    "vnta.xyz": "vnta.xyz",
    "eirvox.ie": "eirvox.ie",
    "vendr.ie": "vendr.ie",
    "maisonseul.com": "maisonseul.com",
    "tacet.social": "tacet.social",
    "buildt.ie": "buildt.ie",
    "ezgoautoworks.ie": "ezgoautoworks.ie",
    "supabase: vendr + vnta": "the database behind vendr.ie",
    "supabase: eirvox": "the database behind eirvox.ie",
}


def parse_report(report_path):
    """Returns a list of (friendly_name, ok: bool) for every row, in the
    order the workflow probed them."""
    rows = []
    try:
        with open(report_path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return rows
    for line in lines:
        if not line.startswith("|") or line.startswith("| Property") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        raw_name = cells[0]
        ok = "**DOWN**" not in cells[2]
        rows.append((FRIENDLY_NAMES.get(raw_name, raw_name), ok))
    return rows


def english_list(items):
    """['a'] -> 'a'; ['a','b'] -> 'a and b'; ['a','b','c'] -> 'a, b, and c'."""
    if len(items) <= 1:
        return items[0] if items else "something"
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def checklist_html(rows):
    """One row per checked property: name in Manrope, a plain OK / DOWN
    label in the mono small-caps register the site already uses for labels.
    Tone, not colour, carries the difference: this is a monochrome system,
    no reds or greens."""
    items = []
    for name, ok in rows:
        status = "OK" if ok else "DOWN"
        status_color = "#9b9b9b" if ok else "#0a0a0a"
        status_weight = "500" if ok else "600"
        items.append(
            '<tr>'
            f'<td style="padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.08);'
            'font-family:\'Manrope\',system-ui,-apple-system,\'Segoe UI\',sans-serif;'
            f'font-size:14px;color:#404040;">{name}</td>'
            f'<td align="right" style="padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.08);'
            'font-family:ui-monospace,SFMono-Regular,\'SF Mono\',Menlo,Consolas,monospace;'
            f'font-size:11px;letter-spacing:0.12em;font-weight:{status_weight};'
            f'color:{status_color};">{status}</td>'
            '</tr>'
        )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;">'
        + "".join(items)
        + "</table>"
    )


def build():
    fail = os.environ.get("FAIL", "0") == "1"
    report_path = os.environ.get("REPORT_PATH", "")
    issues_url = os.environ.get("ISSUES_URL", "")
    today = os.environ.get("TODAY", "")

    rows = parse_report(report_path)
    down = [name for name, ok in rows if not ok]

    if fail:
        named = english_list(down)
        be = "isn't" if len(down) <= 1 else "aren't"
        headline_thing = "One thing" if len(down) <= 1 else f"{len(down)} things"
        subject = (
            f"VNTA daily check: {named} needs a look"
            if len(down) <= 1
            else f"VNTA daily check: {len(down)} things need a look"
        )
        intro_text = (
            f"{named} {be} answering right now. This was caught automatically, "
            f"a few minutes after it happened. Details are in the note here if "
            f"you want them: {issues_url}."
        )
        intro_html = (
            f'<p style="margin:0;">{named} {be} answering right now. '
            "This was caught automatically, a few minutes after it happened. "
            f'Details are in the note here if you want them: '
            f'<a href="{issues_url}" style="color:#0a0a0a;">{issues_url}</a>.</p>'
        )
        label = "daily check &middot; needs a look"
        headline = f"{headline_thing} need{'s' if len(down) <= 1 else ''} a look."
    else:
        subject = "VNTA daily check: all clear"
        intro_text = "Every VNTA site and both databases answered normally today."
        intro_html = (
            '<p style="margin:0;">Every VNTA site and both databases answered '
            "normally today.</p>"
        )
        label = "daily check"
        headline = "All clear."

    checked_lines = "\n".join(f"{name}: {'ok' if ok else 'down'}" for name, ok in rows)
    text = f"{intro_text}\n\nChecked today:\n{checked_lines}" if rows else intro_text
    footer_note = f"Automated check for VNTA Group{f' &middot; {today}' if today else ''}."

    payload = {
        "from": FROM,
        "to": TO,
        "subject": subject,
        "text": text,
        "html": html_shell(label, headline, intro_html + checklist_html(rows), footer_note),
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    build()
