import json
import os

class Settings:
	def __init__( self ):
		self.DeviceId = ""
		self.SerialNumber = ""
		self.AccessToken = ""
		self.RefreshToken = ""
		self.UserId = ""
		self.UserKey = ""
		self.SettingsFilePath = Settings.__GetCacheFilePath()

		self.Load()

	def AreAuthenticationSettingsSet( self ) -> bool:
		return len( self.DeviceId ) > 0 and len( self.AccessToken ) > 0 and len( self.RefreshToken ) > 0

	def IsLoggedIn( self ) -> bool:
		return len( self.UserId ) > 0 and len( self.UserKey ) > 0

	def Load( self ) -> None:
		if not os.path.isfile( self.SettingsFilePath ):
			return

		with open( self.SettingsFilePath, "r" ) as f:
			jsonText = f.read()
			jsonObject = json.loads( jsonText )
			self.__LoadFromJson( jsonObject )

	def Save( self ) -> None:
		with open( self.SettingsFilePath, "w" ) as f:
			jsonObject = self.__SaveToJson()
			f.write( json.dumps( jsonObject, indent = 4 ) )

	def __SaveToJson( self ) -> dict:
		return {
			"AccessToken": self.AccessToken,
			"DeviceId": self.DeviceId,
			"RefreshToken": self.RefreshToken,
			"SerialNumber": self.SerialNumber,
			"UserId": self.UserId,
			"UserKey": self.UserKey
		}

	def __LoadFromJson( self, jsonMap: dict ) -> None:
		self.AccessToken = jsonMap.get( "AccessToken", self.AccessToken )
		self.DeviceId = jsonMap.get( "DeviceId", self.DeviceId )
		self.RefreshToken = jsonMap.get( "RefreshToken", self.RefreshToken )
		self.SerialNumber = jsonMap.get( "SerialNumber", self.SerialNumber )
		self.UserId = jsonMap.get( "UserId", self.UserId )
		self.UserKey = jsonMap.get( "UserKey", self.UserKey )

	@staticmethod
	def __GetCacheFilePath() -> str:
		cacheHome = os.environ.get( "XDG_CONFIG_HOME" )
		if ( cacheHome is None ) or ( not os.path.isdir( cacheHome ) ):
			home = os.path.expanduser( "~" )
			cacheHome = os.path.join( home, ".config" )
			if not os.path.isdir( cacheHome ):
				cacheHome = home

		return os.path.join( cacheHome, "kobo-book-downloader.json" )
