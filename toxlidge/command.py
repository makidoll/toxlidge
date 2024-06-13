from typing import Union

from slidge.command import Command, CommandAccess, Form, FormField, TableResult
from slidge.command.base import FormValues
from slixmpp.exceptions import XMPPError

from .session import Session

class ToxInfo(Command):
	NAME = "Show Tox ID, name and status"
	CHAT_COMMAND = NODE = "tox-info"
	HELP = "Shows Tox ID, name and status"
	ACCESS = CommandAccess.USER_LOGGED

	async def run(self, session: Session, _ifrom, *args: str):
		status = session.tox_client.tox.self_get_status_message()
		status_line = "(empty)" if status == "" else status
		return (
		    "*Tox ID:*\n"
		    f"{session.tox_client.tox.self_get_toxid()}\n"
		    "*Address:*\n"
		    f"{session.tox_client.tox.self_get_address()}\n"
		    "*Name:*\n"
		    f"{session.tox_client.tox.self_get_name()}\n"
		    "*Status:*\n"
		    f"{status_line}\n"
		)

class SetToxName(Command):
	NAME = "Set Tox name that others will see"
	CHAT_COMMAND = NODE = "tox-name"
	HELP = "Set Tox name that others will see"
	ACCESS = CommandAccess.USER_LOGGED

	async def run(self, session: Session, _ifrom, *args: str):
		return Form(
		    title=self.NAME,
		    instructions="",
		    handler=self.finish,
		    fields=[
		        FormField(
		            "new_name",
		            label="New name",
		            type="text-single",
		            required=True
		        )
		    ],
		)

	@staticmethod
	async def finish(
	    form_values: FormValues,
	    session: Session,
	    _ifrom,
	):
		new_name = form_values["new_name"]
		session.tox_client.self_set_name(new_name)
		return "Updated Tox name to: " + new_name

class SetToxStatus(Command):
	NAME = "Set Tox status that others will see"
	CHAT_COMMAND = NODE = "tox-status"
	HELP = "Set Tox name that others will see"
	ACCESS = CommandAccess.USER_LOGGED

	async def run(self, session: Session, _ifrom, *args: str):
		return Form(
		    title=self.NAME,
		    instructions="(message a single space to clear)",
		    handler=self.finish,
		    fields=[
		        FormField(
		            "new_status",
		            label="New status",
		            type="text-single",
		            required=True
		        )
		    ],
		)

	@staticmethod
	async def finish(
	    form_values: FormValues,
	    session: Session,
	    _ifrom,
	):
		new_status = form_values["new_status"].strip()
		session.tox_client.self_set_status_message(new_status)
		if new_status == "":
			return "Cleared Tox status"
		else:
			return "Updated Tox status to: " + new_status
