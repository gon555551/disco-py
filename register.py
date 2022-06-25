import requests

# register commands endpoint
reg_url = "https://discord.com/api/v10/applications/976890311051726859/commands"

# auth
auth = {
    "Authorization": "Bot OTc2ODkwMzExMDUxNzI2ODU5.GLfLQJ.2FrH0usmyLFgphww5pe9GleZ402XE14ptjaSOU"
}

def send(json: dict, id: str, token: str):
    url = f"https://discord.com/api/v10/interactions/{id}/{token}/callback"
    print(url)
    print(json)

    r = requests.post(url, json=json)
    print(r.text)
