import asyncio
import datetime
import json
from time import sleep

import aiofiles
import gui
import configargparse
from environs import env


async def save_messages(messages_queue):
    async with aiofiles.open('message_history.txt', 'r', encoding='utf-8') as f:  # TODO: use filename
        async for message in f:
            await messages_queue.put(message)


async def send_msgs(sending_queue, send_writer):
    while True:
        message = await sending_queue.get()
        print(message)
        # await messages_queue.put(message)

        send_writer.write(f'{message} \n\n'.encode())
        await send_writer.drain()

        await asyncio.sleep(1)


async def authorise(token, reader, writer, messages_queue):
    data = await reader.readline()
    data = data.decode()

    writer.write(f'{token} \n\n'.encode())
    await writer.drain()

    data = await reader.readline()
    data = data.decode()
    json_response = json.loads(data)

    messages_queue.put_nowait(f'Выполнена авторизация. Пользователь {json_response['nickname']}')

    # if json.loads(data) is None:
    #     print('Неизвестный токен. Проверьте его или зарегистрируйтесь')
    #     return False
    # return True


async def read_msgs(messages_queue, reader):
    while True:
        async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as f:
            await f.write(f'[{datetime.datetime.now()}] Соединение установлено. \n')

        data = await reader.readline()
        data = data.decode()
        messages_queue.put_nowait(data)

        async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as file:
            await file.write(f'[{datetime.datetime.now()}] {data} \n')


async def start_listening(receive_port, receive_host, send_port, send_host, token):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    await save_messages(messages_queue)

    try:
        receive_reader, receive_writer = await asyncio.open_connection(receive_host, receive_port)
        send_reader, send_writer = await asyncio.open_connection(send_host, send_port)
        await asyncio.gather(
            read_msgs(messages_queue, receive_reader),
            authorise(token, send_reader, send_writer, messages_queue),
            send_msgs(sending_queue, send_writer),
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
    parser.add_argument('--receive_port', env_var='RECEIVE_PORT')
    parser.add_argument('--receive_host', env_var='RECEIVE_HOST')
    parser.add_argument('--send_port', env_var='SENDING_PORT', required=False)
    parser.add_argument('--send_host', env_var='SENDING_HOST', required=False)
    parser.add_argument('--token', env_var='TOKEN', required=False)
    parser.add_argument('--username', required=False)
    args = parser.parse_args()

    receive_port = args.receive_port
    receive_host = args.receive_host
    send_port = args.send_port
    send_host = args.send_host
    token = args.token
    username = (args.username or '').replace('\\n', '')

    asyncio.run(start_listening(receive_port, receive_host, send_port, send_host, token))
