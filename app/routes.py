"""Medialoft HTTP routes.

The asset endpoint is intentionally vulnerable. It tries to be safe by only
serving files whose name ends in ``.png`` — but an extension check does nothing
to stop path traversal. Any ``..`` sequence still escapes the media directory,
and the attacker simply points at a target that ends in ``.png`` (the flag is
stored as ``flag.png``). This is a path traversal past an extension allow-list
(CWE-22, level 4) and is the whole point of this lab.

    GET /asset?name=aurora.png     -> serves media/aurora.png
    GET /asset?name=../flag.png    -> escapes the CDN (the flag) — still ".png"!
    GET /asset?name=../secret.txt  -> rejected (fails the .png check)

Paths come from ``current_app.config`` (set by the factory), so the routes
don't read the environment or import mutable globals.

Do NOT reuse this pattern in real software. See README.md for the disclaimer.
"""

from __future__ import annotations

import os

from flask import (
    Blueprint,
    Response,
    current_app,
    render_template,
    request,
    send_file,
)

bp = Blueprint("medialoft", __name__)


@bp.get("/")
def gallery() -> str:
    """Render the CDN dashboard listing the available images."""
    images = current_app.config["LISTED_IMAGES"]
    return render_template("gallery.html", images=images)


@bp.get("/asset")
def asset() -> Response:
    """Serve an image from the CDN.

    VULNERABLE BY DESIGN (level 4 — extension check): the only guard is that the
    requested name must end in ``.png``. That check does not normalize the path
    or confine it to the media directory, so ``../flag.png`` passes the check
    *and* escapes the directory (CWE-22).
    """
    name = request.args.get("name", "")
    if not name:
        return render_error(400, "Missing 'name' query parameter.")

    allowed_ext = current_app.config["ALLOWED_EXTENSION"]

    # --- The (ineffective) guard ---------------------------------------------
    # Only ".png" files are allowed... but an extension check is not a path
    # boundary. "../flag.png" ends in ".png", so it sails straight through.
    if not name.endswith(allowed_ext):
        return render_error(400, f"Only {allowed_ext} assets are served.")
    # -------------------------------------------------------------------------

    media_dir = current_app.config["MEDIA_DIR"]
    target_path = os.path.join(media_dir, name)

    if not os.path.isfile(target_path):
        return render_error(404, f"Asset not found: {name}")

    return send_file(target_path, as_attachment=False)


@bp.get("/healthz")
def healthz() -> Response:
    """Liveness probe used by Docker's HEALTHCHECK."""
    return Response("ok", mimetype="text/plain")


def render_error(status: int, message: str) -> Response:
    """Render the styled error page with the given status and message."""
    html = render_template("error.html", status=status, message=message)
    return Response(html, status=status, mimetype="text/html")
