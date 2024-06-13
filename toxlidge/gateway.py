import typing

from slidge import BaseGateway, FormField, GatewayUser
from slidge.command.register import RegistrationType
from slixmpp import JID

REGISTRATION_INSTRUCTIONS = ("Registration instructions lmao")

class Gateway(BaseGateway):
	REGISTRATION_INSTRUCTIONS = REGISTRATION_INSTRUCTIONS
	REGISTRATION_FIELDS = [
	    FormField(var="gamer", label="gamer kek", required=False),
	    FormField(var="gamer idk whatever", required=False, private=True),
	]
	REGISTRATION_TYPE = RegistrationType.SINGLE_STEP_FORM

	ROSTER_GROUP = "Tox"
	COMPONENT_NAME = "Tox (slidge)"
	COMPONENT_TYPE = "tox"
	COMPONENT_AVATAR = "https://tox.chat/theme/img/favicon.ico"

	SEARCH_FIELDS = [
	    FormField(var="gamer", label="gamer idk", required=True),
	]

	GROUPS = False

	async def validate(
	    self, user_jid: JID, registration_form: dict[str, typing.Optional[str]]
	):
		gamer = registration_form.get("gamer")
		# if not is_valid_phone_number(phone):
		# 	raise ValueError("Not a valid phone number")
		# for u in user_store.get_all():
		# 	if u.registration_form.get("phone") == phone:
		# 		raise XMPPError(
		# 		    "not-allowed",
		# 		    text=
		# 		    "Someone is already using this phone number on this server.",
		# 		)
		# tg_client = CredentialsValidation(registration_form)  # type: ignore
		# auth_task = self.loop.create_task(tg_client.start())
		# self._pending_registrations[user_jid.bare
		#                            ] = auth_task, tg_client  # type:ignore

	async def unregister(self, user: GatewayUser):
		session = self.session_cls.from_user(user)
		# session.logged = False
		# workdir = session.tg.settings.files_directory.absolute()
		# await session.tg.api.log_out()
		# shutil.rmtree(workdir)
