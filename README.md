# Medialoft

[![GHCR](https://img.shields.io/badge/ghcr.io-iv0ks%2Fmedialoft-blue?logo=docker)](https://github.com/iv0ks/medialoft/pkgs/container/medialoft)


**Medialoft is an intentionally vulnerable application built for security education.** It is a small image CDN with a deliberate [path traversal](https://owasp.org/www-community/attacks/Path_Traversal)
(CWE-22) flaw — it only checks that the requested file ends in `.png`, which does nothing to stop traversal — so you can practice finding and exploiting it in a safe and controlled environment.

<br>

## 🗂️ Project layout

The repository is organised so the vulnerable code is easy to find and reason
about. Three areas, clearly separated: the **application** itself in `app/`
(a small Flask app split into factory, routes and config), the **served data**
in `media/` (the directory the CDN is *meant* to expose), and the **tooling**
around it (Docker, CI/CD, linters). The challenge flag is deliberately kept
*out* of both the repo and the served directory — see the note under the tree.

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
`Dockerfile` writes it to `/app/flag.png` at build time — *outside* the served
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

#### Option A — just the app (quickest)

```bash
docker compose up -d --build medialoft
```

Reachable directly at **<http://localhost:5000>**. That is all you need for Burp.

#### Option B — full stack with Traefik (HTTPS + hostname)

```bash
docker compose up -d --build
```

Now the *same* app is reachable two ways at once:

- **<http://localhost:5000>** — direct, no TLS.
- **<https://medialoft.iv0ks.dev>** — proxied by Traefik with a real certificate.

#### Running without cloning (prebuilt image)

```bash
docker run --rm -p 5000:5000 ghcr.io/iv0ks/medialoft:latest
```

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

Medialoft only serves files ending in `.png` from its media library. Your goal:

> **Read a file that lives _outside_ the media directory — specifically,
> capture the flag stored in `flag.png`.**

The flag has the format `FLAG{...}`.

| | |
|---|---|
| **Vulnerability** | Path Traversal (CWE-22) |
| **Difficulty** | ⭐⭐⭐⭐ Level 4 — file-extension check bypass |
| **Stack** | Python · Flask · gunicorn |
| **Entry point** | `GET /asset?name=<file>.png` |

<details>
<summary>Hint 1</summary>
Try a plain <code>../</code> traversal to a <code>.txt</code> file — it is
rejected. So there <em>is</em> a filter. What exactly is it checking?
</details>

<details>
<summary>Hint 2</summary>
The guard only looks at how the name <em>ends</em>. Does an extension check
stop <code>../</code> sequences? What if your target also ends in
<code>.png</code>?
</details>

A full walkthrough lives in [SOLUTION.md](SOLUTION.md) (spoilers!).

<br>

## 🧰 About this repo (DevSecOps showcase)

Beyond the vulnerability, this repo is a template for shipping a small service
with sane engineering practices:

- **Conventional Commits** enforced via **commitlint** (pre-commit hook).
- **pre-commit** suite: `ruff`, `black`, `gitleaks`, `hadolint`, whitespace/EOF.
- **Centralized CI/CD** via reusable workflows in
  [`iv0ks/cicd-hub`](https://github.com/iv0ks/cicd-hub): Integration
  (secrets → vuln → lint → tests on PR), Delivery (build & push the image to
  GHCR on tag), Security (scheduled CVE scan), Release (release-please).
- **Dependabot**: daily updates for pip, Docker and GitHub Actions.
- **Hardened container**: multi-stage build, non-root user, read-only root
  filesystem, dropped capabilities.

> 💡 **Teaching note:** image/dependency scanners look for *known CVEs*. They
> will **not** flag Medialoft's path traversal, because it is a business-logic
> flaw in our own code, not a vulnerable dependency. Catching that class of bug
> needs SAST / manual review / DAST — exactly what you're practicing here.

### Running the tests

```bash
pip install -r requirements.txt pytest
pytest
```

The suite documents the behaviour executably: a listed `.png` is served, a
non-`.png` request is rejected, and `../flag.png` slips past the extension
check and reads the flag — so if someone "fixes" the bug, the exploit test
turns red.

<br>

## 📄 License

[MIT](LICENSE) — see also [SECURITY.md](SECURITY.md).
