import asyncio
import logging
import json

import aiofiles
import configargparse
from environs import env


async def submit_message(message, reader, writer):
    try:
        writer.write(f'{message} \n\n'.encode())
        await writer.drain()
        logging.debug(f'Отправлено сообщение: {message}')

        data = await reader.readline()
        data = data.decode()
        logging.debug(f'Получено сообщение: {data}')

    except Exception as error:
        print(f'ОШИБКА! Соединение прервано. {error}')
        logging.error(f'ОШИБКА! Соединение прервано. {error}')


async def register(host, port, username):
    try:
        logging.debug('Регистрация нового пользователя.')
        reader, writer = await asyncio.open_connection(host, port)
        data = await reader.readline()
        data = data.decode()
        logging.debug(f'Получено сообщение: {data}')

        writer.write(f'\n'.encode())
        await writer.drain()

        data = await reader.readline()
        data = data.decode()
        logging.debug(f'Получено сообщение: {data}')

        writer.write(f'{username}\n'.encode())
        await writer.drain()
        logging.debug(f'Отправлено имя пользователя: {username}')

        data = await reader.readline()
        data = data.decode()
        logging.debug(f'Получено сообщение: {data}')

        json_response = json.loads(data)
        async with aiofiles.open('user.txt', 'a', encoding='utf-8') as file:
            await file.write(f'{json_response['nickname']} --- {json_response['account_hash']} \n')

        writer.close()
        await writer.wait_closed()
        logging.debug('Соединение закрыто.')

        return json_response['account_hash']

    except Exception as error:
        print(f'ОШИБКА! Соединение прервано. {error}')
        logging.error(f'ОШИБКА! Соединение прервано. {error}')


async def authorise(host, port, token):
    try:
        logging.debug('Авторизация в чате.')
        reader, writer = await asyncio.open_connection(host, port)
        data = await reader.readline()
        data = data.decode()
        logging.debug(f'Получено сообщение: {data}')

        writer.write(f'{token} \n\n'.encode())
        await writer.drain()
        logging.debug(f'Отправлен токен: {token}')

        data = await reader.readline()
        data = data.decode()
        logging.debug(f'Получено сообщение: {data}')

        if json.loads(data) is None:
            print('Неизвестный токен. Проверьте его или зарегистрируйтесь')

        return reader, writer

    except Exception as error:
        print(f'ОШИБКА! Соединение прервано. {error}')
        logging.error(f'ОШИБКА! Соединение прервано. {error}')


async def start_dialog(port, host, message, token, username):
    if token:
        reader, writer = await authorise(host, port, token)
        await submit_message(message, reader, writer)
    if username:
        token = await register(host, port, username)
        reader, writer = await authorise(host, port, token)
        await submit_message(message, reader, writer)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, encoding='utf-8')
    env.read_env()

    parser = configargparse.ArgumentParser()
    parser.add_argument('--port', env_var='SENDING_PORT', required=False)
    parser.add_argument('--host', env_var='SENDING_HOST', required=False)
    parser.add_argument('--message', required=True)
    parser.add_argument('--token', env_var='TOKEN', required=False)
    parser.add_argument('--username', env_var='USERNAME', required=False)
    args = parser.parse_args()

    port = args.port
    host = args.host
    message = args.message.replace('\n', '')
    token = args.token
    username = args.username.replace('\n', '')

    asyncio.run(start_dialog(port, host, message, token, username))
