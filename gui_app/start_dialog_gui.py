import asyncio
import datetime
import json
import logging
import socket

import aiofiles
import gui
import configargparse
from environs import env
from tkinter import messagebox
from exceptions import InvalidToken
from async_timeout import timeout
from anyio import create_task_group

TIMEOUT_BETWEEN_CONNECTIONS = 10
TIMEOUT_TEST_CONNECTION = 5


async def handle_connection(status_updates_queue, messages_queue, sending_queue, watchdog_queue):
    try:
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
        receive_reader, receive_writer = await asyncio.open_connection(receive_host, receive_port)
        status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)

        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
        send_reader, send_writer = await asyncio.open_connection(send_host, send_port)
        status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)

        await authorise(token, send_reader, send_writer, messages_queue, status_updates_queue)
    except InvalidToken as error:
        receive_writer.close()
        await receive_writer.wait_closed()

        send_writer.close()
        await send_writer.wait_closed()

        messagebox.showerror('Неверный токен', 'Проверьте токен, сервер его не узнал.')

        async with aiofiles.open('../message_history.txt', 'a', encoding='utf-8') as file:
            await file.write(f'[{datetime.datetime.now()}] ОШИБКА! Соединение прервано. \n')
        raise Exception

    while True:
        try:
            async with create_task_group() as tg:
                tg.start_soon(watch_for_connection, watchdog_queue, sending_queue)
                tg.start_soon(read_msgs, messages_queue, receive_reader, watchdog_queue)
                tg.start_soon(send_msgs, sending_queue, send_writer, watchdog_queue)

        except* (socket.gaierror, ConnectionAbortedError) as error:
            tg.cancel_scope.cancel()
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)
            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)

            await asyncio.sleep(TIMEOUT_BETWEEN_CONNECTIONS)
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
            receive_reader, receive_writer = await asyncio.open_connection(receive_host, receive_port)
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)

            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
            send_reader, send_writer = await asyncio.open_connection(send_host, send_port)
            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)


async def watch_for_connection(watchdog_queue, sending_queue):
    while True:
        try:
            async with timeout(TIMEOUT_TEST_CONNECTION):
                await watchdog_queue.get()
        except asyncio.TimeoutError:
            sending_queue.put_nowait(''.encode())


async def save_messages(messages_queue):
    async with aiofiles.open('../message_history.txt', 'r', encoding='utf-8') as f:
        async for message in f:
            await messages_queue.put(message)


async def send_msgs(sending_queue, send_writer, watchdog_queue):
    while True:
        message = await sending_queue.get()

        send_writer.write(f'{message} \n\n'.encode())
        await send_writer.drain()

        watchdog_queue.put_nowait('Connection is alive. Message sent')
        await asyncio.sleep(1)


async def authorise(token, reader, writer, messages_queue, status_updates_queue):
    data = await reader.readline()
    data = data.decode()

    writer.write(f'{token} \n\n'.encode())
    await writer.drain()

    data = await reader.readline()
    data = data.decode()

    if json.loads(data) is None:
        raise InvalidToken
    json_response = json.loads(data)

    messages_queue.put_nowait(f'Выполнена авторизация. Пользователь {json_response['nickname']}')
    event = gui.NicknameReceived(json_response['nickname'])
    status_updates_queue.put_nowait(event)


async def read_msgs(messages_queue, reader, watchdog_queue):
    while True:
        async with aiofiles.open('../message_history.txt', 'a', encoding='utf-8') as f:
            await f.write(f'[{datetime.datetime.now()}] Соединение установлено. \n')

        data = await reader.readline()
        data = data.decode()
        messages_queue.put_nowait(data)

        watchdog_queue.put_nowait('Connection is alive. New message in chat')

        async with aiofiles.open('../message_history.txt', 'a', encoding='utf-8') as file:
            await file.write(f'[{datetime.datetime.now()}] {data} \n')


async def start_chat(receive_port, receive_host, send_port, send_host, token):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()

    try:
        await save_messages(messages_queue)

        async with create_task_group() as tg:
            tg.start_soon(handle_connection, status_updates_queue, messages_queue, sending_queue, watchdog_queue),
            tg.start_soon(gui.draw, messages_queue, sending_queue, status_updates_queue),

    except Exception as error:
        async with aiofiles.open('../message_history.txt', 'a', encoding='utf-8') as file:
            await file.write(f'[{datetime.datetime.now()}] ОШИБКА! Соединение прервано. {error} \n')


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

    watchdog_logger = logging.getLogger('watchdog_logger')
    watchdog_logger.setLevel(logging.INFO)
    watchdog_logger.setLevel(logging.INFO)
    watchdog_logger.addHandler(logging.StreamHandler())
    try:
        asyncio.run(start_chat(receive_port, receive_host, send_port, send_host, token))
    except (KeyboardInterrupt, gui.TkAppClosed):
        pass
