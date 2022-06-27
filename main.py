from client import *
import dotenv, os


if __name__ == "__main__":
    dotenv.load_dotenv()

    bot = Bot(os.environ["TOKEN"])
    bot.intents = bot.MESSAGE_CONTENT, bot.GUILD_MESSAGES

    @bot.on_ready()
    def do_on_ready():
        print(f"logged in as {bot.full_name}")

    @bot.message_create()
    async def do_on_message(event: MessageCreate):
        if event.author["username"] == bot.username:
            return

        bot.send_message(event, "bruh no way")

    @bot.interaction_create()
    async def do_on_interaction(event: InteractionCreate):
        bot.send_interaction(event, "testing successfull")

    bot.loop()
