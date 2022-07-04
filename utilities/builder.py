def message_obj(params: dict, id: str) -> dict:
    if "self" in params.keys():
        params.pop("self")

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

    to_send = dict()
    for param in params.keys():
        if params[param] is not None:
            to_send[param] = params[param]

    return to_send
