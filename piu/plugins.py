from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app import PIU


class Plugin:
    name: str = "unnamed"

    def setup(self, app: "PIU"):
        raise NotImplementedError(f"Plugin '{self.name}' must implement setup(app).")

    def __repr__(self):
        return f"<Plugin '{self.name}'>"