from slidge.util.util import get_version  # noqa: F401

from . import command, contact, gateway, session

__all__ = "command", "contact", "gateway", "session"

__version__ = get_version()
