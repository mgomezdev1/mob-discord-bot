from dotenv import dotenv_values
import logging
import yaml

import discord

logger = logging.getLogger(__name__)

def write_env_value(key: str, value: str):
    with open(".env", "a") as f:
        f.write(f"{key}={value}\n")

config = None
def get_config(env_source = ".env", allow_request = True, config_source = "config.yaml"):
    global config
    if not config:
        config = Config(env_source=env_source, allow_request=allow_request, config_source=config_source)
    return config

class Config:
    def try_load(self, dict: dict[str, str], key: str, name: str, allow_request: bool):
        val = dict.get(key, "")
        if not val:
            if allow_request:
                val = input(f"{name}: ")
                write_env_value(key, val)
            else:
                logger.error(f"No {name} available in environment file.")
        self.__setattr__(key.lower(), val)

    def is_staff(self, user: discord.Member):
        staff_roles = set(self.staff_roles)
        
        for r in user.roles:
            if r.id in staff_roles:
                return True
        return False

    def __init__(self, env_source = ".env", allow_request = True, config_source = "config.yaml"):
        self.env_dict: dict = dotenv_values(env_source)
        self.token: str
        self.try_load(self.env_dict, "TOKEN", "Discord bot token", allow_request)
        self.twitch_id: str
        self.try_load(self.env_dict, "TWITCH_ID", "Twitch app id", allow_request)
        self.twitch_secret: str
        self.try_load(self.env_dict, "TWITCH_SECRET", "Twitch secret", allow_request)

        with open(config_source) as f:
            self.config_dict: dict = yaml.safe_load(f)
        self.prefix: str = self.config_dict.get("prefix", "!")
        self.cogs: list[str] = self.config_dict.get("cogs", [])
        self.listening_guilds: list[int] = [int(x) for x in self.config_dict.get("listening_guilds", [])]
        self.staff_roles: list[int] = [int(x) for x in self.config_dict.get("staff_roles", [])]