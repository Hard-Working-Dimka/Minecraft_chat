import asyncio
import datetime
import json
import logging

import aiofiles
import gui
import configargparse
from environs import env
from tkinter import messagebox
from exceptions import InvalidToken
from async_timeout import timeout
from anyio import create_task_group

#TODO: подумать над авторизацией
async def handle_connection(status_updates_queue, messages_queue, sending_queue, watchdog_queue):
    while True:
        try:
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
            receive_reader, receive_writer = await asyncio.open_connection(receive_host, receive_port)
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)

            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
            send_reader, send_writer = await asyncio.open_connection(send_host, send_port)
            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)

            async with create_task_group() as tg:
                tg.start_soon(watch_for_connection, watchdog_queue)
                tg.start_soon(read_msgs, messages_queue, receive_reader, watchdog_queue)
                tg.start_soon(send_msgs, sending_queue, send_writer, watchdog_queue)
                tg.start_soon(authorise, token, send_reader, send_writer, messages_queue, status_updates_queue)
        except* ConnectionError as excgroup:
            tg.cancel_scope.cancel()

        except* InvalidToken as error:
            messagebox.showerror('Неверный токен', 'Проверьте токен, сервер его не узнал.')
            tg.cancel_scope.cancel()


            async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as file:
                await file.write(f'[{datetime.datetime.now()}] ОШИБКА! Соединение прервано. \n')

        raise


async def watch_for_connection(watchdog_queue):
    while True:
        time = 5
        try:
            async with timeout(time):
                event = await watchdog_queue.get()
        except asyncio.TimeoutError:
            watchdog_logger.info(f'[{datetime.datetime.now()}] {time}s timeout is elapsed')
            raise ConnectionError

        watchdog_logger.info(f'[{datetime.datetime.now()}] {event}')


async def save_messages(messages_queue):
    async with aiofiles.open('message_history.txt', 'r', encoding='utf-8') as f:  # TODO: use filename
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
    json_response = json.loads(data)

    if json.loads(data) is None:
        raise InvalidToken

    messages_queue.put_nowait(f'Выполнена авторизация. Пользователь {json_response['nickname']}')
    event = gui.NicknameReceived(json_response['nickname'])
    status_updates_queue.put_nowait(event)


async def read_msgs(messages_queue, reader, watchdog_queue):
    while True:
        async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as f:
            await f.write(f'[{datetime.datetime.now()}] Соединение установлено. \n')

        data = await reader.readline()
        data = data.decode()
        messages_queue.put_nowait(data)

        # watchdog_queue.put_nowait('Connection is alive. New message in chat') #TODO: раскомментить

        async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as file:
            await file.write(f'[{datetime.datetime.now()}] {data} \n')


async def start_chat(receive_port, receive_host, send_port, send_host, token):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()

    await save_messages(messages_queue)

    await asyncio.gather(
        handle_connection(status_updates_queue, messages_queue, sending_queue, watchdog_queue),
        gui.draw(messages_queue, sending_queue, status_updates_queue),
    )

    # except InvalidToken as error:
    #     receive_writer.close()
    #     await receive_writer.wait_closed()
    #
    #     send_writer.close()
    #     await send_writer.wait_closed()
    #
    #     messagebox.showerror('Неверный токен', 'Проверьте токен, сервер его не узнал.')
    #
    #     async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as file:
    #         await file.write(f'[{datetime.datetime.now()}] ОШИБКА! Соединение прервано. \n')

    # except Exception as error:
    #     print('привет')
    #     async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as file:
    #         await file.write(f'[{datetime.datetime.now()}] ОШИБКА! Соединение прервано. {error} \n')


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

    asyncio.run(start_chat(receive_port, receive_host, send_port, send_host, token))
