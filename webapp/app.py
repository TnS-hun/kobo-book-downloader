from __future__ import annotations

import os
from typing import List, Dict

from flask import Flask, render_template, request, redirect, url_for, flash

from . import backend


def create_app() -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__)
    # Simple secret key for flash messages; users can override via env in the future if desired.
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "kobo-book-downloader-secret")

    @app.route("/")
    def index() -> str:
        """Render main page with auth status and optional book list."""

        backend.initialize_globals()
        status = backend.get_auth_status()
        activation_state = backend.get_activation_state()
        logged_in = bool(status.get("logged_in", False))

        # Determine which tab is active. Default to the authentication tab.
        tab = request.args.get("tab") or "auth"
        if tab not in {"auth", "library"}:
            tab = "auth"

        # Load books only if explicitly requested via query parameter to avoid
        # triggering Kobo API calls on every page load.
        books: List[Dict[str, object]] = []
        books_mode = request.args.get("books")
        if books_mode in {"unread", "all"}:
            # When listing books, always show the Library tab.
            tab = "library"
            if not logged_in:
                flash("You must complete activation/login before listing books.", "error")
            else:
                list_all = books_mode == "all"
                try:
                    books = backend.list_books(list_all=list_all)
                except Exception as exc:  # pragma: no cover
                    flash(f"Error loading books: {exc}", "error")

        return render_template(
            "index.html",
            auth_settings_set=status.get("auth_settings_set", False),
            logged_in=logged_in,
            activation_state=activation_state,
            books=books,
            books_mode=books_mode,
            active_tab=tab,
        )

    @app.post("/activation/start")
    def activation_start() -> str:
        """Start the Kobo web activation flow."""

        try:
            result = backend.start_activation()
            code = result.get("activation_code")
            if code:
                flash(f"Activation started. Code: {code}", "info")
            else:
                flash("Activation started.", "info")
        except Exception as exc:  # pragma: no cover
            flash(f"Error starting activation: {exc}", "error")

        return redirect(url_for("index"))

    @app.post("/activation/check")
    def activation_check() -> str:
        """Check whether the Kobo web activation has completed."""

        try:
            result = backend.check_activation_once()
            status = result.get("status")
            if status == "complete":
                flash("Activation complete. You are now logged in.", "info")
            elif status == "no_activation":
                flash("No activation in progress. Start activation first.", "error")
            else:
                flash(f"Activation status: {status}", "info")
        except Exception as exc:  # pragma: no cover
            flash(f"Error checking activation: {exc}", "error")

        return redirect(url_for("index"))

    @app.post("/download/unread")
    def download_unread() -> str:
        """Download all unread books to /downloads."""

        status = backend.get_auth_status()
        if not bool(status.get("logged_in", False)):
            flash("You must complete activation/login before downloading books.", "error")
            # Redirect back to the authentication tab so the user can fix it.
            return redirect(url_for("index", tab="auth"))

        try:
            result = backend.download_unread_books("/downloads")
            downloaded = result.get("downloaded")
            errors = result.get("errors") or []
            msg = f"Downloaded {downloaded} unread books to /downloads."
            if errors:
                msg += f" {len(errors)} errors encountered."
            flash(msg, "info")
        except Exception as exc:  # pragma: no cover
            flash(f"Error downloading unread books: {exc}", "error")

        return redirect(url_for("index", books="unread", tab="library"))

    @app.post("/download/all")
    def download_all() -> str:
        """Download all books to /downloads."""

        status = backend.get_auth_status()
        if not bool(status.get("logged_in", False)):
            flash("You must complete activation/login before downloading books.", "error")
            return redirect(url_for("index", tab="auth"))

        try:
            result = backend.download_all_books("/downloads")
            errors = result.get("errors") or []
            msg = "Requested download of all books to /downloads."
            if errors:
                msg += f" {len(errors)} errors encountered."
            flash(msg, "info")
        except Exception as exc:  # pragma: no cover
            flash(f"Error downloading all books: {exc}", "error")

        return redirect(url_for("index", books="all", tab="library"))

    return app


def main() -> None:
    app = create_app()
    port = int(os.environ.get("UI_PORT", "5000"))
    # Use 0.0.0.0 so the container port mapping works.
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":  # pragma: no cover
    main()
