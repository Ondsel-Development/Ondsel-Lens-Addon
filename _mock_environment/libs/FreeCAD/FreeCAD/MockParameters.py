class MockParameters:
    stored_dict = {}

    def GetBool(self, name: str, default: bool) -> bool:
        return self._Get(name, default)

    def GetInt(self, name: str, default: int) -> int:
        return self._Get(name, default)

    def GetFloat(self, name: str, default: float) -> float:
        return self._Get(name, default)

    def GetString(self, name: str, default: str) -> str:
        return self._Get(name, default)

    def _Get(self, name, default):
        return self.stored_dict[name] if name in self.stored_dict else default

    def SetBool(self, name: str, value: bool) -> None:
        self.stored_dict[name] = value

    def SetInt(self, name: str, value: int) -> None:
        self.stored_dict[name] = value

    def SetFloat(self, name: str, value: float) -> None:
        self.stored_dict[name] = value

    def SetString(self, name: str, value: str) -> None:
        self.stored_dict[name] = value

    def SetDict(self, name, value):
        """made this one up for the mock"""
        self.stored_dict[name] = value

    def RemBool(self, name: str) -> None:
        self.stored_dict.pop(name)

    def RemInt(self, name: str) -> None:
        self.stored_dict.pop(name)

    def RemFloat(self, name: str) -> None:
        self.stored_dict.pop(name)

    def RemString(self, name: str) -> None:
        self.stored_dict.pop(name)
