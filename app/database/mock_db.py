import json
from pathlib import Path
from typing import Any

from app.config import DATA_DIR


class MockDatabase:
    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def _read_json(self, name: str) -> Any:
        if name in self._cache:
            return self._cache[name]
        path = Path(DATA_DIR / name)
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        self._cache[name] = payload
        return payload

    def facilities(self) -> list[dict]:
        return self._read_json("facilities.json")

    def departments(self) -> list[dict]:
        return self._read_json("departments.json")

    def doctors(self) -> list[dict]:
        return self._read_json("doctors.json")

    def schedules(self) -> list[dict]:
        return self._read_json("schedules.json")


db = MockDatabase()
