from Globals import Globals
from KoboDrmRemover import KoboDrmRemover

import requests

from typing import Dict, Tuple
import base64
import html
import os
import re
import secrets
import string
import time
import urllib

# It was not possible to enter the entire captcha response on MacOS.
# Importing readline changes the implementation of input() and solves the issue.
# See https://stackoverflow.com/q/65735885 and https://stackoverflow.com/q/7357007.
import readline

class KoboException( Exception ):
	pass

# The hook's workflow is based on this:
# https://github.com/requests/toolbelt/blob/master/requests_toolbelt/auth/http_proxy_digest.py
def ReauthenticationHook( r, *args, **kwargs ):
	if r.status_code != requests.codes.unauthorized: # 401
		return

	Globals.Logger.debug( "Refreshing expired authentication token" )

	# Consume content and release the original connection to allow our new request to reuse the same one.
	r.content
	r.close()

	prep = r.request.copy()

	# Refresh the authentication token and use it.
	Globals.Kobo.RefreshAuthentication()
	headers = Kobo.GetHeaderWithAccessToken()
	prep.headers[ "Authorization" ] = headers[ "Authorization" ]

	# Don't retry to reauthenticate this request again.
	prep.deregister_hook( "response", ReauthenticationHook )

	# Resend the failed request.
	_r = r.connection.send( prep, **kwargs )
	_r.history.append( r )
	_r.request = prep

	return _r

class SessionWithTimeOut( requests.Session ):
	def request( self, method, url, **kwargs ):
		if "timeout" not in kwargs:
			kwargs[ "timeout" ] = 30 # 30 seconds
		return super().request( method, url, **kwargs )

class Kobo:
	Affiliate = "Kobo"
	ApplicationVersion = "4.38.23171"
	DefaultPlatformId = "00000000-0000-0000-0000-000000000373"
	DisplayProfile = "Android"
	DeviceModel = "Kobo Aura ONE"
	DeviceOs = "3.0.35+"
	DeviceOsVersion = "NA"

	def __init__( self ):
		headers = {
			# Use the user agent of the Kobo e-readers.
			"User-Agent": "Mozilla/5.0 (Linux; U; Android 2.0; en-us;) AppleWebKit/538.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/538.1 (Kobo Touch 0373/4.38.23171)",
		}

		self.InitializationSettings = {}
		self.Session = SessionWithTimeOut()
		self.Session.headers.update( headers )

	# This could be added to the session but then we would need to add { "Authorization": None } headers to all other
	# functions that doesn't need authorization.
	@staticmethod
	def GetHeaderWithAccessToken() -> dict:
		authorization = "Bearer " + Globals.Settings.AccessToken
		headers = { "Authorization": authorization }
		return headers

	# This could be added to the session too. See the comment at GetHeaderWithAccessToken.
	@staticmethod
	def __GetReauthenticationHook() -> dict:
		return { "response": ReauthenticationHook }

	@staticmethod
	def __GenerateRandomHexDigitString( length: int ) -> str:
		id = "".join( secrets.choice( string.hexdigits ) for _ in range( length ) )
		return id.lower()

	# The initial device authentication request for a non-logged in user doesn't require a user key, and the returned
	# user key can't be used for anything.
	def AuthenticateDevice( self, userKey: str = "" ) -> None:
		Globals.Logger.debug( "Kobo.AuthenticateDevice" )

		if len( Globals.Settings.DeviceId ) == 0:
			Globals.Settings.DeviceId = Kobo.__GenerateRandomHexDigitString( 64 )
			Globals.Settings.SerialNumber = Kobo.__GenerateRandomHexDigitString( 32 )
			Globals.Settings.AccessToken = ""
			Globals.Settings.RefreshToken = ""

		postData = {
			"AffiliateName": Kobo.Affiliate,
			"AppVersion": Kobo.ApplicationVersion,
			"ClientKey": base64.b64encode( Kobo.DefaultPlatformId.encode() ).decode(),
			"DeviceId": Globals.Settings.DeviceId,
			"PlatformId": Kobo.DefaultPlatformId,
			"SerialNumber": Globals.Settings.SerialNumber,
		}

		if len( userKey ) > 0:
			postData[ "UserKey" ] = userKey

		response = self.Session.post( "https://storeapi.kobo.com/v1/auth/device", json = postData )
		response.raise_for_status()
		jsonResponse = response.json()

		if jsonResponse[ "TokenType" ] != "Bearer":
			raise KoboException( "Device authentication returned with an unsupported token type: '%s'" % jsonResponse[ "TokenType" ] )

		Globals.Settings.AccessToken = jsonResponse[ "AccessToken" ]
		Globals.Settings.RefreshToken = jsonResponse[ "RefreshToken" ]
		if not Globals.Settings.AreAuthenticationSettingsSet():
			raise KoboException( "Authentication settings are not set after device authentication." )

		if len( userKey ) > 0:
			Globals.Settings.UserKey = jsonResponse[ "UserKey" ]

		Globals.Settings.Save()

	def RefreshAuthentication( self ) -> None:
		Globals.Logger.debug( "Kobo.RefreshAuthentication" )

		headers = Kobo.GetHeaderWithAccessToken()

		postData = {
			"AppVersion": Kobo.ApplicationVersion,
			"ClientKey": base64.b64encode( Kobo.DefaultPlatformId.encode() ).decode(),
			"PlatformId": Kobo.DefaultPlatformId,
			"RefreshToken": Globals.Settings.RefreshToken
		}

		# The reauthentication hook is intentionally not set.
		response = self.Session.post( "https://storeapi.kobo.com/v1/auth/refresh", json = postData, headers = headers )
		response.raise_for_status()
		jsonResponse = response.json()

		if jsonResponse[ "TokenType" ] != "Bearer":
			raise KoboException( "Authentication refresh returned with an unsupported token type: '%s'" % jsonResponse[ "TokenType" ] )

		Globals.Settings.AccessToken = jsonResponse[ "AccessToken" ]
		Globals.Settings.RefreshToken = jsonResponse[ "RefreshToken" ]
		if not Globals.Settings.AreAuthenticationSettingsSet():
			raise KoboException( "Authentication settings are not set after authentication refresh." )

		Globals.Settings.Save()

	def LoadInitializationSettings( self ) -> None:
		Globals.Logger.debug( "Kobo.LoadInitializationSettings" )

		headers = Kobo.GetHeaderWithAccessToken()
		hooks = Kobo.__GetReauthenticationHook()
		response = self.Session.get( "https://storeapi.kobo.com/v1/initialization", headers = headers, hooks = hooks )
		response.raise_for_status()
		jsonResponse = response.json()
		self.InitializationSettings = jsonResponse[ "Resources" ]

	def WaitTillActivation( self, activationCheckUrl: str ) -> Tuple[ str, str ]:
		while True:
			print( "Waiting for you to finish the activation..." )
			time.sleep( 5 )

			response = self.Session.post( activationCheckUrl )
			response.raise_for_status()

			jsonResponse = None
			try:
				jsonResponse = response.json()
			except Exception:
				Globals.Logger.debug( f"Activation check's response:\n{response.text}" )
				raise KoboException( "Error checking the activation's status. The response is not JSON." )

			if jsonResponse[ "Status" ] == "Complete":
				# RedirectUrl looks like this:
				# kobo://UserAuthenticated?returnUrl=https%3A%2F%2Fwww.kobo.com%2Fww%2Fen%2F&userKey=...&userId=...&email=...
				redirectUrl = jsonResponse[ "RedirectUrl" ]
				parsed = urllib.parse.urlparse( redirectUrl )
				parsedQueries = urllib.parse.parse_qs( parsed.query )
				userId = parsedQueries[ "userId" ][ 0 ]
				userKey = parsedQueries[ "userKey" ][ 0 ]
				return userId, userKey

	def ActivateOnWeb( self ) -> Tuple[ str, str ]:
		print( "Initiating web-based activation" )

		params = {
			"pwspid": Kobo.DefaultPlatformId,
			"wsa": Kobo.Affiliate,
			"pwsdid": Globals.Settings.DeviceId,
			"pwsav": Kobo.ApplicationVersion,
			"pwsdm": Kobo.DefaultPlatformId, # In the Android app this is the device model but Nickel sends the platform ID...
			"pwspos": Kobo.DeviceOs,
			"pwspov": Kobo.DeviceOsVersion,
		}

		response = self.Session.get( "https://auth.kobobooks.com/ActivateOnWeb", params = params )
		response.raise_for_status()
		htmlResponse = response.text

		match = re.search( 'data-poll-endpoint="([^"]+)"', htmlResponse )
		if match is None:
			raise KoboException( "Can't find the activation poll endpoint in the response. The page format might have changed." )
		activationCheckUrl = "https://auth.kobobooks.com" + html.unescape( match.group( 1 ) )

		match = re.search( r"""qrcodegenerator/generate.+?%26code%3D(\d+)""", htmlResponse )
		if match is None:
			raise KoboException( "Can't find the activation code in the response. The page format might have changed." )
		activationCode = match.group( 1 )

		return activationCheckUrl, activationCode

	def Login( self ) -> None:
		Globals.Logger.debug( "Kobo.Login" )

		activationCheckUrl, activationCode = self.ActivateOnWeb()

		print( "" )
		print( "kobo-book-downloader uses the same web-based activation method to log in as the Kobo e-readers." )
		print( "You will have to open the link below in your browser and enter the code, then you might need to login too if kobo.com asks you to." )
		print( "kobo-book-downloader will wait now and periodically check for the activation to complete." )
		print( "" )
		print( f"Open https://www.kobo.com/activate and enter {activationCode}." )
		print( "" )

		userId, userKey = self.WaitTillActivation( activationCheckUrl )
		print( "" )

		# We don't call Settings.Save here, AuthenticateDevice will do that if it succeeds.
		Globals.Settings.UserId = userId
		self.AuthenticateDevice( userKey )

	def GetBookInfo( self, productId: str ) -> dict:
		Globals.Logger.debug( "Kobo.GetBookInfo" )

		url = self.InitializationSettings[ "book" ].replace( "{ProductId}", productId )
		headers = Kobo.GetHeaderWithAccessToken()
		hooks = Kobo.__GetReauthenticationHook()

		response = self.Session.get( url, headers = headers, hooks = hooks )
		response.raise_for_status()
		jsonResponse = response.json()
		return jsonResponse

	def __GetMyBookListPage( self, syncToken: str ) -> Tuple[ list, str ]:
		Globals.Logger.debug( "Kobo.__GetMyBookListPage" )

		url = self.InitializationSettings[ "library_sync" ]
		headers = Kobo.GetHeaderWithAccessToken()
		hooks = Kobo.__GetReauthenticationHook()

		if len( syncToken ) > 0:
			headers[ "x-kobo-synctoken" ] = syncToken

		response = Globals.Kobo.Session.get( url, headers = headers, hooks = hooks )
		response.raise_for_status()
		bookList = response.json()

		syncToken = ""
		syncResult = response.headers.get( "x-kobo-sync" )
		if syncResult == "continue":
			syncToken = response.headers.get( "x-kobo-synctoken", "" )

		return bookList, syncToken

	def GetMyBookList( self ) -> list:
		# The "library_sync" name and the synchronization tokens make it somewhat suspicious that we should use
		# "library_items" instead to get the My Books list, but "library_items" gives back less info (even with the
		# embed=ProductMetadata query parameter set).

		fullBookList = []
		syncToken = ""
		while True:
			bookList, syncToken = self.__GetMyBookListPage( syncToken )
			fullBookList += bookList
			if len( syncToken ) == 0:
				break

		return fullBookList

	def GetMyWishList( self ) -> list:
		Globals.Logger.debug( "Kobo.GetMyWishList" )

		items = []
		currentPageIndex = 0

		while True:
			url = self.InitializationSettings[ "user_wishlist" ]
			headers = Kobo.GetHeaderWithAccessToken()
			hooks = Kobo.__GetReauthenticationHook()

			params = {
				"PageIndex": currentPageIndex,
				"PageSize": 100, # 100 is the default if PageSize is not specified.
			}

			response = Globals.Kobo.Session.get( url, params = params, headers = headers, hooks = hooks )
			response.raise_for_status()
			wishList = response.json()

			items.extend( wishList[ "Items" ] )

			currentPageIndex += 1
			if currentPageIndex >= wishList[ "TotalPageCount" ]:
				break

		return items

	def __GetContentAccessBook( self, productId: str, displayProfile: str ) -> dict:
		Globals.Logger.debug( "Kobo.__GetContentAccessBook" )

		url = self.InitializationSettings[ "content_access_book" ].replace( "{ProductId}", productId )
		params = { "DisplayProfile": displayProfile }
		headers = Kobo.GetHeaderWithAccessToken()
		hooks = Kobo.__GetReauthenticationHook()

		response = self.Session.get( url, params = params, headers = headers, hooks = hooks )
		response.raise_for_status()
		jsonResponse = response.json()
		return jsonResponse

	@staticmethod
	def __GetContentKeys( contentAccessBookResponse: dict ) -> Dict[ str, str ]:
		jsonContentKeys = contentAccessBookResponse.get( "ContentKeys" )
		if jsonContentKeys is None:
			return {}

		contentKeys = {}
		for contentKey in jsonContentKeys:
			contentKeys[ contentKey[ "Name" ] ] = contentKey[ "Value" ]
		return contentKeys

	@staticmethod
	def __GetDownloadInfo( productId: str, contentAccessBookResponse: dict ) -> Tuple[ str, bool ]:
		jsonContentUrls = contentAccessBookResponse.get( "ContentUrls" )
		if jsonContentUrls is None:
			raise KoboException( "Download URL can't be found for product '%s'." % productId )

		if len( jsonContentUrls ) == 0:
			raise KoboException( "Download URL list is empty for product '%s'. If this is an archived book then it must be unarchived first on the Kobo website (https://www.kobo.com/help/en-US/article/1799/restoring-deleted-books-or-magazines)." % productId )

		for jsonContentUrl in jsonContentUrls:
			if ( jsonContentUrl[ "DRMType" ] == "KDRM" or jsonContentUrl[ "DRMType" ] == "SignedNoDrm" ) and \
				( jsonContentUrl[ "UrlFormat" ] == "EPUB3" or jsonContentUrl[ "UrlFormat" ] == "KEPUB" ):
				# Remove the mysterious "b" query parameter that causes forbidden downloads.
				url = jsonContentUrl[ "DownloadUrl" ]
				parsed = urllib.parse.urlparse( url )
				parsedQueries = urllib.parse.parse_qs( parsed.query )
				parsedQueries.pop( "b", None )
				url = parsed._replace( query = urllib.parse.urlencode( parsedQueries, doseq = True ) ).geturl()

				hasDrm = jsonContentUrl[ "DRMType" ] == "KDRM"
				return url, hasDrm

		message = "Download URL for supported formats can't be found for product '%s'.\n" % productId
		message += "Available formats:"
		for jsonContentUrl in jsonContentUrls:
			message += "\nDRMType: '%s', UrlFormat: '%s'" % ( jsonContentUrl[ "DRMType" ], jsonContentUrl[ "UrlFormat" ] )

		raise KoboException( message )

	def __DownloadToFile( self, url, outputPath: str ) -> None:
		Globals.Logger.debug( "Kobo.__DownloadToFile" )

		response = self.Session.get( url, stream = True )
		response.raise_for_status()
		with open( outputPath, "wb" ) as f:
			for chunk in response.iter_content( chunk_size = 1024 * 256 ):
				f.write( chunk )

	# Downloading archived books is not possible, the "content_access_book" API endpoint returns with empty ContentKeys
	# and ContentUrls for them.
	def Download( self, productId: str, displayProfile: str, outputPath: str ) -> None:
		Globals.Logger.debug( "Kobo.Download" )

		jsonResponse = self.__GetContentAccessBook( productId, displayProfile )
		contentKeys = Kobo.__GetContentKeys( jsonResponse )
		downloadUrl, hasDrm = Kobo.__GetDownloadInfo( productId, jsonResponse )

		temporaryOutputPath = outputPath + ".downloading"

		try:
			self.__DownloadToFile( downloadUrl, temporaryOutputPath )

			if hasDrm:
				drmRemover = KoboDrmRemover( Globals.Settings.DeviceId, Globals.Settings.UserId )
				drmRemover.RemoveDrm( temporaryOutputPath, outputPath, contentKeys )
				os.remove( temporaryOutputPath )
			else:
				os.rename( temporaryOutputPath, outputPath )
		except:
			if os.path.isfile( temporaryOutputPath ):
				os.remove( temporaryOutputPath )
			if os.path.isfile( outputPath ):
				os.remove( outputPath )

			raise
