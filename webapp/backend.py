import logging
from typing import Dict, List
import sys
from pathlib import Path
import urllib.parse

import colorama

# Ensure the original CLI code directory is importable. In the container, the
# upstream project lives under /app/kobo-book-downloader, while this web UI
# code lives under /app/webapp.
ROOT_DIR = Path(__file__).resolve().parent.parent
CLI_DIR = ROOT_DIR / "kobo-book-downloader"
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

from Commands import Commands
from Globals import Globals
from Kobo import Kobo, KoboException
from LogFormatter import LogFormatter
from Settings import Settings


_initialized = False
_activation_check_url: str | None = None
_activation_code: str | None = None


def initialize_globals() -> None:
    """Initialize shared Globals for use in the web UI.

    This mirrors the CLI initialization but keeps it small and self-contained
    so we do not modify the original CLI entrypoint.
    """
    global _initialized
    if _initialized:
        return

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(LogFormatter())

    logger = logging.getLogger("kobo-webui")
    logger.addHandler(stream_handler)

    Globals.Logger = logger
    Globals.Settings = Settings()
    Globals.Kobo = Kobo()

    colorama.init()

    _initialized = True


def _ensure_kobo_api_ready() -> None:
    """Ensure device is authenticated, initialization loaded, and user logged in.

    This follows the same logic as the CLI InitializeKoboApi function.
    """

    initialize_globals()

    if not Globals.Settings.AreAuthenticationSettingsSet():
        Globals.Kobo.AuthenticateDevice()

    Globals.Kobo.LoadInitializationSettings()

    if not Globals.Settings.IsLoggedIn():
        Globals.Kobo.Login()


def get_auth_status() -> Dict[str, bool]:
    """Return basic authentication status flags for the Start tab."""
    initialize_globals()

    return {
        "auth_settings_set": Globals.Settings.AreAuthenticationSettingsSet(),
        "logged_in": Globals.Settings.IsLoggedIn(),
    }


def get_activation_state() -> Dict[str, object]:
    """Return any pending activation code and URL.

    This does not trigger a new activation; it only reports what has been
    started with start_activation.
    """

    return {
        "activation_code": _activation_code,
        "activation_url": "https://www.kobo.com/activate" if _activation_code else None,
        "has_activation": _activation_code is not None,
    }


def start_activation() -> Dict[str, object]:
    """Start the web-based activation flow using ActivateOnWeb.

    This returns an activation code for the user and stores the poll URL so
    that check_activation_once can later complete the login.
    """

    global _activation_check_url, _activation_code

    initialize_globals()

    # Ensure we have a device ID and initial auth tokens.
    if not Globals.Settings.AreAuthenticationSettingsSet():
        Globals.Kobo.AuthenticateDevice()

    activation_check_url, activation_code = Globals.Kobo.ActivateOnWeb()
    _activation_check_url = activation_check_url
    _activation_code = activation_code

    return {
        "activation_code": activation_code,
        "activation_url": "https://www.kobo.com/activate",
    }


def check_activation_once() -> Dict[str, object]:
    """Poll the activation endpoint once to see if login completed.

    If activation is complete, this will extract userId/userKey from the
    redirect URL and finalize authentication via AuthenticateDevice.
    """

    global _activation_check_url, _activation_code

    if not _activation_check_url:
        return {"status": "no_activation"}

    initialize_globals()

    response = Globals.Kobo.Session.post(_activation_check_url)
    response.raise_for_status()

    try:
        json_response = response.json()
    except Exception as exc:  # pragma: no cover
        Globals.Logger.debug("Activation check response was not JSON: %s", response.text)
        raise KoboException("Error checking the activation's status. The response is not JSON.") from exc

    status = json_response.get("Status", "Unknown")
    if status == "Complete":
        redirect_url = json_response["RedirectUrl"]
        parsed = urllib.parse.urlparse(redirect_url)
        parsed_queries = urllib.parse.parse_qs(parsed.query)
        user_id = parsed_queries["userId"][0]
        user_key = parsed_queries["userKey"][0]

        Globals.Settings.UserId = user_id
        # AuthenticateDevice will save updated tokens.
        Globals.Kobo.AuthenticateDevice(user_key)

        # Clear activation state.
        _activation_check_url = None
        _activation_code = None

        return {"status": "complete"}

    return {"status": status}


def list_books(list_all: bool) -> List[Dict[str, object]]:
    """Return a list of books for the Library tab.

    Each item is a dict with revision_id, title, author, and archived fields.
    """

    _ensure_kobo_api_ready()

    # Reuse the internal helper that already builds the book list.
    rows = Commands._Commands__GetBookList(list_all)  # type: ignore[attr-defined]

    result: List[Dict[str, object]] = []
    for revision_id, title, author, archived in rows:
        result.append(
            {
                "revision_id": revision_id,
                "title": title,
                "author": author,
                "archived": bool(archived),
            }
        )

    return result


def download_unread_books(output_dir: str) -> Dict[str, object]:
    """Download all unread, non-archived books to the given directory."""

    _ensure_kobo_api_ready()

    errors: List[str] = []
    count = 0

    rows = Commands._Commands__GetBookList(False)  # unread only
    for revision_id, _title, _author, _archived in rows:
        try:
            Commands.GetBookOrBooks(revision_id, output_dir, False)
            count += 1
        except KoboException as exc:  # pragma: no cover - simple error collection
            Globals.Logger.error(exc)
            errors.append(str(exc))

    return {"downloaded": count, "errors": errors}


def download_all_books(output_dir: str) -> Dict[str, object]:
    """Download all books (equivalent of CLI --all) to the given directory."""

    _ensure_kobo_api_ready()

    errors: List[str] = []

    try:
        Commands.GetBookOrBooks(None, output_dir, True)
    except KoboException as exc:  # pragma: no cover
        Globals.Logger.error(exc)
        errors.append(str(exc))

    return {"downloaded": "all", "errors": errors}
