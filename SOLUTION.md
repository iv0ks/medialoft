# Medialoft: Solution / Walkthrough

![CWE-22](https://img.shields.io/badge/CWE--22-Path%20Traversal-red?style=flat-square)
![Python](https://img.shields.io/badge/Python-Flask-blue?style=flat-square&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Lab-Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

**Medialoft is an intentionally vulnerable application built for security education.** It is a small image CDN with a deliberate [path traversal](https://owasp.org/www-community/attacks/Path_Traversal)
(CWE-22) flaw — it only checks that the requested file ends in `.png`, which does nothing to stop traversal — so you can practice finding and exploiting it in a safe and controlled environment.

<br>

> [!WARNING]
> This page gives away the payload and the flag. If you want to solve it yourself, start with the non-spoiler **[Learning Guide](GUIDE.md)** and come back here to check your work.

<br>

## 📚 What you'll get from this page

The [Learning Guide](GUIDE.md) covers *what* path traversal is and *how* to
approach the lab. This page is the spoiler half: the confirmed exploit, the
flag, and — most importantly — the **why** behind the bug and its fix. By the
end you should be able to:

- Read a snippet of file-serving code and point to the exact vulnerable line.
- Explain why an extension check is not a containment check.
- Explain **why** each fix works — and why some "obvious" fixes don't.

> **One-line recap** (full version in the [GUIDE](GUIDE.md)): path traversal
> happens when an app builds a file path from user input and trusts it to stay
> inside the intended folder. Medialoft checks the *extension*, not the
> *location* — so a `.png` payload walks straight out.

If you only want the payload, jump to [Exploitation](#-exploitation) — but the
real value is in the *why*.

<br>

## 🐛 The vulnerability

The `app/routes.py` guards the request like this:

```python
name = request.args.get("name", "")            # attacker controls this
allowed_ext = current_app.config["ALLOWED_EXTENSION"]   # ".png"

# The only guard: the name must end in ".png".
if not name.endswith(allowed_ext):
    return render_error(400, f"Only {allowed_ext} assets are served.")

media_dir = current_app.config["MEDIA_DIR"]
target_path = os.path.join(media_dir, name)         # no boundary check

if not os.path.isfile(target_path):
    return render_error(404, f"Asset not found: {name}")

return send_file(target_path, as_attachment=False)
```

Walk through it the way the computer does:

1. `name` comes **straight from the query string** — fully attacker-controlled.
2. The guard checks only one thing: does `name` **end with** `.png`? A non-image
   request (`../secret.txt`) is rejected here — which makes the check *feel*
   protective.
3. But the check says nothing about *where* the file is. `os.path.join` keeps
   `..` segments, so `../flag.png` escapes `media/` — and it ends in `.png`, so
   it passes the guard.
4. There is no boundary check on the resolved path before `send_file` opens it.

The mistake is validating the wrong property. "Ends in `.png`" answers "is this
the right *kind* of file?" It never answers "is this file in the right
*place*?" — which is the only question that stops traversal.

> **Why does this look safe?** Because rejecting `../secret.txt` *looks* like the
> filter is doing its job. It is — just not the job you need. The target simply
> wears a `.png` costume.

<br>

## 💥 Exploitation

**The intended request** — what the app expects:

```
GET /asset?name=aurora.png
```

Resolves to `media/aurora.png`. Working as designed.

**A non-`.png` traversal is blocked** by the extension guard:

```
GET /asset?name=../secret.txt      -> 400 (fails the .png check)
```

**The exploit** — traverse to a target that *also* ends in `.png`:

```
GET /asset?name=../flag.png
```

`../flag.png` ends in `.png` (guard passes) and the `..` escapes `media/` to the
flag one level up. Let's send it.

With `curl`:

```bash
curl --path-as-is "http://localhost:5000/asset?name=../flag.png"
```

> **Why `--path-as-is`?** It stops curl from normalising `../` away before the
> request is sent, so the server actually receives the traversal and its guard
> is what you're testing.

Expected output: the raw bytes of `flag.png`. It is a tiny text file wearing a
`.png` name, so you can read the flag directly:

```
FLAG{MEDIALOFT_OUT_OF_BOUNDS}
```

> **Where does the flag come from?** It is **not** in the repo — it is baked into
> the Docker image at build time at `/app/flag.png`, one level above `media/`
> (see the `Dockerfile`). It ends in `.png` precisely so the extension guard
> lets you reach it.

<br>

## 🚀 Going further

The extension guard blocks non-`.png` targets, so you can't directly grab
`/etc/passwd` here — a nice illustration that the check *does* something, just
not containment. If the app also served other extensions (or you could smuggle
one), the same traversal would reach anything. Think about how a content-type or
magic-byte check would fare against the same payload (answer: no better — they
check the *kind*, not the *location*).

> Inside the hardened container the exploit runs as a non-root user — the blast
> radius is deliberately small. That containment is why we run labs in Docker.

<br>

## 🛠️ Doing it in Burp Suite

Prefer a proxy-driven workflow? This mirrors a real engagement:

1. Proxy your browser through Burp and load <http://localhost:5000>.
2. Let an image load and capture the `/asset?name=` request in **Proxy > HTTP
   history**. Send it to **Repeater** and re-send for a **baseline**.
3. Try `name=../secret.txt` — blocked (400). A filter exists; identify what it
   checks (the suffix).
4. Change `name` to `../flag.png` and send. Guard passes, traversal escapes, the
   flag comes back.
5. (Optional) With **Intruder**, fuzz the parameter but keep a `.png` suffix on
   your payloads to stay past the guard.

> If a `../` payload fails in Repeater but works in `curl --path-as-is`, Burp's
> path normalisation is the usual culprit — inspect the raw request.

<br>

## 🛡️ The fix

An extension check is orthogonal to containment — keep it if you like, but it is
**not** the security control. **Resolve** the path and **verify** it stays inside
the media directory:

```python
import os
from flask import abort, send_file

def safe_asset(media_dir: str, user_supplied: str) -> str:
    # Extension check (optional, for content policy — NOT for containment):
    if not user_supplied.endswith(".png"):
        abort(400)

    # The real control: resolve, then confirm the path is inside media_dir.
    full = os.path.realpath(os.path.join(media_dir, user_supplied))
    base = os.path.realpath(media_dir)
    if os.path.commonpath([full, base]) != base:
        abort(403)
    return full
```

Why this works: `realpath` collapses the `..` *before* the check, so you
validate the path the OS will actually open; the `commonpath` boundary check is
what actually confines the request. The extension check is now just a
content-policy nicety, not load-bearing security.

### ⚠️ Tempting fixes that *don't* work

These are the traps specific to an extension-based design:

- **"Only allow `.png`, so we're safe."** This is the bug itself. The extension
  describes the *type*, never the *location*. `../flag.png` is a `.png`.
- **Stricter suffix checks (allow-list of extensions, regex on the end).** Still
  orthogonal to traversal — any allowed extension can ride a `../`.
- **Sniffing content-type / magic bytes instead.** Same category error: it
  verifies *what* the file is, not *where* it is.
- **Blocking the literal `..`.** A blocklist, and encodings defeat it — you'll
  see an encoding-timing bypass in
  **[ziphaven (Level 5)](https://github.com/iv0ks/ziphaven)**.

> Series thread: **[deskmint (Level 3)](https://github.com/iv0ks/deskmint)** tried
> to *filter* `..`; Medialoft validates a different property and still misses the
> boundary. Next, **ziphaven** gets the validation *order* wrong — filtering
> before decoding.

### ✅ Even better: don't build paths from user input at all

- **Opaque IDs.** Serve assets by a server-side ID mapped to a real path.
- **Allow-list.** Accept only names you explicitly know
  (`if name not in LISTED_IMAGES: abort(404)`).
- **Use a vetted helper.** Flask's
  [`send_from_directory`](https://flask.palletsprojects.com/en/latest/api/#flask.send_from_directory)
  performs the safe-join boundary check for you.

<br>

## 🎓 Key takeaways

If you remember five things from this lab, make it these:

1. **Validate the right property.** Type checks (extension, MIME, magic bytes)
   are not location checks. Only a boundary check confines a path.
2. **An extension rides along.** `../flag.png` is "a `.png`" *and* a traversal.
3. **Resolve, then check.** Canonicalise with `realpath` *before* validating,
   and fail closed if the result escapes the base directory.
4. **A filter that blocks *something* can lull you.** Rejecting `.txt` made the
   guard look real; always ask what it *doesn't* stop.
5. **Defence in depth matters.** Non-root + container didn't *fix* the bug, but
   it kept the blast radius small.

That's Level 4 — the right check for the wrong question. Head back to the
**[Learning Guide](GUIDE.md)** for the method, or the **[README](README.md)** for
the lab setup.
