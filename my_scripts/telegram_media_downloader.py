from telethon import TelegramClient
import os
import telegram_media_downloader_creds as creds

api_id = creds.API_ID
api_hash = creds.API_HASH

client = TelegramClient('test1', api_id, api_hash)

async def main():
    # me = await client.get_me()
    # print(me.stringify())

    async for message in client.iter_messages('dztup'):
        # print(message.id, message.text)
        # if message.id == 528 or message.id == 529:
        #     print(message)
        if message.media:
            path = await message.download_media()
            print('File ', message.id, ' saved to: ', path)


with client:
    client.loop.run_until_complete(main())

