import os
from typing import List, Union

import dataclasses
from dataclasses_json import dataclass_json


@dataclass_json
@dataclasses.dataclass
class User:
    Email: str
    DeviceId: str = ""
    AccessToken: str = ""
    RefreshToken: str = ""
    UserId: str = ""
    UserKey: str = ""

    def AreAuthenticationSettingsSet(self) -> bool:
        return (
            len(self.DeviceId) > 0
            and len(self.AccessToken) > 0
            and len(self.RefreshToken) > 0
        )

    def IsLoggedIn(self) -> bool:
        return len(self.UserId) > 0 and len(self.UserKey) > 0


@dataclass_json
@dataclasses.dataclass
class UserList:
    users: List[User] = dataclasses.field(default_factory=list)

    def getUser(self, identifier: str) -> Union[User, None]:
        for user in self.users:
            if user.Email == identifier or user.UserKey == identifier:
                return user
        return None

class Settings:
    def __init__(self):
        self.SettingsFilePath = Settings.__GetCacheFilePath()
        self.UserList = self.Load()

    def Load(self) -> UserList:
        if not os.path.isfile(self.SettingsFilePath):
            return UserList()
        with open(self.SettingsFilePath, "r") as f:
            jsonText = f.read()
            return UserList.from_json(jsonText)

    def Save(self) -> None:
        with open(self.SettingsFilePath, "w") as f:
            f.write(self.UserList.to_json(indent=4))

    @staticmethod
    def __GetCacheFilePath() -> str:
        cacheHome = os.environ.get("XDG_CONFIG_HOME.")
        if (cacheHome is None) or (not os.path.isdir(cacheHome)):
            home = os.path.expanduser("~")
            cacheHome = os.path.join(home, ".config")
            if not os.path.isdir(cacheHome):
                cacheHome = home

        return os.path.join(cacheHome, "kobo-book-downloader.json")
