from Commands import Commands
from Globals import Globals
from Kobo import Kobo, KoboException
from Settings import Settings

import argparse

def Initialize():
	Globals.Kobo = Kobo()
	Globals.Settings = Settings()

	if not Globals.Settings.AreAuthenticationSettingsSet():
		Globals.Kobo.AuthenticateDevice()

	Globals.Kobo.LoadInitializationSettings()

	if not Globals.Settings.IsLoggedIn():
		email = input( "Waiting for your input. You can use Shift+Insert to paste from the clipboard. Ctrl+C aborts the program.\n\nKobo e-mail: " )
		password = input( "Kobo password: " )
		Globals.Kobo.Login( email, password )

def Main() -> None:
	argumentParser = argparse.ArgumentParser( add_help = False )
	argumentParser.add_argument( "--help", "-h", default = False, action = "store_true" )
	subparsers = argumentParser.add_subparsers( dest = "Command", title = "commands", metavar = "command" )
	getParser = subparsers.add_parser( "get", help = "Download book" )
	getParser.add_argument( "OutputPath", metavar = "output-path", help = "If the output path is a directory then the file will be named automatically." )
	getParser.add_argument( "RevisionId", metavar = "book-id", nargs = "?", help = "The identifier of the book" )
	getParser.add_argument( "--all", default = False, action = "store_true", help = "Download all my books" )
	infoParser = subparsers.add_parser( "info", help = "Show the location of the program's configuration file" )
	listParser = subparsers.add_parser( "list", help = "List unread books" )
	listParser.add_argument( "--all", default = False, action = "store_true", help = "List read books too" )
	arguments = argumentParser.parse_args()

	if arguments.Command is None:
		Commands.ShowUsage()
		return

	Initialize()

	if arguments.Command == "get":
		Commands.GetBookOrBooks( arguments.RevisionId, arguments.OutputPath, arguments.all )
	elif arguments.Command == "info":
		Commands.Info()
	elif arguments.Command == "list":
		Commands.ListBooks( arguments.all )


if __name__ == '__main__':
	try:
		Main()
	except KoboException as e:
		print( "ERROR: %s" % e )
