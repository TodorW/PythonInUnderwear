import os
from typing import Any


class Config:
    def __init__(self, defaults: dict = None):
        self._data: dict[str, Any] = {
            "DEBUG": False,
            "HOST": "127.0.0.1",
            "PORT": 5000,
            "SECRET_KEY": "",
            "TEMPLATE_DIR": "templates",
            "STATIC_DIR": "static",
            "STATIC_URL": "/static",
        }
        if defaults:
            self._data.update(defaults)

    def __getitem__(self, key: str) -> Any:
        return self._data[key.upper()]

    def __setitem__(self, key: str, value: Any):
        self._data[key.upper()] = value

    def __contains__(self, key: str) -> bool:
        return key.upper() in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key.upper(), default)

    def set(self, key: str, value: Any):
        self._data[key.upper()] = value

    def all(self) -> dict:
        return dict(self._data)

    def from_dict(self, d: dict):
        for k, v in d.items():
            self._data[k.upper()] = v

    def from_env_file(self, path: str = ".env"):
        if not os.path.isfile(path):
            return
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                self._data[key.strip().upper()] = _cast(val.strip())

    def from_yaml(self, path: str):
        try:
            import yaml
        except ImportError:
            raise RuntimeError("from_yaml() requires pyyaml. Run: pip install pyyaml")
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        for k, v in data.items():
            self._data[k.upper()] = v

    def load_env(self, prefix: str = "PIU_"):
        for k, v in os.environ.items():
            if k.startswith(prefix):
                key = k[len(prefix):]
                self._data[key.upper()] = _cast(v)

    def __repr__(self):
        return f"<Config keys={list(self._data.keys())}>"


def _cast(value: str) -> Any:
    if value.lower() in ("true", "yes"):
        return True
    if value.lower() in ("false", "no"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value