import abc
import logging
import shutil
from typing import Generic, TypeAlias, TypeVar

logger = logging.Logger(__name__)
StatusCode: TypeAlias = int

CODE_UNKNOWN: StatusCode = 0
CODE_MUTED: StatusCode = 1
CODE_UNMUTED: StatusCode = 2

class NotifyConfig:
    def __init__(self, data: dict):
        self.mutenotify_rules: list[MuteNotifyOutput] = []
        for rule_data in data.get("mutenotify_rules", []):
            try: 
                self.mutenotify_rules.append(build_mutenotify_rule(rule_data))
            except ValueError as e:
                logger.error(e)
            except KeyError as e:
                logger.error(f"Unexpected key error while reading mute notify output configuration: {e}")

T = TypeVar("T")
class StatusSwitch(Generic[T]):
    def __init__(self, data: dict[str, T], default: T | None = None, allow_none = False):
        self.muted: T = data.get("muted", default)
        self.unmuted: T = data.get("unmuted", default)
        self.unknown: T = data.get("unknown", default)
        if self.muted == None and not allow_none:
            raise ValueError("'muted' field may not be null in StatusSwitch")
        if self.unmuted == None and not allow_none:
            raise ValueError("'unmuted' field may not be null in StatusSwitch")
        if self.unknown == None and not allow_none:
            raise ValueError("'unknown' field may not be null in StatusSwitch")
        
    def get(self, code: StatusCode) -> T:
        if code == CODE_MUTED:
            return self.muted
        elif code == CODE_UNMUTED:
            return self.unmuted
        else:
            return self.unknown

SUPPORTED_FORMATS = ["image", "html"]
def build_mutenotify_rule(data: dict):
    if "name" not in data:
            raise ValueError("'name' is required in mute notify output specification")
    name: str = data["name"]
    if "format" not in data:
        raise ValueError(f"'format' is required in mute notify output specification '{name}'")
    format: str = data["format"]
    if "file" not in data:
        raise ValueError(f"'file' is required in mute notify output specification '{name}'")
    file: str = data["file"]
    if "id" not in data:
        raise ValueError(f"'id' is required in mute notify output specification '{name}'")
    id: int = int(data["id"])

    if format == "image":
        return MuteNotifyFileOutput(name, id, file, data)
    elif format == "html":
        return MuteNotifyHTMLOutput(name, id, file, data)
    else:
        raise ValueError(f"Unknown format '{format}' in mute notify output specification '{name}'; supported formats are '{"', '".join(SUPPORTED_FORMATS)}'")

class MuteNotifyOutput(abc.ABC):
    def __init__(self, name: str, id: int, out_file: str):
        self.name = name
        self.out_file = out_file
        self.id = id

    @abc.abstractmethod
    def set_status(self, status: StatusCode):
        pass

class MuteNotifyFileOutput(MuteNotifyOutput):
    def __init__(self, name: str, id: int, out_file: str, data: dict):
        super().__init__(name, id, out_file)
        if "image" not in data:
            raise ValueError(f"'image' is required in Image-format mute notify output specification '{self.name}'")
        self.image: StatusSwitch[str] = StatusSwitch(data["image"])

    def set_status(self, status: StatusCode):
        fetch_target: str = self.image.get(status)
        shutil.copyfile(fetch_target, self.out_file)

class MuteNotifyHTMLOutput(MuteNotifyOutput):
    def __init__(self, name: str, id: int, out_file: str, data: dict):
        super().__init__(name, id, out_file)
        if "template" not in data:
            raise ValueError(f"'template' is required in HTML-format mute notify output specification '{self.name}'")
        self.template: StatusSwitch[str] = StatusSwitch(data["template"])

    def process_pattern(self, template: str):
        # for now, no processing
        return template

    def set_status(self, status: StatusCode):
        selected_template = self.template.get(status)
        processed_text = self.process_pattern(selected_template)
        with open(self.out_file, "w") as f:
            f.write(processed_text)
