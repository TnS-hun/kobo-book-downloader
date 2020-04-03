import os
from typing import List, Union

import click
import colorama

from kobodl.globals import Globals
from kobodl.kobo import (
    Book,
    Kobo,
    KoboException,
    NotAuthenticatedException,
)
from kobodl.settings import User


def __GetBookAuthor(book: dict) -> str:
    contributors = book.get('ContributorRoles')

    authors = []
    for contributor in contributors:
        role = contributor.get('Role')
        if role == 'Author':
            authors.append(contributor['Name'])

    # Unfortunately the role field is not filled out in the data returned by the 'library_sync' endpoint, so we only
    # use the first author and hope for the best. Otherwise we would get non-main authors too. For example Christopher
    # Buckley beside Joseph Heller for the -- terrible -- novel Catch-22.
    if len(authors) == 0 and len(contributors) > 0:
        authors.append(contributors[0]['Name'])

    return ' & '.join(authors)


def __SanitizeFileName(fileName: str) -> str:
    result = ''
    for c in fileName:
        if c.isalnum() or ' ,;.!(){}[]#$\'-+@_'.find(c) >= 0:
            result += c

    result = result.strip(' .')
    result = result[
        :100
    ]  # Limit the length -- mostly because of Windows. It would be better to do it on the full path using MAX_PATH.
    return result


def __MakeFileNameForBook(bookMetadata: dict) -> str:
    '''filename without extension'''
    fileName = ''
    author = __GetBookAuthor(bookMetadata)
    if len(author) > 0:
        fileName = author + ' - '
    fileName += bookMetadata['Title']
    fileName = __SanitizeFileName(fileName)
    return fileName


def __GetBookMetadata(entitlement: dict) -> dict:
    keys = entitlement.keys()
    if 'BookMetadata' in keys:
        return entitlement['BookMetadata']
    if 'AudiobookMetadata' in keys:
        return entitlement['AudiobookMetadata']
    return None


def __IsBookArchived(newEntitlement: dict) -> bool:
    keys = newEntitlement.keys()
    if 'BookEntitlement' in keys:
        bookEntitlement = newEntitlement['BookEntitlement']
    if 'AudiobookEntitlement' in keys:
        bookEntitlement = newEntitlement['AudiobookEntitlement']
    return bookEntitlement.get('IsRemoved', False)


def __IsAudioBook(bookMetadata: dict) -> bool:
    return 'Duration' in bookMetadata.keys()


def __IsBookRead(newEntitlement: dict) -> bool:
    readingState = newEntitlement.get('ReadingState')
    if readingState is None:
        return False

    statusInfo = readingState.get('StatusInfo')
    if statusInfo is None:
        return False

    status = statusInfo.get('Status')
    return status == 'Finished'


def __GetBookList(kobo: Kobo, listAll: bool) -> list:
    bookList = kobo.GetMyBookList()
    rows = []

    for entitlement in bookList:
        newEntitlement = entitlement.get('NewEntitlement')
        if newEntitlement is None:
            continue

        bookEntitlement = newEntitlement.get('BookEntitlement')
        if bookEntitlement is not None:
            # Skip saved previews.
            if bookEntitlement.get('Accessibility') == 'Preview':
                continue

            # Skip refunded books.
            if bookEntitlement.get('IsLocked'):
                continue

        if (not listAll) and __IsBookRead(newEntitlement):
            continue

        bookMetadata = __GetBookMetadata(newEntitlement)
        book = [
            bookMetadata['RevisionId'],
            bookMetadata['Title'],
            __GetBookAuthor(bookMetadata),
            __IsBookArchived(newEntitlement),
            __IsAudioBook(bookMetadata),
        ]
        rows.append(book)

    rows = sorted(rows, key=lambda columns: columns[1].lower())
    return rows


def ListBooks(users: List[User], listAll: bool) -> List[Book]:
    '''list all books currently in the account'''
    for user in users:
        kobo = Kobo(user)
        kobo.LoadInitializationSettings()
        rows = __GetBookList(kobo, listAll)
        for columns in rows:
            yield Book(
                RevisionId=columns[0],
                Title=columns[1],
                Author=columns[2],
                Archived=columns[3],
                Audiobook=columns[4],
                Owner=user,
            )


def Login(user: User, password: str, captcha: str) -> None:
    '''perform device initialization and get token'''
    kobo = Kobo(user)
    kobo.AuthenticateDevice()
    kobo.LoadInitializationSettings()
    kobo.Login(user.Email, password, captcha)


def GetBookOrBooks(
    user: User, outputPath: str, productId: str = ''
) -> Union[None, str]:
    '''
    download 1 or all books to file
    returns output filepath if identifier is passed, otherwise returns None
    '''
    kobo = Kobo(user)
    kobo.LoadInitializationSettings()

    # Must call GetBookList every time, even if you're only getting 1 book,
    # because it invokes a library sync endpoint.
    # This is the only known endpoint that returns
    # download URLs along with book metadata.
    bookList = kobo.GetMyBookList()

    for entitlement in bookList:
        newEntitlement = entitlement.get('NewEntitlement')
        if newEntitlement is None:
            continue

        bookMetadata = __GetBookMetadata(newEntitlement)
        isAudiobook = __IsAudioBook(bookMetadata)
        fileName = __MakeFileNameForBook(bookMetadata)
        outputFilePath = os.path.join(outputPath, fileName)

        if productId and productId != Kobo.GetProductId(bookMetadata):
            # user only asked for a single title,
            # and this is not the book they want
            continue

        # Skip archived books.
        if __IsBookArchived(newEntitlement):
            click.echo(f'Skipping archived book {fileName}')
            continue

        kobo.Download(bookMetadata, isAudiobook, outputFilePath)
        click.echo(f'Downloaded {productId} to {outputFilePath}', err=True)

        if productId:
            # TODO: support audiobook downloads from web
            return outputFilePath + ".epub"

    return None
