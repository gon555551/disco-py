def message_obj(params: dict) -> dict:
    if "self" in params.keys():
        params.pop("self")

    to_send = dict()
    for param in params.keys():
        if params[param] is not None:
            to_send[param] = params[param]

    return to_send
