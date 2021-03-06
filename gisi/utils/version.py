from datetime import datetime
from enum import IntEnum, auto

from gisi.constants import Sources


class ChangeType(IntEnum):
    BUGFIX = auto()

    MINOR_FEATURE = auto()
    MAJOR_FEATURE = auto()


class VersionStamp:
    def __init__(self, year, month, day, hour, minute):
        self.datetime = datetime(year, month, day, hour, minute)

    def __repr__(self):
        return self.timestamp

    def __eq__(self, other):
        return isinstance(other, VersionStamp) and self.timestamp == other.timestamp

    def __gt__(self, other):
        return isinstance(other, VersionStamp) and self.timestamp > other.timestamp

    def __ge__(self, other):
        return isinstance(other, VersionStamp) and self.timestamp >= other.timestamp

    def __lt__(self, other):
        return isinstance(other, VersionStamp) and self.timestamp < other.timestamp

    def __le__(self, other):
        return isinstance(other, VersionStamp) and self.timestamp <= other.timestamp

    def __getattr__(self, item):
        return getattr(self.datetime, item)

    @property
    def timestamp(self):
        return f"{self.year:04}.{self.month:02}.{self.day:02}-{self.hour:02}{self.minute:02}"

    @classmethod
    def from_timestamp(cls, timestamp):
        date, time = timestamp.split("-")
        year, month, day = map(int, date.split("."))
        hour, minute = map(int, (time[:2], time[2:]))
        return cls(year, month, day, hour, minute)


class CurrentVersion:
    def __init__(self, version, name):
        self.version = version
        self.name = name

    def __repr__(self):
        return f"{self.name}/{self.version}"

    @classmethod
    def parse(cls, data):
        version = VersionStamp.from_timestamp(data["version"])
        return cls(version, data["name"])


class HistoryEntry:
    def __init__(self, version, change, change_type):
        self.version = version
        self.change = change
        self.change_type = change_type

    def __repr__(self):
        return f"{self.version} {self.change_type}: {self.change}"

    @classmethod
    def parse(cls, data):
        version = VersionStamp.from_timestamp(data["version"])
        change_type = ChangeType[data["type"]]
        return cls(version, data["change"], change_type)


class Changelog:
    def __init__(self, current_version, history):
        self.current_version = current_version
        self.history = history

    def __repr__(self):
        return f"<Changelog up to {self.current_version}>"

    @classmethod
    def parse(cls, data):
        current_version = CurrentVersion.parse(data["current_version"])
        history = [HistoryEntry.parse(entry) for entry in data["history"]]

        return cls(current_version, history)

    def filter_history(self, *, min_version=None, max_entries=None, min_type=None):
        entries = []
        for entry in self.history:
            if min_version and min_version >= entry.version:
                break
            if min_type and entry.change_type < min_type:
                continue
            entries.append(entry)
            if max_entries and len(entries) >= max_entries:
                break
        return entries


async def get_changelog(session):
    async with session.get(Sources.GISI_VERSION_LOG) as resp:
        data = await resp.json()
    return Changelog.parse(data)
