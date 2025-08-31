import asyncio
import datetime
import logging

import aiofiles
import configargparse
from environs import env


async def receive_messages(host, port):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print('Соединение установлено.')
        async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as f:
            await f.write(f'[{datetime.datetime.now()}] Соединение установлено. \n')
        logging.debug(f'Соединение установлено.')

        while True:
            data = await reader.readline()
            data = data.decode()
            print(f'[{datetime.datetime.now()}] {data}')
            logging.debug(f'Получено сообщение: {data}')

            async with aiofiles.open('message_history.txt', 'a', encoding='utf-8') as file:
                await file.write(f'[{datetime.datetime.now()}] {data} \n')

    except Exception as error:
        print(f'ОШИБКА! Соединение прервано. {error}')
        logging.error(f'ОШИБКА! Соединение прервано. {error}')

        async with aiofiles.open('message_history.txt', 'a') as file:
            await file.write(f'[{datetime.datetime.now()}] ОШИБКА! Соединение прервано. \n')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, encoding='utf-8')
    env.read_env()

    parser = configargparse.ArgumentParser()
    parser.add_argument('--port', env_var='RECEIVE_PORT')
    parser.add_argument('--host', env_var='RECEIVE_HOST')
    args = parser.parse_args()

    port = args.port
    host = args.host

    asyncio.run(receive_messages(host, port))

