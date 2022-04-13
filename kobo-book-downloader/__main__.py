from Commands import Commands
from Globals import Globals
from Kobo import Kobo, KoboException
from LogFormatter import LogFormatter
from Settings import Settings

import colorama
import requests

import argparse
import logging

def InitializeGlobals() -> None:
	streamHandler = logging.StreamHandler()
	streamHandler.setFormatter( LogFormatter() )
	Globals.Logger = logging.getLogger()
	Globals.Logger.addHandler( streamHandler )

	Globals.Kobo = Kobo()
	Globals.Settings = Settings()

def InitializeKoboApi() -> None:
	if not Globals.Settings.AreAuthenticationSettingsSet():
		Globals.Kobo.AuthenticateDevice()

	Globals.Kobo.LoadInitializationSettings()

	if not Globals.Settings.IsLoggedIn():
		email = input( "Waiting for your input. You can use Shift+Insert to paste from the clipboard. Ctrl+C aborts the program.\n\nKobo e-mail: " )
		password = input( "Kobo password: " )

		print( """
Open https://authorize.kobo.com/signin in a private/incognito window in your browser, wait till the page
loads (do not login!) then open the developer tools (use F12 in Firefox/Chrome), select the console tab,
and paste the following code there and then press Enter there in the browser.

var newCaptchaDiv = document.createElement( "div" );
newCaptchaDiv.id = "new-hcaptcha-container";
document.getElementById( "hcaptcha-container" ).insertAdjacentElement( "afterend", newCaptchaDiv );
hcaptcha.render( newCaptchaDiv.id, {
	sitekey: "51a1773a-a9ae-4992-a768-e3b8d87355e8",
	callback: function( response ) { console.log( "Captcha response:" ); console.log( response ); }
} );

A captcha should show up below the Sign-in form. Once you solve the captcha its response will be written
below the pasted code in the browser's console. Copy the response (the line below "Captcha response:")
and paste it here.
""" )

		captcha = input( "Captcha response: " ).strip()

		print( "" )

		Globals.Kobo.Login( email, password, captcha )

def Main() -> None:
	InitializeGlobals()
	colorama.init()

	argumentParser = argparse.ArgumentParser( add_help = False )
	argumentParser.add_argument( "--help", "-h", default = False, action = "store_true" )
	argumentParser.add_argument( "--verbose", default = False, action = "store_true", dest = "VerboseLogging" )
	subparsers = argumentParser.add_subparsers( dest = "Command", title = "commands", metavar = "command" )
	getParser = subparsers.add_parser( "get", help = "Download book" )
	getParser.add_argument( "OutputPath", metavar = "output-path", help = "If the output path is a directory then the file will be named automatically." )
	getParser.add_argument( "RevisionId", metavar = "book-id", nargs = "?", help = "The identifier of the book" )
	getParser.add_argument( "--all", default = False, action = "store_true", help = "Download all my books" )
	infoParser = subparsers.add_parser( "info", help = "Show the location of the program's configuration file" )
	listParser = subparsers.add_parser( "list", help = "List unread books" )
	listParser.add_argument( "--all", default = False, action = "store_true", help = "List read books too" )
	pickParser = subparsers.add_parser( "pick", help = "Download books using interactive selection" )
	pickParser.add_argument( "OutputPath", metavar = "output-path", help = "Output path must be an existing directory" )
	pickParser.add_argument( "--all", default = False, action = "store_true", help = "List read books too" )
	wishListParser = subparsers.add_parser( "wishlist", help = "List your wish listed books" )
	arguments = argumentParser.parse_args()

	if arguments.VerboseLogging:
		Globals.Logger.setLevel( logging.DEBUG )

	if arguments.Command is None:
		Commands.ShowUsage()
	elif arguments.Command == "info":
		Commands.Info()
	else:
		InitializeKoboApi()

		if arguments.Command == "get":
			Commands.GetBookOrBooks( arguments.RevisionId, arguments.OutputPath, arguments.all )
		elif arguments.Command == "list":
			Commands.ListBooks( arguments.all )
		elif arguments.Command == "pick":
			Commands.PickBooks( arguments.OutputPath, arguments.all )
		elif arguments.Command == "wishlist":
			Commands.ListWishListedBooks()

if __name__ == '__main__':
	try:
		Main()
	except KoboException as e:
		Globals.Logger.error( e )
	except requests.exceptions.Timeout as e:
		Globals.Logger.error( "The request has timed out." )
