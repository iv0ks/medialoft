"""Medialoft configuration — static defaults.

These are pure constants. The actual runtime paths (which depend on the
``DATA_ROOT`` env var) are resolved by the application factory in
``app.main.create_app`` and stored on ``app.config``, so nothing here reads the
environment at import time. That keeps the app easy to test: each ``create_app``
call can be pointed at a different data root.

Runtime layout (resolved in the factory):

    <data_root>/           <- DATA_ROOT   (holds flag.png, the target)
    <data_root>/media/     <- MEDIA_DIR   (the served image CDN)
"""

from __future__ import annotations

import os

# Repo root is one level above the app/ package. Used as the DATA_ROOT default.
DEFAULT_DATA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Name of the sub-directory (under DATA_ROOT) the CDN serves images from.
MEDIA_DIRNAME = "media"

# The only extension the CDN "allows". The vulnerability is that checking the
# extension does nothing to stop path traversal — an attacker just needs their
# target to end in .png (see the flag below).
ALLOWED_EXTENSION = ".png"

# The challenge flag. It is the *target* of the path traversal and lives at
# <DATA_ROOT>/flag.png (one level above the served media/). It deliberately ends
# in .png so it satisfies the extension check — that is the whole lesson of this
# level. It is intentionally not committed to the repo; the app seeds it on
# startup if missing (and the Docker image also writes it at build time).
FLAG_FILENAME = "flag.png"
DEFAULT_FLAG = "FLAG{MEDIALOFT_OUT_OF_BOUNDS}"

# Images shown on the CDN dashboard so the app behaves like a real product.
LISTED_IMAGES = [
    "aurora.png",
    "cityscape.png",
    "desert.png",
    "forest.png",
    "ocean.png",
    "peaks.png",
]
