import asyncio
import json
from tkinter import Tk, Entry, Button, Label, W, E, N, messagebox
import tkinter as tk

import aiofiles
from anyio import create_task_group
from environs import env


async def draw_successful_registration(account_hash, nickname, interval=1 / 120):
    title = Label(text="Вы успешно зарегистрировались!", font='Arial 32', bd=20, bg='lightblue', foreground='black')
    title.grid(row=4, column=2, pady=10, padx=10)

    nickname_label = Label(text="Имя:", font='Arial 32', bd=20, bg='lightblue', foreground='black')
    nickname_label.grid(row=5, column=1, sticky=W, pady=10, padx=10)

    nickname_field = Label(text=nickname, font='Arial 32', bd=20, bg='lightblue', foreground='black')
    nickname_field.grid(row=5, column=2, columnspan=2, sticky=W + E, pady=10, padx=10)

    token_label = Label(text="Токен входа:", font='Arial 32', bd=20, bg='lightblue', foreground='black')
    token_label.grid(row=6, olumn=1, sticky=W, pady=10, padx=10)

    token_field = Label(text=account_hash, font='Arial 32', bd=20, bg='lightblue', foreground='black')
    token_field.grid(row=6, column=2, columnspan=2, sticky=W + E, pady=10, padx=10)

    await asyncio.sleep(interval)


async def register(reader, writer, entry):
    username = entry.get()

    data = await reader.readline()
    data = data.decode()

    writer.write(f'\n'.encode())
    await writer.drain()

    data = await reader.readline()
    data = data.decode()

    writer.write(f'{username}\n'.encode())
    await writer.drain()

    data = await reader.readline()
    data = data.decode()

    json_response = json.loads(data)
    async with aiofiles.open('../user.txt', 'a', encoding='utf-8') as file:
        await file.write(f'{json_response['nickname']} --- {json_response['account_hash']} \n')

    account_hash = json_response['account_hash']
    nickname = json_response['nickname']

    await draw_successful_registration(account_hash, nickname)


async def update_tk(root_frame, interval=1 / 120):
    while True:
        try:
            root_frame.update()
        except tk.TclError:
            # if application has been destroyed/closed
            raise Exception
        await asyncio.sleep(interval)


async def main(sending_port, sending_host):
    try:
        reader, writer = await asyncio.open_connection(sending_host, sending_port)
    except Exception as error:
        writer.close()
        await writer.wait_closed()
        messagebox.showerror('Ошибка соединения', 'Повторите попытку позже!.')

    root = tk.Tk()
    root.title('Регистрация в чате Майнкрафтера')
    root.configure(bg="lightblue")

    main_title = Label(text='Регистрация нового аккаунта', font='Arial 35', bd=20, bg='lightblue', foreground='black')
    main_title.grid(row=0, column=0, columnspan=10, sticky=N)

    user_nickname = Label(text="Имя:", font='Arial 32', bd=20, bg='lightblue', foreground='black')
    user_nickname.grid(row=1, column=1, sticky=W, pady=10, padx=10)

    nickname_input_field = Entry(font='Arial 32', bg='white', fg='black')
    nickname_input_field.grid(row=1, column=2, columnspan=2, sticky=W + E, padx=40)

    Button(text="Отправить", width=15, height=-3, font='Arial 20',
           command=lambda: asyncio.create_task(register(reader, writer, nickname_input_field))).grid(row=3,
                                                                                                     column=3,
                                                                                                     padx=40)

    async with create_task_group() as tg:
        tg.start_soon(update_tk, root),

    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':
    env.read_env()
    sending_port = env('SENDING_PORT')
    sending_host = env('SENDING_HOST')
    try:
        asyncio.run(main(sending_port, sending_host))
    except (KeyboardInterrupt, Exception):
        pass
