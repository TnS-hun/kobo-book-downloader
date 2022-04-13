import colorama

import logging

class LogFormatter( logging.Formatter ):
	def __init__( self ):
		self.DebugFormatter = logging.Formatter( colorama.Style.BRIGHT + colorama.Fore.GREEN + "%(levelname)s: " + colorama.Style.RESET_ALL + "%(message)s" )
		self.ErrorFormatter = logging.Formatter( colorama.Style.BRIGHT + colorama.Fore.RED + "%(levelname)s: " + colorama.Style.RESET_ALL + "%(message)s" )

	def format( self, record ):
		if record.levelname == "DEBUG":
			return self.DebugFormatter.format( record )
		elif record.levelname == "ERROR":
			return self.ErrorFormatter.format( record )
		else:
			return super().format( record )
