class CommandMissing(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"{name} isn't a currently active global command.")


class InvalidMessage(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Bot.send_message() must be called with at least one of content, embeds, sticker_ids being non-None."
        )
