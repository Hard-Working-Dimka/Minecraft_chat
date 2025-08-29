import asyncio
import datetime

import aiofiles
import configargparse
from environs import env


async def receive_messages(message, host, port, log_path):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print('Соединение установлено.')
        async with aiofiles.open(log_path, 'a', encoding='utf-8') as f:
            await f.write(f'[{datetime.datetime.now()}] Соединение установлено. \n')
        while True:
            data = await reader.readline()
            print(f'[{datetime.datetime.now()}] {data.decode()}')

            async with aiofiles.open(log_path, 'a', encoding='utf-8') as f:
                await f.write(f'[{datetime.datetime.now()}] {data.decode()} \n')
    except Exception as e:
        print(f'ОШИБКА! Соединение прервано. {e}')
        async with aiofiles.open(log_path, 'a') as f:
            await f.write(f'[{datetime.datetime.now()}] ОШИБКА! Соединение прервано. \n')
        # asyncio.run(tcp_echo_client(message, host, port, log_path))


if __name__ == '__main__':
    env.read_env()

    parser = configargparse.ArgumentParser()
    parser.add_argument('--port', env_var='RECEIVE_PORT')
    parser.add_argument('--host', env_var='RECEIVE_HOST')
    parser.add_argument('--log_path', default='message_history.txt', type=str, env_var='LOG_PATH', )
    args = parser.parse_args()

    port = args.port
    host = args.host
    log_path = args.log_path

    asyncio.run(receive_messages('Hello World!', host, port, log_path))
