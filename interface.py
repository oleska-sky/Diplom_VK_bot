import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import pandas as pd
from pprint import pprint

from config import comunity_token, access_token
from core import VkTools
from data_store import check_user, add_user, engine


# отправка сообщений
class BotInterface:
    def __init__(self, comunity_token, access_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(access_token)
        self.check_user = check_user
        self.add_user = add_user
        self.params = {}
        self.worksheets = []
        self.offset = 0


    def message_send(self, user_id, message, attachment=None, keyboard=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id(),
                        'keyboard': keyboard
                        }
                       )

    def create_keyboard(self, buttons, button_colors):

        keyboard = VkKeyboard(one_time=False)
        for btn, btn_color in zip(buttons, button_colors):
            keyboard.add_button(btn, btn_color)
        return keyboard

    def event_handler(self):

        for event in self.longpoll.listen():
            buttons = ['привет', 'поиск', 'пока']
            button_colors = VkKeyboardColor.SECONDARY, VkKeyboardColor.PRIMARY, \
                VkKeyboardColor.SECONDARY
            keyboard = self.create_keyboard(buttons, button_colors)

            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                message = event.text.lower()
                try:
                    if message == 'привет':
                        self.params = self.vk_tools.get_profile_info(event.user_id)
                        self.message_send(
                            event.user_id,
                            f'Привет, {self.params["name"]}! Жми "поиск"',
                            keyboard=keyboard.get_keyboard())
                        if not self.params['city']:  # проверка в анкете:город
                            self.city_input(event.user_id)
                        elif not self.params['year']:  # проверка в анкете: возраст
                            self.year_input(event.user_id)

                    elif event.text.lower() == 'поиск':
                        self.message_send(
                            event.user_id, 'Начинается поиск, жми "поиск"', keyboard=keyboard.get_keyboard())
                        if self.worksheets:
                            worksheet = self.worksheets.pop()
                            photos = self.vk_tools.get_photos(worksheet['id'])
                            photo_string = ''
                            for photo in photos:
                                photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                        else:
                            self.worksheets = self.vk_tools.search_worksheet(self.params, self.offset)
                            worksheet = self.worksheets.pop()
                            self.offset += 50

                            """ проверка анкеты в бд в соответствии с event.user_id """
                        while self.check_user(engine, event.user_id, worksheet["id"]) is True:
                            if len(self.worksheets):
                                worksheet = self.worksheets.pop()

                        """ добавление анкет в бд в соответствии с event.user_id """
                        if self.check_user(engine, event.user_id, worksheet["id"]) is False:
                            self.add_user(engine, event.user_id, worksheet["id"])
                            photos = self.vk_tools.get_photos(worksheet['id'])
                            photo_string = ''
                            for photo in photos:
                                photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

                            self.message_send(
                                event.user_id,
                                f'имя: {worksheet["name"]} ссылка: vk.com/id{worksheet["id"]}',
                                attachment=photo_string
                            )

                    elif message == 'пока':
                        self.message_send(
                            event.user_id,
                            f'До встречи, {self.params["name"]}',
                            keyboard=keyboard.get_keyboard())
                except:
                    self.message_send(
                            event.user_id, 'Неизвестная команда, уточните выбор')

    # 'Начинаем проверку данных в анкете пользователя анкет'
    def city_input(self, user_id):
        url = 'https://ru.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D0%B3%D0%BE%D1%80%D0%BE%D0%B4%D0%BE%D0%B2_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8'
        df = pd.read_html(url)[0]
        df_city = df['Город']
        cities = df_city.values.tolist()

        self.message_send(user_id, f' Введите город для поиска:')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.params['city'] = event.text.title()
                if self.params['city'] in cities:
                    self.message_send(user_id, f'{self.params["city"]} - город выбран. Введите: "поиск"')
                else:
                    self.message_send(user_id, f' {self.params["name"]}.\n Уточните город, пожалуйста')
                break

    def year_input(self, user_id):
        self.message_send(user_id, f'{self.params["name"]}, введите количество лет:')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.params['year'] = int(event.text)
                break
            try:
                if self.params['year']>18:
                    self.message_send(user_id, f' {self.params["year"]} - количество лет выбрано. Введите: "поиск"')
            except KeyError:
                self.message_send(user_id, f' {self.params["name"]}. \n Уточните количество лет, пожалуйста')

if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, access_token)
    bot_interface.event_handler()

