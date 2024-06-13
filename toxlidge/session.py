from typing import Optional

from slidge import BaseSession
from slidge.util.db import GatewayUser
from slidge.util.types import LegacyMessageType, Mention
from slixmpp.exceptions import XMPPError

from .contact import Contact
from .tox_client import ToxClient

class Session(BaseSession):
	tox_client: ToxClient

	def __init__(self, user: GatewayUser):
		super().__init__(user)

		self.tox_client = ToxClient(self)

	def tox_connected(self):
		print("tox connected")

	async def login(self):
		tox_id = self.tox_client.tox.self_get_address()

		self.contacts.user_legacy_id = tox_id
		self.bookmarks.user_nick = tox_id

		# self.contacts.fill()  # i dont think this is how you do it

		# friends_list = self.tox_client.tox.self_get_friend_list()
		# for friend_id in friends_list:
		# 	public_key = self.tox_client.tox.friend_get_public_key(friend_id
		# 	                                                      ).lower()

		# 	contact: Contact = await self.contacts.by_legacy_id(
		# 	    public_key
		# 	)

		# 	await contact.add_to_roster(True)

		await self.tox_client.login()

		return f"Connected as {tox_id}"

	async def logout(self):
		self.tox_client.logout()

	async def on_text(
	    self,
	    contact: Contact,
	    text: str,
	    *,
	    reply_to_msg_id=None,
	    mentions: Optional[list[Mention]] = None,
	    **_kwargs,
	) -> int:
		# TODO: maybe await this till we're connected
		await self.tox_client.send_message(contact.jid_username, text)

	async def on_composing(self, contact: Contact, thread=None):
		await self.tox_client.set_typing(contact.jid_username, True)

	async def on_paused(self, contact: Contact, thread=None):
		await self.tox_client.set_typing(contact.jid_username, False)

	async def on_active(self, contact: Contact, thread=None):
		await self.tox_client.set_typing(contact.jid_username, False)

	async def on_correct(
	    self,
	    contact: Contact,
	    text: str,
	    legacy_msg_id: LegacyMessageType,
	    *,
	    thread=None,
	    link_previews=(),
	    mentions=None
	):
		# TODO: doesnt actually fail
		raise XMPPError("bad-request", "Tox doesn't support message correcting")

	# async def on_avatar(
	#     self,
	#     bytes: bytes,
	#     hash,  # sha1
	#     type: str,  # mime
	# ):
	# 	print(bytes)
	# 	print(hash)
	# 	print(type)
	# 	print("\n\n\n")
