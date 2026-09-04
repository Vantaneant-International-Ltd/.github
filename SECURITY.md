# Security

## Reporting a vulnerability

If you find a security problem in any VNTA Group repository or live site
(vnta.xyz, eirvox.ie, vendr.ie, maisonseul.com, tacet.social, or a client site
we operate), email **studio@vnta.xyz** with "SECURITY" in the subject.

Please include what you found, where, and how to reproduce it. Do not open a
public issue for security reports.

You should hear back within 5 working days. We will tell you what we are doing
about it and when it is fixed. If the problem involves a payment or a person's
data, we treat it as urgent.

## Scope

This policy applies to every repository in the `Vantaneant-International-Ltd`
organisation. A repository may carry its own `SECURITY.md` with more detail;
where it does, that file adds to this one and does not replace it.

## What we already do

- Every repository runs a full-history secret scan (gitleaks) on each push.
- Secret scanning and push protection are enabled at the organisation level.
- Server-side secrets are never committed. Public keys that are safe in a
  browser (Supabase publishable keys, Turnstile site keys) are the only keys
  that appear in source, and each is protected by row-level security or a
  server-side secret counterpart.
