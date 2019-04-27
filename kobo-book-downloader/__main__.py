from Commands import Commands
from Globals import Globals
from Kobo import Kobo, KoboException
from Settings import Settings

import argparse

def Initialize() -> None:
	Globals.Kobo = Kobo()
	Globals.Settings = Settings()

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
newCaptchaDiv.id = "new-grecaptcha-container";
document.getElementById( "grecaptcha-container" ).insertAdjacentElement( "afterend", newCaptchaDiv );
grecaptcha.render( newCaptchaDiv.id, {
	sitekey: "6LeEbUwUAAAAADJxtlhMsvgnR7SsFpMm4sirr1CJ",
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
