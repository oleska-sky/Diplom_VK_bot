import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from datetime import datetime
from config import comunity_token, access_token
from core import VkTools
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from data_store import check_user, add_user, engine

# отправка сообщений

class BotInterface():
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
        keyboard = VkKeyboard.get_empty_keyboard() #Получить json пустой клавиатуры.
        keyboard = VkKeyboard(one_time=False)
        for btn, btn_color in zip(buttons, button_colors):
            keyboard.add_button(btn, btn_color)
        return keyboard

    def event_handler(self):
        for event in self.longpoll.listen():
            buttons = ['привет', 'поиск', 'пока']# кнопки
            button_colors = VkKeyboardColor.SECONDARY, VkKeyboardColor.PRIMARY, VkKeyboardColor.SECONDARY
            keyboard = self.create_keyboard(buttons, button_colors)

            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'Привет, {self.params["name"]}!', keyboard=keyboard.get_keyboard())
                    if not self.params['city']:# проверка на наличие в анкете:город
                        self.city_input(event.user_id)
                    elif not self.params['year']:#  проверка на наличие в анкете: возраст
                        self.year_input(event.user_id)
                elif event.text.lower() == 'поиск':
                    self.message_send(
                        event.user_id, 'Начинаем поиск, жми "поиск"', keyboard=keyboard.get_keyboard())

                    if self.worksheets:
                        worksheet = self.worksheets.pop()
                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                    else:
                        self.worksheets = self.vk_tools.search_worksheet(self.params, self.offset)
                        worksheet = self.worksheets.pop()
                        """ проверка анкеты в бд в соответствии с event.user_id """
                    while self.check_user(engine, event.user_id, worksheet["id"]) is True:
                        worksheet = self.worksheets.pop()
                    """ добавление анкет в бд в соответствии с event.user_id """
                    if self.check_user(engine, event.user_id, worksheet["id"]) is False:
                        self.add_user(engine, event.user_id, worksheet["id"])
                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                        self.offset += 50

                    self.message_send(
                        event.user_id, f'имя: {worksheet["name"]} ссылка: vk.com/{worksheet["id"]}',
                        attachment=photo_string
                    )


                elif event.text.lower() == 'пока':
                    self.message_send(
                        event.user_id, f'До встречи, {self.params["name"]}', keyboard=keyboard.get_keyboard())
                else:
                    self.message_send(
                        event.user_id, 'Неизвестная команда, уточните выбор')




    # 'Начинаем проверку данных в анкете пользователя анкет'

    def city_input(self, user_id):
        self.message_send(user_id, f'{self.params["name"]}, введите город для поиска:')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.params['city'] = event.text.title()
                break
        if self.params['city']:
            self.message_send(user_id, f' {self.params["city"]} - город выбран. Введите: "поиск"')
        else:
           self.message_send(user_id, f' {self.params["name"]}.\n Уточните город, пожалуйста')

    def year_input(self, user_id):
       self.message_send(user_id, f'{self.params["year"]}, введите количество лет:')
       for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.params['year'] = int(event.text)
                break
       if self.params['year']>18:
           self.message_send(user_id, f' {self.params["year"]} - количество лет выбрано. Введите: "поиск"')
       else:
           self.message_send(user_id, f' {self.params["name"]}. \n Уточните количество лет, пожалуйста')



if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, access_token)
    bot_interface.event_handler()
