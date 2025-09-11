import asyncio
import datetime

import aiofiles
import gui
import configargparse
from environs import env


async def save_messages(messages_queue):
    async with aiofiles.open('message_history.txt', 'r', encoding='utf-8') as f: #TODO: use filename
        async for line in f:
            await messages_queue.put(line)


async def read_msgs(messages_queue, reader, writer):
    while True:
        async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as f:
            await f.write(f'[{datetime.datetime.now()}] Соединение установлено. \n')

        data = await reader.readline()
        data = data.decode()
        messages_queue.put_nowait(data)

        async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as file:
            await file.write(f'[{datetime.datetime.now()}] {data} \n')


async def start_listening(host, port):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    await save_messages(messages_queue)

    try:
        reader, writer = await asyncio.open_connection(host, port)
        await asyncio.gather(
            read_msgs(messages_queue, reader, writer),
            gui.draw(messages_queue, sending_queue, status_updates_queue),
        )

    except Exception as error:
        writer.close()
        await writer.wait_closed()

        async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as file:
            await file.write(f'[{datetime.datetime.now()}] ОШИБКА! Соединение прервано. \n')


if __name__ == '__main__':
    env.read_env()

    parser = configargparse.ArgumentParser()
    parser.add_argument('--port', env_var='RECEIVE_PORT')
    parser.add_argument('--host', env_var='RECEIVE_HOST')
    args = parser.parse_args()

    port = args.port
    host = args.host

    asyncio.run(start_listening(host, port))
