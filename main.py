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
        if event.data["name"] == "new_commands":
            if (
                event.options["option_1"] == "this"
                and event.options["option_2"] == "the_other"
            ):
                bot.send_interaction("this new one works")
            else:
                bot.send_interaction("that one too")
        else:
            bot.send_interaction("testing successfull")

    bot.loop()
