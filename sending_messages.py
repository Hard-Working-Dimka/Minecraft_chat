import asyncio
import logging
import json

import configargparse
from environs import env


async def send_message(host, port):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        data = await reader.readline()
        data = data.decode()
        print(f'Получено сообщение: {data}')
        logging.debug(f'Получено сообщение: {data}')

        while True:
            user_message = input()

            writer.write(f'{user_message} \n\n'.encode())
            await writer.drain()
            logging.debug(f'Отправлено сообщение: {user_message}')

            data = await reader.readline()
            data = data.decode()
            print(f'Получено сообщение: {data}')
            logging.debug(f'Получено сообщение: {data}')

            if json.loads(data) is None:
                print('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
                break

    except Exception as error:
        print(f'ОШИБКА! Соединение прервано. {error}')
        logging.error(f'ОШИБКА! Соединение прервано. {error}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, encoding='utf-8')
    env.read_env()

    parser = configargparse.ArgumentParser()
    parser.add_argument('--port', env_var='SENDING_PORT')
    parser.add_argument('--host', env_var='SENDING_HOST')
    args = parser.parse_args()

    port = args.port
    host = args.host

    asyncio.run(send_message(host, port))

#TODO: закрыть соединение
