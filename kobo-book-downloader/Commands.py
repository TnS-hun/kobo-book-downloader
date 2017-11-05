from Globals import Globals
from Kobo import Kobo, KoboException

import colorama

import os

class Commands:
	# It wasn't possible to format the main help message to my liking, so using a custom one.
	# This was the most annoying:
	#
	# commands:
	#   command <-- absolutely unneeded text
	#     get     List unread books
	#     list    Get book
	#
	# See https://stackoverflow.com/questions/13423540/ and https://stackoverflow.com/questions/11070268/
	@staticmethod
	def ShowUsage():
		usage = \
"""Kobo book downloader and DRM remover

Usage:
  kobo-book-downloader [--help] command ...

Commands:
  get      Download book
  info     Show the location of the configuration file
  list     List your books

Optional arguments:
  -h, --help    Show this help message and exit

Examples:
  kobo-book-downloader get /dir/book.epub 01234567-89ab-cdef-0123-456789abcdef   Download book
  kobo-book-downloader get /dir/ 01234567-89ab-cdef-0123-456789abcdef            Download book and name the file automatically
  kobo-book-downloader get /dir/ --all                                           Download all your books
  kobo-book-downloader info                                                      Show the location of the program's configuration file
  kobo-book-downloader list                                                      List your unread books
  kobo-book-downloader list --all                                                List all your books
  kobo-book-downloader list --help                                               Get additional help for the list command (it works for get too)"""

		print( usage )

	@staticmethod
	def __GetBookAuthor( book: dict ) -> str:
		contributors = book.get( "ContributorRoles" )

		authors = []
		for contributor in contributors:
			role = contributor.get( "Role" )
			if role == "Author":
				authors.append( contributor[ "Name" ] )

		# Unfortunately the role field is not filled out in the data returned by the "library_sync" endpoint, so we only
		# use the first author and hope for the best. Otherwise we would get non-main authors too. For example Christopher
		# Buckley beside Joseph Heller for the -- terrible -- novel Catch-22.
		if len( authors ) == 0 and len( contributors ) > 0:
			authors.append( contributors[ 0 ][ "Name" ] )

		return " & ".join( authors )

	@staticmethod
	def __SanitizeFileName( fileName: str ) -> str:
		result = ""
		for c in fileName:
			if c.isalnum() or " ,;.!(){}[]#$'-+@_".find( c ) >= 0:
				result += c

		result = result.strip( " ." )
		result = result[ :100 ] # Limit the length -- mostly because of Windows. It would be better to do it on the full path using MAX_PATH.
		return result

	@staticmethod
	def __MakeFileNameForBook( book: dict ) -> str:
		fileName = ""

		author = Commands.__GetBookAuthor( book )
		if len( author ) > 0:
			fileName = author + " - "

		fileName += book[ "Title" ]
		fileName = Commands.__SanitizeFileName( fileName )
		fileName += ".epub"

		return fileName

	@staticmethod
	def __GetBook( revisionId: str, outputPath: str ) -> None:
		if os.path.isdir( outputPath ):
			book = Globals.Kobo.GetBookInfo( revisionId )
			fileName = Commands.__MakeFileNameForBook( book )
			outputPath = os.path.join( outputPath, fileName )
		else:
			parentPath = os.path.dirname( outputPath )
			if not os.path.isdir( parentPath ):
				raise KoboException( "The parent directory ('%s') of the output file must exist." % parentPath )

		print( "Downloading book to '%s'." % outputPath )
		Globals.Kobo.Download( revisionId, Kobo.DisplayProfile, outputPath )

	@staticmethod
	def __GetAllBooks( outputPath: str ) -> None:
		if not os.path.isdir( outputPath ):
			raise KoboException( "The output path must be a directory when downloading all books." )

		bookList = Globals.Kobo.GetMyBookList()

		for entitlement in bookList:
			newEntitlement = entitlement.get( "NewEntitlement" )
			if newEntitlement is None:
				continue

			bookMetadata = newEntitlement[ "BookMetadata" ]
			fileName = Commands.__MakeFileNameForBook( bookMetadata )
			outputFilePath = os.path.join( outputPath, fileName )

			print( "Downloading book to '%s'." % outputFilePath )
			Globals.Kobo.Download( bookMetadata[ "RevisionId" ], Kobo.DisplayProfile, outputFilePath )

	@staticmethod
	def GetBookOrBooks( revisionId: str, outputPath: str, getAll: bool ) -> None:
		revisionIdIsSet = ( revisionId is not None ) and len( revisionId ) > 0

		if getAll:
			if revisionIdIsSet:
				raise KoboException( "Got unexpected book identifier parameter ('%s')." % revisionId )

			Commands.__GetAllBooks( outputPath )
		else:
			if not revisionIdIsSet:
				raise KoboException( "Missing book identifier parameter. Did you mean to use the --all parameter?" )

			Commands.__GetBook( revisionId, outputPath )

	@staticmethod
	def __IsBookRead( newEntitlement: dict ) -> bool:
		readingState = newEntitlement.get( "ReadingState" )
		if readingState is None:
			return False

		statusInfo = readingState.get( "StatusInfo" )
		if statusInfo is None:
			return False

		status = statusInfo.get( "Status" )
		return status == "Finished"

	@staticmethod
	def ListBooks( listAll: bool ) -> None:
		colorama.init()

		bookList = Globals.Kobo.GetMyBookList()
		rows = []

		for entitlement in bookList:
			newEntitlement = entitlement.get( "NewEntitlement" )
			if newEntitlement is None:
				continue

			if ( not listAll ) and Commands.__IsBookRead( newEntitlement ):
				continue

			bookMetadata = newEntitlement[ "BookMetadata" ]
			rows.append( [ bookMetadata[ "RevisionId" ], bookMetadata[ "Title" ], Commands.__GetBookAuthor( bookMetadata ) ] )

		rows = sorted( rows, key = lambda columns: columns[ 1 ] )
		for columns in rows:
			revisionId = colorama.Style.DIM + columns[ 0 ] + colorama.Style.RESET_ALL
			title = colorama.Style.BRIGHT + columns[ 1 ] + colorama.Style.RESET_ALL
			author = columns[ 2 ]

			if len( author ) > 0:
				print( "%s \t %s by %s" % ( revisionId, title, author ) )
			else:
				print( "%s \t %s" % ( revisionId, title ) )

	@staticmethod
	def Info():
		print( "The configuration file is located at:\n%s" % Globals.Settings.SettingsFilePath )
