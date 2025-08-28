import asyncio
import datetime

import aiofiles


async def tcp_echo_client(message):
    while True:
        reader, writer = await asyncio.open_connection(
            'minechat.dvmn.org', 5000)

        # print(f'Send: {message!r}')
        # writer.write(message.encode())
        # await writer.drain()

        data = await reader.read(100)
        print(f'[{datetime.datetime.now()}] {data.decode()}')

        # print('Close the connection')
        # writer.close()
        # await writer.wait_closed()
        async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as f:
            await f.write(f'[{datetime.datetime.now()}] {data.decode()} \n')


asyncio.run(tcp_echo_client('Hello World!'))
