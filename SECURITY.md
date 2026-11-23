# Security & Privacy Policy

## Reporting Security or Privacy Vulnerabilities

CareerForge is dedicated to being 100% local-first and private. We take accidental network exfiltration or security vulnerabilities very seriously.

If you discover a security vulnerability or network leakage in CareerForge:

1. **Do not disclose it publicly.** Do not open a public GitHub issue.
2. Open a security advisory on GitHub or email the maintainers at `security@careerforge.dev`.
3. Include details of the vulnerability, reproduction steps, and platform.
4. You will receive an acknowledgment within 48 hours.

## Scope
CareerForge is an offline CLI tool. The only permitted network calls are in `scrapers/` to fetch public, unauthenticated job boards. Any other unexpected network socket or credential logging is considered a high-severity bug.
