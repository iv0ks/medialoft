# Medialoft: Learning Guide

![CWE-22](https://img.shields.io/badge/CWE--22-Path%20Traversal-red?style=flat-square)
![Python](https://img.shields.io/badge/Python-Flask-blue?style=flat-square&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Lab-Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

**Medialoft is an intentionally vulnerable application built for security education.** It is a small image CDN with a deliberate [path traversal](https://owasp.org/www-community/attacks/Path_Traversal)
(CWE-22) flaw — it only checks that the requested file ends in `.png`, which does nothing to stop traversal — so you can practice finding and exploiting it in a safe and controlled environment.

<br>

> [!TIP]
> A guided, **non-spoiler** path to solving this lab. It teaches the *method*, not the answer — the exact winning payload and the flag stay in [SOLUTION.md](SOLUTION.md).

<br>

## 🧬 What path traversal is

Here is the whole idea in one sentence:

> **Path traversal happens when an app builds a file path out of user input and
> then trusts that path to stay where it's supposed to.**

A web app usually wants to serve files from *one* folder — here, the `media/`
library. The intended deal is: "give me a filename, I'll give you that image
*from this folder*." The catch is that the folder boundary is a **convention**,
not a **rule** the code enforces. Filesystems understand `..` as "go up one
level", so a filename like `../something.png` is a perfectly valid instruction
to leave the folder. If the guard doesn't check the *path*, the app obeys.

Think of `media/` as a room and the filename as directions. "`aurora.png`" means
"the aurora image in this room." "`../something`" means "step out the door, then
grab a file in the hallway." Medialoft checks what *kind* of thing you asked for
(a `.png`) but never checks *where* it is — it guards the label on the box, not
the room.

That "filename → file read" shape is the **sink** you're training your eye to
spot. Once you can recognise it on sight, you can find this bug in seconds.

> Want the deeper background — history, variants, encoding tricks, and the full
> manual-testing workflow with **Burp Suite** and **OWASP ZAP**? Read the shared
> **[Path Traversal field guide](https://github.com/iv0ks/appsec-labs/blob/main/docs/path-traversal.md)**.
> This lab is a hands-on application of it.

<br>

## 🎓 What this level teaches

**Level 4 — validating the wrong thing (file extension).** Medialoft's CDN only
serves images, so the endpoint checks that the requested name ends in `.png`
and rejects anything else. An extension check *feels* like an allow-list, but an
extension is **not** a path boundary: a traversal payload can perfectly well end
in `.png` and still climb out of the served directory. The lesson is to notice
*what* a validation actually constrains versus what the developer assumed.

- **Entry point:** `GET /asset?name=<file>.png`
- **The broken defence:** the name must end with `.png` (no path containment).
- **Served directory:** `media/` · **target:** a `.png` file one level above it.

## 🪧 How to approach it

1. Load the gallery through your proxy and capture an `/asset?name=` request for
   a real image. Re-send it for your **baseline**.
2. Probe the guard: try a `../` traversal to a `.txt` file — it is rejected, so
   a filter *is* active. Read what it actually checks.
3. The guard only cares how the name *ends*. Can a path that escapes the
   directory still satisfy "ends with `.png`"? Shape your payload so the
   extension check passes **and** the path traverses — note the target is stored
   with a `.png` extension on purpose.
4. Confirm you read the target outside `media/`. Keep the path **as-is** so
   `../` isn't normalised before it is sent (`curl --path-as-is`, or edit the
   raw request).

## 🕵️‍♂️ Going further

Extension checks appear everywhere (uploads, downloads, image proxies). The same
mental move — "what does this validation *actually* guarantee?" — applies to
content-type checks, magic-byte sniffing and MIME filters. The labs run as a
non-root user inside Docker, so the bug is real but the blast radius is
contained on purpose.

## 🤔 Why it matters

Mistaking a *type* check for a *location* check is a classic real-world blind
spot. This level trains you to separate "is it the right kind of file" from
"is it in the right place" — two questions developers constantly conflate.

---

When you have captured the flag (or want to check the fix and the *why* behind
it), continue to **[SOLVE → SOLUTION.md](SOLUTION.md)**.
