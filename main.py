from client import *
import dotenv, os


if __name__ == "__main__":
    dotenv.load_dotenv()

    bot = Bot(os.environ["TOKEN"])
    bot.intents = bot.MESSAGE_CONTENT, bot.GUILD_MESSAGES

    @bot.on_ready()
    def do_on_ready():
        print(f"logged in as {bot.full_name}")

    bot.loop()
