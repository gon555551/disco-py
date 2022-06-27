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
                "name": "option",
                "description": "the option",
                "required": True,
                "type": 3,
                "choices": [
                    {"name": "this", "value": "this"},
                    {"name": "that", "value": "that"},
                ],
            }
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
            bot.send_interaction("the new one works")
        else:
            bot.send_interaction("testing successfull")

    bot.loop()
