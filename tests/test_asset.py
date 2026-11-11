"""Tests for Medialoft's asset endpoint.

These document the app's behaviour executably:

* a listed ``.png`` asset is served,
* a non-``.png`` request is rejected by the extension check, and
* the *path traversal* (CWE-22, level 4) slips past the extension check,
  because the flag is stored as ``flag.png`` — ``../flag.png`` both ends in
  ``.png`` *and* escapes the media directory.

The exploit test deliberately asserts that the vulnerability is present — if
someone "fixes" it, the test turns red and flags that the lab no longer teaches
what it claims to.

The flag does NOT live in the repo (it is created inside the Docker image at
build time). The fixture builds a throwaway data root mirroring the runtime
layout — ``<root>/media/`` for served files and ``<root>/flag.png`` as the
traversal target — and points the app at it via the ``DATA_ROOT`` env var.
"""

from __future__ import annotations

import pytest

from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "aurora.png").write_text("fake-png-bytes-aurora\n")
    (media_dir / "ocean.png").write_text("fake-png-bytes-ocean\n")
    # The flag ends in .png on purpose — that is the whole point of level 4.
    (tmp_path / "flag.png").write_text("FLAG{MEDIALOFT_OUT_OF_BOUNDS}\n")
    # A non-.png secret the extension check is *supposed* to help protect.
    (tmp_path / "secret.txt").write_text("not reachable via the .png check\n")

    monkeypatch.setenv("DATA_ROOT", str(tmp_path))

    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_gallery_lists_images(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"aurora.png" in resp.data


def test_serves_listed_png(client):
    """The intended, happy-path asset request works."""
    resp = client.get("/asset?name=aurora.png")
    assert resp.status_code == 200
    assert b"fake-png-bytes-aurora" in resp.data


def test_non_png_is_rejected(client):
    """The extension check blocks non-.png names (the only thing it does)."""
    resp = client.get("/asset?name=../secret.txt")
    assert resp.status_code == 400
    assert b"Medialoft" in resp.data  # styled error page


def test_path_traversal_past_extension_check(client):
    """CWE-22 (level 4): ../flag.png ends in .png, passes the check, escapes."""
    resp = client.get("/asset?name=../flag.png")
    assert resp.status_code == 200
    assert b"FLAG{" in resp.data


def test_missing_name_returns_styled_400(client):
    resp = client.get("/asset")
    assert resp.status_code == 400
    assert b"Medialoft" in resp.data


def test_unknown_png_returns_styled_404(client):
    resp = client.get("/asset?name=nope.png")
    assert resp.status_code == 404
    assert b"Medialoft" in resp.data


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.data == b"ok"
