# Medialoft — Learning Guide

> A guided, **non-spoiler** path to solving this lab. It teaches the *method*,
> not the answer — the exact winning payload and the flag stay in
> [SOLUTION.md](SOLUTION.md).

## Before you start

Read the shared **[Path Traversal field guide](https://github.com/iv0ks/appsec-labs/blob/main/docs/path-traversal.md)**
first. It covers what path traversal (CWE-22) is, why it appears, and the manual
testing workflow with **Burp Suite** and **OWASP ZAP**. This guide assumes it.

## What this level teaches

**Level 4 — validating the wrong thing (file extension).** Medialoft's CDN only
serves images, so the endpoint checks that the requested name ends in `.png`
and rejects anything else. An extension check *feels* like a whitelist, but an
extension is **not** a path boundary: a traversal payload can perfectly well end
in `.png` and still climb out of the served directory. The lesson is to notice
*what* a validation actually constrains versus what the developer assumed.

- **Entry point:** `GET /asset?name=<name>`
- **The broken defence:** the name must end with `.png` (no path containment).
- **Served directory:** `media/` · **target:** a file one level above it.

## How to approach it

1. Load the gallery through your proxy and capture an `/asset?name=` request for
   a real image.
2. Baseline it, then try a non-`.png` traversal — notice it is rejected (the
   check *is* active).
3. Re-read the check: it only cares about how the name *ends*. Can a path that
   escapes the directory still satisfy "ends with `.png`"? Shape your payload so
   the extension check passes **and** the path traverses.
4. Keep the path as-is and confirm you read the target outside `media/`.

## Going further

Extension checks appear everywhere (uploads, downloads, image proxies). The same
mental move — "what does this validation *actually* guarantee?" — applies to
content-type checks, magic-byte sniffing and MIME filters.

## Why it matters

Mistaking a *type* check for a *location* check is a classic real-world blind
spot. This level trains you to separate "is it the right kind of file" from "is
it in the right place".

When you have captured the flag (or want to check the fix), read
[SOLUTION.md](SOLUTION.md).
