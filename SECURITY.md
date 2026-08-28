# Security Policy

## Supported version

Security fixes are applied to the latest release on the `main` branch.

## Reporting a vulnerability

Do **not** publish sensitive vulnerability details in a public GitHub issue.

Use GitHub's private vulnerability reporting / Security Advisory flow for this repository when available:

`Security` → `Advisories` → `Report a vulnerability`

If private reporting is unavailable, open a minimal public issue requesting a private contact channel without including exploit details, credentials, tokens, or personal data.

## Security model

ORBIT is a local desktop agent and can perform real actions on the user's machine. Treat every new tool as a permission boundary.

Current design choices include:

- no arbitrary shell-execution tool;
- application launches are allowlisted through configuration;
- normal URL tools are restricted to `http` / `https`;
- `config.json`, local memory, session-like files, and recordings are ignored by Git;
- PyAutoGUI fail-safe remains enabled;
- the assistant is instructed not to claim action success when the underlying tool reports failure.

## Desktop automation

Telegram automation controls the user's real keyboard/window state. Test it with a non-sensitive contact before a course demo or release.

Do not use the automation for spam, bulk unsolicited messaging, credential collection, or behavior that violates platform terms.

## Web research

The web reader is intended for ordinary public HTML. It should not be modified to bypass authentication, paywalls, CAPTCHAs, or anti-bot controls.

## Secrets

Never commit:

- API tokens;
- passwords;
- Telegram session files;
- `.env`;
- `config.json` when it contains private data;
- personal memory files;
- captured audio containing private information.

If a secret is accidentally committed, rotate/revoke the secret first; deleting the file in a later commit is not sufficient.


## Prompt injection and web content

Webpage text and search snippets are untrusted input.

ORBIT:

- instructs the LLM not to follow instructions embedded in retrieved content;
- applies a deterministic user-authorization guard before current side-effecting tools can execute;
- adds a system-level reminder after web-tool results;
- blocks private/loopback/link-local destinations in the webpage reader;
- bounds response bytes and total research evidence size.

Do not remove these boundaries when adding richer browsing features.

## Action confirmations

The public example configuration enables confirmations for side-effecting tools. The separate course/demo profile can disable the dialog for an instructor-controlled demonstration.

A tool's `requires_confirmation` classification must remain accurate even when the dialog is disabled by configuration.
