"""Shared VNTA email envelope: hairline masthead, Marcellus headline, Manrope
body, hairline footer. Table-based and inline-styled since email clients do
not reliably honour a <style> block, let alone external CSS. Colours and
spacing are lifted straight from the site's own tokens.css (paper #f6f6f6,
ink #0a0a0a, ink-70 #404040, ink-35 #9b9b9b, hairline rgba(0,0,0,.14)), not
approximated.

Used by heartbeat_email.py (the daily check) and send_branded_email.py (a
one-off send, e.g. an example of a monthly report). Keep this module free of
anything specific to either caller.
"""

FONT_IMPORT = (
    "https://fonts.googleapis.com/css2"
    "?family=Marcellus&family=Manrope:wght@400;500;600&display=swap"
)


def html_shell(label, headline, body_html, footer_note):
    return f"""\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VNTA</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="{FONT_IMPORT}" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background-color:#f6f6f6;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f6f6f6;">
<tr><td align="center" style="padding:40px 20px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background-color:#ffffff;">

<tr><td style="padding:24px 32px;border-bottom:1px solid rgba(0,0,0,0.14);">
<span style="font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace;font-size:11px;letter-spacing:0.22em;text-transform:uppercase;color:#6b6b6b;">VNTA &middot; {label}</span>
</td></tr>

<tr><td style="padding:40px 32px 8px;">
<h1 style="margin:0;font-family:'Marcellus','Optima','Times New Roman',serif;font-weight:400;font-size:28px;line-height:1.25;color:#0a0a0a;">{headline}</h1>
</td></tr>

<tr><td style="padding:16px 32px 40px;">
<div style="font-family:'Manrope',system-ui,-apple-system,'Segoe UI',sans-serif;font-size:16px;line-height:1.65;color:#404040;">
{body_html}
</div>
</td></tr>

<tr><td style="padding:20px 32px;border-top:1px solid rgba(0,0,0,0.14);">
<span style="font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace;font-size:11px;letter-spacing:0.08em;color:#9b9b9b;">{footer_note}</span>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""
