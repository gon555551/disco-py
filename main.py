from client import *
import dotenv, os


if __name__ == "__main__":
    dotenv.load_dotenv()

    bot = Bot(os.environ["TOKEN"])
    bot.intents = bot.MESSAGE_CONTENT, bot.GUILD_MESSAGES

    command = {
        "name": "new_commands",
        "type": 1,
        "description": "this is a new command",
        "options": [
            {
                "name": "option_1",
                "description": "the first option",
                "required": True,
                "type": 3,
                "choices": [
                    {"name": "this", "value": "this"},
                    {"name": "that", "value": "that"},
                ],
            },
            {
                "name": "option_2",
                "description": "the other option",
                "required": False,
                "type": 3,
                "choices": [{"name": "whatever", "value": "the_other"}],
            },
        ],
    }

    bot.register(command)

    @bot.on_ready()
    def do_on_ready():
        print(f"logged in as {bot.full_name}")

    @bot.message_create()
    async def do_on_message(event: MessageCreate):
        if event.author["username"] == bot.username:
            return

        bot.send_message(event.content)

    @bot.interaction_create()
    async def do_on_interaction(event: InteractionCreate):
        match event.data["name"]:
            case "test_slash_command":
                bot.send_interaction("KAPOW", True)
            case "new_commands":
                match list(event.options.keys()):
                    case ("option_1", "option_2"):
                        match event.options["option_1"]:
                            case "this":
                                bot.send_interaction("both and this")
                            case _:
                                bot.send_interaction("both and that")
                    case _:
                        match event.options["option_1"]:
                            case "this":
                                bot.send_interaction("just this")
                            case _:
                                bot.send_interaction("just that")

    bot.loop()
