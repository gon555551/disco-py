class MessageCreate:
    channel_id: str
    timestamp: str
    member: dict
    content: str
    author: dict
    guild_id: str

    def __init__(self, event: dict) -> None:
        self.event = event
        self.__set_message_attributes()

    def __set_message_attributes(self) -> None:
        for attr in self.__annotations__:
            self.__setattr__(attr, self.event["d"][attr])


class InteractionCreate:
    token: str
    member: dict
    data: dict
    channel_id: str
    id: str
    application_id: str

    def __init__(self, event: dict) -> None:
        self.event = event
        self.options = dict()
        self.__set_interaction_attributes()
        if "options" in self.data.keys():
            self.__set_options_attributes()
        self.member = self.member["user"]

    def __set_interaction_attributes(self):
        for attr in self.__annotations__:
            self.__setattr__(attr, self.event["d"][attr])

    def __set_options_attributes(self):
        for options in self.data["options"]:
            self.options[f"{options['name']}"] = f"{options['value']}"
