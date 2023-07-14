import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from datetime import datetime
from config import comunity_token, access_token
from core import VkTools
from keyboard import keyboard

# отправка сообщений

class BotInterface():
    def __init__(self, comunity_token, access_token, keyboard):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(access_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0
        self.keyboard = keyboard


    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()
                        }
                       )

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(
                        event.user_id, f'Привет, {self.params["name"]}. \n Введите: "поиск", если хотите найти пару')

                # elif event.text.lower() == 'проверка':
                #     self.message_send(
                #         event.user_id, 'Начинаем проверку для поиска анкет')
                    # if 'city' in self.params.get is None:
                    #     self.message_send(
                    #         event.user_id, "Введите город: ")
                    #     # str.capitalize(input("Введите город: "))
                    #     print('city')
                    # elif 'year' in self.params.get is None:
                    #     self.message_send(
                    #         event.user_id, "Введите год рождения: ")
                        # datetime.strftime(input("Введите дату рождения: "))


                elif event.text.lower() == 'поиск':
                    self.message_send(
                        event.user_id, 'Начинаем поиск')
                    if self.worksheets:  # сделать в виде функции
                        worksheet = self.worksheets.pop()
                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                        self.offset += 50
                    else:
                        self.worksheets = self.vk_tools.search_worksheet(
                            self.params,
                            self.offset
                        )  # находим анкеты #сделать в виде функции
                        worksheet = self.worksheets.pop()
                        """ проверка анкеты в бд в соответствии с event.user_id """
                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                        self.offset += 50

                    self.message_send(
                        event.user_id,
                        f' имя: {worksheet["name"]} ссылка: vk.com/{worksheet["id"]}',
                        attachment=photo_string
                    )
                    """ добавление анкет в бд в соответствии с event.user_id """
                elif event.text.lower() == 'пока':
                    self.message_send(
                        event.user_id, 'До встречи, ')
                else:
                    self.message_send(
                        event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, access_token, keyboard)
    bot_interface.event_handler()
