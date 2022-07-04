from utilities.obj_util import *


class MessageCreate:
    id: str
    channel_id: str
    timestamp: str
    member: dict
    content: str
    author: Author
    guild_id: str

    def __init__(self, event: dict) -> None:
        self.event = event
        self.__set_message_attributes()
        self.author = Author(self.author)

    def __set_message_attributes(self) -> None:
        for attr in self.__annotations__:
            try:
                self.__setattr__(attr, self.event["d"][attr])
            except KeyError:
                pass


class MessageDelete:
    id: str
    channel_id: str
    guild_id: str

    def __init__(self, event: dict) -> None:
        self.id = event["d"]["id"]
        self.channel_id = event["d"]["channel_id"]
        self.guild_id = event["d"]["guild_id"]


class InteractionCreate:
    token: str
    author: Author
    data: dict
    channel_id: str
    id: str
    application_id: str

    def __init__(self, event: dict) -> None:
        self.event = event
        self.options: dict[str, str] = dict()
        self.__set_interaction_attributes()

        self.__set_options_attributes()
        self.__set_resolved()

    def __set_interaction_attributes(self):
        for attr in self.__annotations__:
            try:
                self.__setattr__(attr, self.event["d"][attr])
            except KeyError:
                if attr == "author":
                    self.__setattr__(attr, Author(self.event["d"]["member"]["user"]))

    def __set_options_attributes(self):
        if "options" in self.data.keys():
            for options in self.data["options"]:
                self.options[f"{options['name']}"] = f"{options['value']}"

    def __set_resolved(self):
        if "resolved" in self.data.keys():
            self.resolved = Author(
                self.data["resolved"]["users"][
                    list(self.data["resolved"]["users"].keys())[0]
                ]
            )
