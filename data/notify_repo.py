from typing import Iterable
import yaml
import abc
import logging

logger = logging.Logger(__name__)

class NotifyRepo(abc.ABC):
    @abc.abstractmethod
    async def get_mutenotify_users(self) -> list[int]:
        """
        Returns a list of IDs of all users who have mute/unmute notifications enabled
        """
        pass

    async def set_mutenotify_users(self, users: Iterable[int]) -> None:
        """
        Sets the list of IDs of all users who have mute/unmute notifications enabled
        """
        pass

    async def add_mutenotify_users(self, users: Iterable[int]) -> None:
        """
        Adds one or more users to the list of users with mute/unmute notifications enabled
        """
        current = set(await self.get_mutenotify_users())
        await self.set_mutenotify_users(list(current.union(users)))

    async def remove_mutenotify_users(self, users: Iterable[int]) -> None:
        """
        Removes one or more users to the list of users with mute/unmute notifications enabled
        """
        current = set(await self.get_mutenotify_users())
        await self.set_mutenotify_users(list(current.difference(users)))


# This should be replaced with SQL eventually.
class YamlNotifyRepo(NotifyRepo):
    def __init__(self, db_name = "data/notify_db.yaml"):
        self.db_name = db_name

    async def get_mutenotify_users(self) -> list[int]:
        try:
            with open(self.db_name) as f:
                data: dict = yaml.safe_load(f)
            return [int(x) for x in data.get("mute_listen_users", [])] or []
        except FileNotFoundError:
            logger.warning(f"Unable to find data file {self.db_name}")
            with open(self.db_name, "w") as f:
                yaml.safe_dump({}, f)
            return []

    async def set_mutenotify_users(self, users: list[int]) -> None:
        data = {}
        try:
            with open(self.db_name) as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Unable to find data file {self.db_name}")
        data["mute_listen_users"] = [str(x) for x in users]
        with open(self.db_name, "w") as f:
            yaml.safe_dump(data, f)