class CommandMissing(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"{name} isn't a currently active global command.")