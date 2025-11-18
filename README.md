## kobo-book-downloader

With kobo-book-downloader you can download your purchased [Kobo](https://www.kobo.com/) books and remove the Digital Rights Management (DRM) protection from them. The resulting [EPUB](https://en.wikipedia.org/wiki/EPUB) files can be read with, amongst others, [KOReader](https://github.com/koreader/koreader).

Unlike [obok.py](https://github.com/apprenticeharper/DeDRM_tools/blob/master/Other_Tools/Kobo/obok.py), kobo-book-downloader doesn't require any pre-downloading through a Kobo e-reader or application.

kobo-book-downloader is a command line program. It looks like this:

![Screenshot](https://raw.githubusercontent.com/TnS-hun/kobo-book-downloader/master/screenshot.png)

### Overview

- Download and decrypt your purchased Kobo books to standard EPUB files.
- Run as a Python CLI **or** as a Docker container with a small Flask web UI.
- Designed for NAS/Docker hosts (for example Unraid), but works anywhere Docker runs.

## Container & Web UI

This repository (`chemicalsno/kobo-book-downloader`) is a Docker and web
UI-focused fork of the original
[TnS-hun/kobo-book-downloader](https://github.com/TnS-hun/kobo-book-downloader).

It includes a Docker image plus a small Flask web UI to make activation and
downloading easier on NAS hosts (for example Unraid).

- Optional web UI controlled by `UI_ENABLED`.
- UI listens on `UI_PORT` (default `5000` from `.env.example`).
- Configuration is stored under `/config` inside the container.
- Downloaded books are written under `/downloads` inside the container.
- An Unraid icon is provided as `kobo-icon.svg` and referenced by the XML template.

### Quick start (docker-compose)

1. Copy `.env.example` to `.env` and adjust as needed:

   - `PUID` / `PGID`: user and group IDs for file ownership on the host.
   - `TZ`: your timezone (e.g. `America/Denver`).
   - `UI_ENABLED=true`: enable the web UI.
   - `UI_PORT=5000`: port exposed for the UI.
   - `KBD_COMMAND`: CLI command when `UI_ENABLED=false` (ignored in UI mode).

2. Start the container:

   ```bash
   ./build.sh
   docker-compose up -d
   ```

3. Open the web UI in your browser:

   ```
   http://localhost:5000/?tab=auth
   ```

### Web UI overview

- **Authentication tab**
  - Shows whether the device is authenticated and whether you are logged in.
  - Lets you start the Kobo web activation flow and check activation status.
  - Uses Kobo's official activation page (`kobo.com/activate`); your password is
    never stored, only access tokens.

- **Library tab**
  - Provides buttons to:
    - list unread books
    - list all books
    - download unread
    - download all
  - Shows a table of books when a list has been loaded.

### Unraid notes

- On Unraid, it is typical to run the container with `PUID=99` and `PGID=100`
  so that files are owned by `nobody:users`.
- Map host paths to the container like:
  - `/mnt/user/appdata/kobo-book-downloader` → `/config`
  - `/mnt/user/downloads/kobo` → `/downloads`
- Expose the UI port (for example `5000`) in the template and make sure
  `UI_ENABLED` is set to `true`.
- Once the container is running, open `http://[UNRAID-IP]:[PORT]/?tab=auth` to
  complete activation.

### Configuration & security

- The program stores its tokens and device information in a JSON file inside
  `/config` (typically `config/kobo-book-downloader.json` on the host).
- This file **will contain access tokens, device IDs, and user identifiers**.
- It is intentionally ignored by Git via `.gitignore` so it is not committed by
  accident.

If you have already created `config/kobo-book-downloader.json` before adding
the `.gitignore` rule and Git is tracking it, remove it from the index with:

```bash
git rm --cached config/kobo-book-downloader.json
```

## Installation

kobo-book-downloader requires [Python 3+](https://www.python.org/). Make sure that you have it installed. You can verify it by running `python --version` from the terminal.

Use Git to clone this repository or
[download it](https://github.com/chemicalsno/kobo-book-downloader/archive/master.zip)
as a zip. If you downloaded it as a zip then you have to extract it.

From your terminal enter the directory where kobo-book-downloader is then run `pip install -r requirements.txt` to install its dependencies.

It has been tested on Linux but it should work on other platforms too.

## Usage

To interactively select from your unread books to download:
```
python kobo-book-downloader pick /dir/
```
To interactively select from all of your books to download:
```
python kobo-book-downloader pick /dir/ --all
```
To list your unread books:
```
python kobo-book-downloader list
```
To list all your books:
```
python kobo-book-downloader list --all
```
To download a book:
```
python kobo-book-downloader get /dir/book.epub 01234567-89ab-cdef-0123-456789abcdef
```
To download a book and name the file automatically:
```
python kobo-book-downloader get /dir/ 01234567-89ab-cdef-0123-456789abcdef
```
To download all your books:
```
python kobo-book-downloader get /dir/ --all
```
To list all your books from your wish list:
```
python kobo-book-downloader wishlist
```
To show the location of the program's configuration file:
```
python kobo-book-downloader info
```
Running the program without any arguments will show the help:
```
python kobo-book-downloader
```
To get additional help for the **list** command (it works for **get** and **pick** too):
```
python kobo-book-downloader list --help
```

## Notes

kobo-book-downloader uses the same web-based activation method to login as the
Kobo e-readers. You will have to open an activation link -- that uses the
official [Kobo](https://www.kobo.com/) site -- in your browser and enter the
code, then you might need to login too if kobo.com asks you to. Once
kobo-book-downloader has successfully logged in, it won't ask for the
activation again. kobo-book-downloader doesn't store your Kobo password in any
form, it works with access tokens.

The DRM removal code is based on Physisticated's
[obok.py](https://github.com/apprenticeharper/DeDRM_tools/blob/master/Other_Tools/Kobo/obok.py).

The web UI layout and containerization were inspired in part by
[subdavis/kobo-book-downloader](https://github.com/subdavis/kobo-book-downloader).
