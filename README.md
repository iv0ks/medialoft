# Medialoft

![CWE-22](https://img.shields.io/badge/CWE--22-Path%20Traversal-red?style=flat-square)
![Python](https://img.shields.io/badge/Python-Flask-blue?style=flat-square&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Lab-Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
[![GHCR](https://img.shields.io/badge/ghcr.io-iv0ks%2Fmedialoft-blue?logo=docker)](https://github.com/iv0ks/medialoft/pkgs/container/medialoft)

**Medialoft is an intentionally vulnerable application built for security education.** It is a small image CDN with a deliberate [path traversal](https://owasp.org/www-community/attacks/Path_Traversal)
(CWE-22) flaw — it only checks that the requested file ends in `.png`, which does nothing to stop traversal — so you can practice finding and exploiting it in a safe and controlled environment.

<br>

<div align="center">

| 🛡️ Vulnerability | 🎯 Difficulty | 🛠️ Stack | 🚩 Entry point |
| :--- | :--- | :--- | :--- |
| Path Traversal (CWE-22) | ⭐⭐⭐⭐ Level 4 (Extension check) | Python · Flask | `GET /asset?name=<file>.png` |

</div>

<br>

> [!NOTE]
> The guided, spoiler-free path is [GUIDE.md](GUIDE.md); the full answer waits in [SOLUTION.md](SOLUTION.md) whenever you want it.

<br>

## 📂 Project layout

The repository is organised so the vulnerable code is easy to find and reason
about. Three areas, clearly separated: the **application** itself in `app/`
(a small Flask app split into factory, routes and config), the **served data**
in `media/` (the directory the CDN is _meant_ to expose), and the **tooling**
around it (Docker, CI/CD, linters). The challenge flag is deliberately kept
_out_ of both the repo and the served directory — see the note under the tree.

```
medialoft/
├── app/                    # the application package (the bug lives here)
│   ├── main.py             # Flask app factory (resolves paths, error handlers)
│   ├── routes.py           # routes — the vulnerable asset endpoint
│   ├── config.py           # static defaults (dir name, allowed extension)
│   ├── static/
│   │   └── style.css       # CDN UI styles (dark media-library theme)
│   └── templates/
│       ├── gallery.html    # asset library UI
│       └── error.html      # styled error page
├── media/                  # the served images (the "allowed" directory)
│   └── *.png               # six real PNGs (generated, see tools/)
├── tools/                  # image + favicon generators (Pillow, build-time)
├── tests/                  # exploit + happy-path tests (pytest)
├── SOLUTION.md             # exploit writeup + the fix (spoilers)
├── SECURITY.md             # security policy (it's a lab — read before reporting)
├── .github/workflows/      # integration · delivery · security · release
├── Dockerfile              # hardened multi-stage image (creates the flag)
├── docker-compose.yml      # medialoft + traefik stack
├── pyproject.toml          # ruff + black + pytest config, packaging
└── requirements.txt
```

The application code lives in `app/` and serves its images from `media/`, just
like a real CDN would. The target `flag.png` is **not** in the repo: the
`Dockerfile` writes it to `/app/flag.png` at build time — _outside_ the served
`media/` dir, and ending in `.png` so it satisfies the extension check — so
traversal can reach it while the flag stays out of version control.

<br>

## 🚀 The Lab

Medialoft runs as a Docker Compose stack:

- **`medialoft`** — the Flask CDN (gunicorn), published on port `5000`.
- **`traefik`** — a reverse proxy that serves the app over HTTPS on a real
  hostname. Optional: only needed for the domain-based access.

Because the stack attaches to an **external** Docker network (`iv0ks-dev`),
create it once before the first run:

```bash
docker network create iv0ks-dev
```

<br>

#### Option A — just the app (quickest)

```bash
docker compose up -d --build medialoft
```

Reachable directly at **<http://localhost:5000>**. That is all you need for Burp.

<br>

#### Option B — full stack with Traefik (HTTPS + hostname)

```bash
docker compose up -d --build
```

Now the _same_ app is reachable two ways at once:

- **<http://localhost:5000>** — direct, no TLS.
- **<https://medialoft.iv0ks.dev>** — proxied by Traefik with a real certificate.

<br>

> [!CAUTION]
> The `medialoft.iv0ks.dev` hostname must resolve to the host running the stack.
> For purely local experiments, Option A (localhost) is simpler and needs no
> DNS or certificates.

<br>

#### Running without cloning (prebuilt image)

```bash
docker run --rm -p 5000:5000 ghcr.io/iv0ks/medialoft:latest
```

<br>

#### Developing without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flask --app app.main run --port 5000 --debug
```

> The app finds its data via the `DATA_ROOT` env var, defaulting to the repo
> root (it serves `<DATA_ROOT>/media/` and the flag is at `<DATA_ROOT>/flag.png`).
> The flag is provisioned at runtime (seeded on startup / baked into the image),
> never committed. Override it with the `FLAG` env var (or `--build-arg FLAG=`).

<br>

## 🎯 The Challenge

### The Scenario

Medialoft is an image CDN: it serves assets from a `media/` library and, to be
"safe", only serves files whose name ends in `.png`. The developer treats that
extension check as the gate that keeps requests inside the library. You're
going to prove an extension is not a location.

### Your objective

Read a file that lives _outside_ the media directory — specifically, capture the flag in `flag.png`.

> [!NOTE]
> The flag has the format `FLAG{...}`. It is stored as `flag.png` — yes, it ends
> in `.png` on purpose.

### The rules

Everything happens over HTTP against the running app — no need to
read the source to win (though you can). The flag is **not** in the repo: it's
baked into the container, outside `media/`, so you have to actually reach it.

> [!TIP]
> For the full method, the **[Learning Guide](GUIDE.md)** walks you through it.
