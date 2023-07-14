import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from config import comunity_token, peer_id

vk_session = vk_api.VkApi(token=comunity_token)

vk = vk_session.get_api()


keyboard = VkKeyboard(one_time=False, inline=True)
keyboard.add_callback_button('поиск', color=VkKeyboardColor.POSITIVE)
keyboard.add_callback_button('пока', color=VkKeyboardColor.PRIMARY)

def sender(peer_id, message):
    vk.messages.send(
        peer_id = peer_id,
        message = 'Выберите кнопку',
        keyboard = keyboard,
        random_id = 0
        )