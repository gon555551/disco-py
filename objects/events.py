from objects.util_obj import *


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
        if "options" in self.data.keys():
            self.__set_options_attributes()

    def __set_interaction_attributes(self):
        for attr in self.__annotations__:
            try:
                self.__setattr__(attr, self.event["d"][attr])
            except KeyError:
                if attr == "author":
                    self.__setattr__(attr, Author(self.event["d"]["member"]["user"]))

    def __set_options_attributes(self):
        for options in self.data["options"]:
            self.options[f"{options['name']}"] = f"{options['value']}"
