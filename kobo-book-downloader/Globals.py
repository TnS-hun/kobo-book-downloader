from logging import Logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from Kobo import Kobo
	from Settings import Settings

class Globals:
	Logger = None # type: Logger | None
	Kobo = None # type: Kobo | None
	Settings = None # type: Settings | None
