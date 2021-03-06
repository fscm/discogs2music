from typing import Any

class Options:
    def __init__(self) -> None: ...
    @property
    def apikey(self) -> str: ...
    @property
    def datafile(self) -> str: ...
    @property
    def debug(self) -> bool: ...
    @property
    def local(self) -> bool: ...
    @property
    def options(self) -> dict[str,Any]: ...
    @property
    def override(self) -> bool: ...
    @property
    def quiet(self) -> bool: ...
    @property
    def songs(self) -> bool: ...
