# Kobodl

This is a hard fork of [kobo-book-downloader](https://github.com/TnS-hun/kobo-book-downloader), a command line tool to download and remove Digital Rights Management (DRM) protection from media legally purchased from [Rakuten Kobo](https://www.kobo.com/). The resulting [EPUB](https://en.wikipedia.org/wiki/EPUB) files can be read with, amongst others, [KOReader](https://github.com/koreader/koreader).

## Features

kobodl preserves the features from `kobo-book-downloader` :

* stand-alone; no need to run other software or pre-download through an e-reader.
* downloads `.epub` formatted books

it adds some new feautres

* multi-user support; fetch books for multiple accounts.
* web interface; adds new browser gui (todo)
* [docker image](https://hub.docker.com/r/subdavis/kobodl)
* [pypi package](https://pypi.org/project/kobodl/)

## Installation

with pipx

``` bash
pipx install kobodl
```

with pypi

``` bash
pip3 install kobodl
```

with docker

``` bash
docker run --rm -it --user $(id -u):$(id -g) \
  -v ${HOME}/.config/kobodl.json:/.config/kobodl.json subdavis/kobodl \
  user list
```

## Examples

Get started by adding one or more users

``` bash
~$ kobodl user add
```

List books from multiple accounts

``` bash
~$ kobodl book list

# +---------------------------------+-----------------------------+--------------------------------------+---------------------------+
# | Title                           | Author                      | RevisionId                           | Owner                     |
# |---------------------------------+-----------------------------+--------------------------------------+---------------------------|
# | Dune                            | Frank Herbert               | c1db3f5c-82da-4dda-9d81-fa718d5d1d16 | user@example.com          |
# | Foundation                      | Isaac Asimov                | 3e12197c-681a-4a53-80b4-88fcdf61e936 | user@example.com          |
# | Girls Burn Brighter             | Shobha Rao                  | 1227cc03-7580-4469-81a5-b6558500832f | user@example.com          |
# | On Earth We're Briefly Gorgeous | Ocean Vuong                 | 4ccc68b1-3dac-433e-b05a-63ab0f93578f | other@domain.com          |
# | She Said                        | Jodi Kantor                 | 5d0872bf-8765-4654-9f90-aca4f54e5707 | other@domain.com          |
# +---------------------------------+-----------------------------+--------------------------------------+---------------------------+
```

Download a book

``` bash
~$ kobodl book get -u user@example.com c1db3f5c-82da-4dda-9d81-fa718d5d1d16

# Downloading book to kobo_downloads/Isaac Asimov - Foundation.epub
```

Show all help

``` bash
~$ kobodl --help

# Usage: kobodl [OPTIONS] COMMAND [ARGS]...
#
# Options:
#   --fmt TEXT
#   --version   Show the version and exit.
#   --help      Show this message and exit.
#
# Commands:
#   book  list and download books
#   user  user management
```

## Development

To get set up for development:

1. clone this repo
2. create a virtual environment (optional)
3. `pip3 install -e .` to install for development
4. `kobodl` should be available inside the virtual env

## Notes

kobo-book-downloader will prompt for your [Kobo](https://www.kobo.com/) e-mail address and password. Once it has successfully logged in, it won't ask for them again. Your password will not be stored on disk; Kobodl uses access tokens after the initial login.

Credit recursively to [kobo-book-downloader](https://github.com/TnS-hun/kobo-book-downloader) and the projects that lead to it.
