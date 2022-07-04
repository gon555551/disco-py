from utilities.errors import *


def popper(params: dict) -> None:
    # pop self
    if "self" in params.keys():
        params.pop("self")

    # pop dm
    if "dm" in params.keys():
        params.pop("dm")

    # pop url
    if "url" in params.keys():
        params.pop("url")

    # pop dm_channel
    if "dm_channel" in params.keys():
        params.pop("dm_channel")
    
    # pop ephemeral
    if "ephemeral" in params.keys():
        params.pop("ephemeral")


def message_obj(params: dict, id: str = None) -> dict:
    popper(params)

    if (
        params["content"] is None
        and params["embeds"] is None
        and params["sticker_ids"] is None
    ):
        raise InvalidMessage()

    # manage replies
    if params["message_reference"] is True:
        params["message_reference"] = {"message_id": id}

        if params["allowed_mentions"] is False:
            params["allowed_mentions"] = {"replied_user": False}
        else:
            params["allowed_mentions"] = None
    elif (
        params["allowed_mentions"] is not None
        and type(params["allowed_mentions"]) == bool
    ):
        params["message_reference"] = {"message_id": id}
        params["allowed_mentions"] = {"replied_user": params["allowed_mentions"]}
    else:
        params["message_reference"] = None
        params["allowed_mentions"] = None

    # manage embeds
    if params["embeds"] is not None:
        params["embeds"] = [
            {list(item.keys())[0]: {"url": list(item.values())[0]}}
            for item in params["embeds"]
        ]

    to_send = dict()
    for param in params.keys():
        if params[param] is not None:
            to_send[param] = params[param]

    return to_send


def interaction_obj(params: dict) -> dict:
    if params["ephemeral"] is True and params["flags"] is not None:
        raise FlagsEphemeral()
    
    if params["ephemeral"]:
        params["flags"] = 64
    
    popper(params)
    
    # manage embeds
    if params["embeds"] is not None:
        params["embeds"] = [
            {list(item.keys())[0]: {"url": list(item.values())[0]}}
            for item in params["embeds"]
        ]

    to_send = dict()
    for param in params.keys():
        if params[param] is not None:
            to_send[param] = params[param]

    return {"type": 4, "data": to_send}
