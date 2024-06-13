from typing import TYPE_CHECKING

from slidge import LegacyContact

if TYPE_CHECKING:
	from .session import Session

async def noop():
	return

class Contact(LegacyContact[int]):
	DISCO_TYPE = "pc"  # or phone but its tox
	session: "Session"

	UNKNOWN_RETRY_DELAY = 5
	UNKNOWN_RETRY_MAX_DELAY = 600
	UNKNOWN_MAX_ATTEMPTS = 10

	def __init__(self, *a, **k):
		super().__init__(*a, **k)
		self.chat_id = self.legacy_id
