import asyncio

import configargparse
from environs import env


async def send_message(host, port):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        data = await reader.read(100)
        print(f'Received: {data.decode()!r}')
        while True:
            user_message = input()

            writer.write(f'{user_message} \n\n'.encode())
            await writer.drain()

            data = await reader.readline()
            print(f'Received: {data.decode()!r}')

            # writer.close()
            # await writer.wait_closed()
    except Exception as e:
        print(f'ОШИБКА! Соединение прервано. {e}')


if __name__ == '__main__':
    env.read_env()

    parser = configargparse.ArgumentParser()
    parser.add_argument('--port', env_var='SENDING_PORT')
    parser.add_argument('--host', env_var='SENDING_HOST')
    args = parser.parse_args()

    port = args.port
    host = args.host

    asyncio.run(send_message(host, port))
