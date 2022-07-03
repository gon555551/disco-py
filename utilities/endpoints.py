def channel_messages_end(id: str) -> str:
    return f"https://discord.com/api/v10/channels/{id}/messages"


def app_commands_end(id: str) -> str:
    return f"https://discord.com/api/v10/applications/{id}/commands"


gateway_url = "wss://gateway.discord.gg/?v=10&encoding=json"
dm_endpoint = "https://discord.com/api/v10/users/@me/channels"
user_endpoint = "https://discord.com/api/v10/users/@me"
