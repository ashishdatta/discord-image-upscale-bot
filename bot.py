import asyncio
from dotenv import load_dotenv
import os
from PIL import Image
from io import BytesIO
import requests
import nextcord
from nextcord.ext import commands
import io
import warnings
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
STABILITY_KEY = os.getenv("STABILITY_TOKEN")
bot = commands.Bot()
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))
guild_ids = [DEV_GUILD_ID, GUILD_ID]


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

intents = nextcord.Intents.default()
intents.message_content = True
bot = Bot(command_prefix="$", intents=intents)

@bot.command()
async def upscale_image(img):
    stability_api = client.StabilityInference(
        key=STABILITY_KEY, # API Key reference.
        engine="esrgan-v1-x2plus", # The name of the upscaling model we want to use.
        verbose=True, # Print debug messages.
    )
    answers = stability_api.upscale(
    init_image=img,
    width=1000
    )
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please submit a different image and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                big_img = Image.open(io.BytesIO(artifact.binary))
                big_img.save("imageupscaled" + ".png") # Save our image to a local file.

@bot.listen()
async def on_message(message):
    if len(message.attachments) > 0:
        if "jpg" in message.attachments[0].filename or "png" in message.attachments[0].filename or "jpeg" in message.attachments[0].filename:
            res = requests.get(message.attachments[0].url)
            img = Image.open(BytesIO(res.content)).convert("RGB")
            if img.size[0] < 512:
                await upscale_image(img)
                await message.reply(f"Low res image detected {img.size[0]}x{img.size[1]} Resized", files=[nextcord.File('imageupscaled.png')])

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
                asyncio.gather(bot.start(TOKEN))
                )
    except KeyboardInterrupt:
        loop.run_until.complete(bot.close())
    finally:
        loop.close()
