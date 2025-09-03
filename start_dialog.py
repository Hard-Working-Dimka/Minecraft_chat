import asyncio
import logging
import json

import aiofiles
import configargparse
from environs import env


async def submit_message(message, reader, writer):
    writer.write(f'{message} \n\n'.encode())
    await writer.drain()
    logging.debug(f'Отправлено сообщение: {message}')

    data = await reader.readline()
    data = data.decode()
    logging.debug(f'Получено сообщение: {data}')


async def register(username, reader, writer):
    logging.debug('Регистрация нового пользователя.')
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

    return json_response['account_hash']


async def authorise(token, reader, writer):
    logging.debug('Авторизация в чате.')
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
        return False
    return True

async def start_dialog(port, host, message, token, username):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        logging.debug('Соединение открыто.')

        if token:
            is_authorise = await authorise(token, reader, writer)
            if is_authorise:
                await submit_message(message, reader, writer)
        if username:
            token = await register(username, reader, writer)

            writer.close()
            await writer.wait_closed()
            reader, writer = await asyncio.open_connection(host, port)

            is_authorise = await authorise(token, reader, writer)
            if is_authorise:
                await submit_message(message, reader, writer)


    except Exception as error:
        logging.error(f'ОШИБКА! Соединение прервано. {error}')

    finally:
        writer.close()
        await writer.wait_closed()
        logging.debug('Соединение закрыто.')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, encoding='utf-8')
    env.read_env()

    parser = configargparse.ArgumentParser()
    parser.add_argument('--port', env_var='SENDING_PORT', required=False)
    parser.add_argument('--host', env_var='SENDING_HOST', required=False)
    parser.add_argument('--message', required=True)
    parser.add_argument('--token', env_var='TOKEN', required=False)
    parser.add_argument('--username', required=False)
    args = parser.parse_args()

    port = args.port
    host = args.host
    message = (args.message or '').replace('\\n', '')
    token = args.token
    username = (args.username or '').replace('\\n', '')

    asyncio.run(start_dialog(port, host, message, token, username))
