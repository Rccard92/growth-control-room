"""Single source of truth for the application version.

It used to live in three places that had drifted apart: the FastAPI app said
0.1.0, the editorial generator stamped every AI log with 0.5.14-alpha, and the
changelog was at 0.5.32-alpha. Bump this constant together with CHANGELOG.md.
"""

APP_VERSION = "0.5.33-alpha"
