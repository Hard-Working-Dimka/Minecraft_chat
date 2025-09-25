import asyncio
import datetime
import logging

import aiofiles
import configargparse
from environs import env


async def receive_messages(host, port):
    while True:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            async with aiofiles.open('../message_history.txt', 'a', encoding='utf-8') as f:
                await f.write(f'[{datetime.datetime.now()}] Соединение установлено. \n')
            logging.debug(f'Соединение установлено.')

            while True:
                data = await reader.readline()
                data = data.decode()
                logging.debug(f'Получено сообщение: {data}')

                async with aiofiles.open('../message_history.txt', 'a', encoding='utf-8') as file:
                    await file.write(f'[{datetime.datetime.now()}] {data} \n')

        except Exception as error:
            logging.error(f'ОШИБКА! Соединение прервано. {error}')

            writer.close()
            await writer.wait_closed()
            logging.debug('Соединение закрыто.')

            async with aiofiles.open('../message_history.txt', 'a', encoding='utf-8') as file:
                await file.write(f'[{datetime.datetime.now()}] ОШИБКА! Соединение прервано. \n')
            continue

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
