import asyncio
from ctypes import c_char_p
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from slidge.core import config as global_config
from toxygen_wrapper.tox import TOX_SAVEDATA_TYPE, Tox
from toxygen_wrapper.toxcore_enums_and_consts import (
    TOX_CONNECTION, TOX_MESSAGE_TYPE, TOX_PUBLIC_KEY_SIZE, TOX_USER_STATUS,
    TOX_FILE_KIND, TOX_FILE_CONTROL
)

from .contact import Contact

if TYPE_CHECKING:
	from .session import Session

class ToxIncomingFile():
	tox_client: "ToxClient"
	friend_id: int
	file_id: int
	is_avatar: bool
	filename: str

	data: bytearray

	def __init__(
	    self, tox_client: "ToxClient", friend_id: int, file_id: int,
	    is_avatar: bool, file_size: int, filename: str
	):
		self.tox_client = tox_client
		self.friend_id = friend_id
		self.file_id = file_id
		self.is_avatar = is_avatar
		self.filename = filename

		self.data = bytearray(file_size)

	def insert(self, bytes: bytes, index: int):
		self.data[index:index] = bytearray(bytes)

	async def complete(self):
		try:
			contact = await self.tox_client.friend_id_to_contact(self.friend_id)
			if self.is_avatar:
				print(self.data)
				print(self.filename)
				await contact.set_avatar(self.data, self.filename)
			else:
				await contact.send_file(data=self.data, file_name=self.filename)
		except:
			pass

		self.tox_client.incoming_files.remove(self)

# class ToxOutgoingFile():
# 	tox_client: "ToxClient"

# 	def __init__(self, tox_client: "ToxClient", file: bytes, filename: str, is_avatar: bool):
# 		self.tox_client = tox_client

class ToxClient():
	active = False

	session: "Session" = None

	tox: Tox = None
	save_path = ""

	connected_f: asyncio.Future = None

	incoming_files: list[ToxIncomingFile] = list()

	def __save(self):
		with open(self.save_path, "wb") as f:
			f.write(self.tox.get_savedata())

	def __bootstrap_dht_nodes(self):
		# https://nodes.tox.chat/json

		res = requests.get("https://nodes.tox.chat/json")
		res_json = res.json()

		for node in res_json["nodes"]:
			ipv4 = node["ipv4"]
			ipv6 = node["ipv6"]
			port = node["port"]
			public_key = node["public_key"]

			if ipv4 != "-" and ipv4 != "NONE":
				try:
					self.tox.bootstrap(ipv4, port, public_key)
				except:
					pass

			if ipv6 != "-" and ipv6 != "NONE":
				try:
					self.tox.bootstrap(ipv6, port, public_key)
				except:
					pass

	# callbacks

	def __on_connection_status(self, connection_status: int):
		if connection_status == TOX_CONNECTION["NONE"]:  # TCP, UDP
			print("Failed to connect")
		else:
			print("Connected!")
			if self.connected_f != None and not self.connected_f.done():
				self.connected_f.set_result(None)

	def __on_friend_request(self, public_key: str, message: str):
		print(public_key)
		print(message)
		self.tox.friend_add_norequest(public_key)
		self.__save()

	async def friend_id_to_contact(self, friend_id: int) -> Contact:
		public_key = self.tox.friend_get_public_key(friend_id).lower()
		contact: Contact = await self.session.contacts.by_legacy_id(public_key)
		asyncio.create_task(contact.add_to_roster())  # dont await
		asyncio.create_task(contact.accept_friend_request())  # dont await
		return contact

	async def __on_friend_message(
	    self, friend_id: int, type: int, message: str
	):
		if type != TOX_MESSAGE_TYPE["NORMAL"]:
			return

		contact = await self.friend_id_to_contact(friend_id)
		contact.active()
		contact.send_text(message)

	async def __on_friend_name(self, friend_id: int, name: str):
		contact = await self.friend_id_to_contact(friend_id)
		contact.name = name
		contact.set_vcard(full_name=name)

	async def __on_friend_connection_status(
	    self, friend_id: int, connection_status: int
	):
		contact = await self.friend_id_to_contact(friend_id)

		if connection_status == TOX_CONNECTION["NONE"]:
			contact.offline()
		else:
			contact.online()

	async def __on_friend_status(self, friend_id: int, user_status: int):
		contact = await self.friend_id_to_contact(friend_id)
		status_message = self.tox.friend_get_status_message(friend_id)

		if user_status == TOX_USER_STATUS["NONE"]:
			contact.online(status_message)
		elif user_status == TOX_USER_STATUS["AWAY"]:
			contact.away(status_message)
		elif user_status == TOX_USER_STATUS["BUSY"]:
			contact.busy(status_message)

	async def __on_friend_status_message(
	    self, friend_id: int, status_message: str
	):
		contact = await self.friend_id_to_contact(friend_id)
		user_status = self.tox.friend_get_status(friend_id)

		if user_status == TOX_USER_STATUS["NONE"]:
			contact.online(status_message)
		elif user_status == TOX_USER_STATUS["AWAY"]:
			contact.away(status_message)
		elif user_status == TOX_USER_STATUS["BUSY"]:
			contact.busy(status_message)

	async def __on_friend_typing(self, friend_id: int, typing: bool):
		contact = await self.friend_id_to_contact(friend_id)
		if typing:
			contact.composing()
		else:
			# contact.paused() # gets stuck
			contact.active()

	def __on_file_recv(
	    self, friend_id: int, file_id: int, file_kind: int, file_size: int,
	    filename: str
	):
		file = ToxIncomingFile(
		    self, friend_id, file_id, file_kind == TOX_FILE_KIND["AVATAR"],
		    file_size, filename
		)

		self.incoming_files.append(file)

		self.tox.file_control(friend_id, file_id, TOX_FILE_CONTROL["RESUME"])

	def __on_file_recv_chunk(
	    self, friend_id: int, file_id: int, file_pos: int, bytes: bytes
	):
		found_file: ToxIncomingFile = None
		for file in self.incoming_files:
			if file.friend_id == friend_id and file.file_id == file_id:
				found_file = file

		if found_file == None:
			self.tox.file_control(
			    friend_id, file_id, TOX_FILE_CONTROL["CANCEL"]
			)
			return

		if len(bytes) == 0:
			asyncio.create_task(found_file.complete())
		else:
			found_file.insert(bytes, file_pos)

	# public functions

	def __get_friend_id_xmpp_safe(self, friend_key: str):
		try:
			return self.tox.friend_by_public_key(friend_key)
		except:
			self.tox.friend_add(
			    friend_key, "Would you like to add me as a friend?"
			)
			self.__save()
			raise Exception(
			    "User not in friends list, however a request was just sent"
			)

	def self_set_name(self, name: str):
		self.tox.self_set_name(name)
		self.__save()

	def self_set_status_message(self, status: str):
		self.tox.self_set_status_message(status)
		self.__save()

	async def send_message(self, friend_key: str, message: str) -> int:
		friend_id = self.__get_friend_id_xmpp_safe(friend_key)

		self.tox.self_set_typing(friend_id, False)

		return self.tox.friend_send_message(
		    friend_id, TOX_MESSAGE_TYPE["NORMAL"], message
		)

	async def set_typing(self, friend_key: str, typing: bool):
		self.tox.self_set_typing(
		    self.__get_friend_id_xmpp_safe(friend_key), typing
		)

	# init and loop

	def __init__(self, session: "Session"):
		self.session = session

		opts = Tox.options_new()

		self.save_path = Path(
		    global_config.HOME_DIR / (session.user.bare_jid + ".tox")
		)

		# load saved data

		did_save_path_exist = self.save_path.exists()

		if did_save_path_exist:
			print("Loading save")

			opts.contents.savedata_type = TOX_SAVEDATA_TYPE["TOX_SAVE"]

			with open(self.save_path, "rb") as f:
				data = f.read()
				opts.contents.savedata_data = c_char_p(data)
				opts.contents.savedata_length = len(data)

		# setup tox

		self.tox = Tox(opts)

		if not did_save_path_exist:
			self.tox.self_set_name(session.user.jid.username)
			# self.tox.self_set_status_message("Horsing around beep boop")

		# TODO: profile picture
		# self.tox.file_send(0, TOX_FILE_KIND["AVATAR"], 0, 0, "avatar.png")

		self.__bootstrap_dht_nodes()

		# setup callbacks

		def on_connection_status(tox, connection_status, *args):
			self.__on_connection_status(connection_status)

		self.tox.callback_self_connection_status(on_connection_status)

		# ---

		def on_friend_request(tox, public_key, message, length, *args):
			# key = ''.join(chr(x) for x in public_key[:TOX_PUBLIC_KEY_SIZE])
			# print(key)
			print(bytes(public_key[:TOX_PUBLIC_KEY_SIZE]).hex())
			self.__on_friend_request(
			    bytes(public_key[:TOX_PUBLIC_KEY_SIZE]).hex(),
			    str(message, "UTF-8")
			)

		self.tox.callback_friend_request(on_friend_request)

		# ---

		def on_friend_message(tox, friend_id, type, message, length, *args):
			asyncio.create_task(
			    self.__on_friend_message(
			        friend_id, type, str(message, "UTF-8")
			    )
			)

		self.tox.callback_friend_message(on_friend_message)

		# ---

		def on_friend_name(tox, friend_id, name_bytes, length, *args):
			name = ''.join(chr(x) for x in name_bytes[:length])
			asyncio.create_task(self.__on_friend_name(friend_id, name))

		self.tox.callback_friend_name(on_friend_name)

		# ---

		def on_friend_connection_status(
		    tox, friend_id, connection_status, *args
		):
			asyncio.create_task(
			    self.__on_friend_connection_status(
			        friend_id, connection_status
			    )
			)

		self.tox.callback_friend_connection_status(on_friend_connection_status)

		# ---

		def on_friend_status(tox, friend_id, user_status, *args):
			asyncio.create_task(self.__on_friend_status(friend_id, user_status))

		self.tox.callback_friend_status(on_friend_status)

		# ---

		def on_friend_status_message(
		    tox, friend_id, message_bytes, length, *args
		):
			message = ''.join(chr(x) for x in message_bytes[:length])
			asyncio.create_task(
			    self.__on_friend_status_message(friend_id, message)
			)

		self.tox.callback_friend_status_message(on_friend_status_message)

		# ---

		def on_friend_typing(tox, friend_id, typing, *args):
			asyncio.create_task(self.__on_friend_typing(friend_id, typing))

		self.tox.callback_friend_typing(on_friend_typing)

		# ---

		def on_file_recv(
		    tox, friend_id, file_id, file_kind, file_size, filename_bytes,
		    filename_length, *args
		):
			filename = ''.join(chr(x) for x in filename_bytes[:filename_length])
			self.__on_file_recv(
			    friend_id, file_id, file_kind, file_size, filename
			)

		self.tox.callback_file_recv(on_file_recv)

		# ---

		def on_file_recv_chunk(
		    tox, friend_id, file_id, file_pos, recv_bytes, length, *args
		):
			self.__on_file_recv_chunk(
			    friend_id, file_id, file_pos, bytes(recv_bytes[:length])
			)

		self.tox.callback_file_recv_chunk(on_file_recv_chunk)

		# save and start loop

		self.__save()

	async def loop(self):
		while self.active:
			self.tox.iterate()
			await asyncio.sleep(self.tox.iteration_interval() / 1000)

	def login(self):
		if self.active:
			return

		print("Connecting...")

		self.active = True
		self.connected_f = asyncio.Future()

		asyncio.create_task(self.loop())  # dont await

		return self.connected_f

	def logout(self):
		if not self.active:
			return

		# will stop loop
		self.active = False
