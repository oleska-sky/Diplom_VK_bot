from datetime import datetime
from pprint import pprint
import vk_api
from vk_api.exceptions import ApiError

from operator import itemgetter
from config import access_token, user_id


class VkTools():
    def __init__(self, access_token):
        self.vkapi = vk_api.VkApi(token=access_token)

    def _bdate_to_year(self, bdate):
        user_year = bdate.split('.')[2]
        now = datetime.now().year
        return now - int(user_year)

    def get_profile_info(self, user_id):
        try:
            info, = self.vkapi.method('users.get',
                                      {'user_id': user_id,
                                       'fields': 'city, bdate, sex, relation'
                                       }
                                      )
        except ApiError as e:
            info = {}
            print(f'"Сервис временно не доступен, попробуйте позднее" error = {e}')

        result_1 = {'name': (info['first_name'] + ' ' + info['last_name']) if 'first_name' in info and 'last_name' in info else None,
                  'sex': info.get('sex'),
                  'city': info.get('city')['title'] if 'city' in info else None,
                  'year': self._bdate_to_year(info.get('bdate')),
                  }


        return result_1




    def search_worksheet(self, params, offset):
        try:
            users = self.vkapi.method('users.search',
                                      {'count': 50,
                                       'offset': offset,
                                       'hometown': params['city'],
                                       'sex': 1 if params['sex'] == 2 else 2,
                                       'has_photo': True,
                                       'age_from': params['year'] - 5,
                                       'age_to': params['year'] + 5,
                                       }
                                      )
        except ApiError as e:
            users = []
            print(f'error = {e}')

        result_2 = [{
            'name': item['first_name'] + ' ' + item['last_name'],
            'id': item['id']
        } for item in users['items'] if item['is_closed'] is False
        ]
        return result_2



    def get_photos(self, id):
        try:
            photos = self.vkapi.method('photos.get',
                                       {'owner_id': id,
                                        'album_id': 'profile',
                                        'extended': 1
                                        }
                                       )

        except ApiError as e:
            photos = {}
            print(f'error = {e}')

        result = [{'owner_id': item['owner_id'],
                   'id': item['id'],
                   'likes': item['likes']['count'],
                   'comments': item['comments']['count']
                   } for item in photos['items']
                  ]

        result_sorted = sorted(result, key=itemgetter('likes', 'comments'), reverse=True)

        return result_sorted[:3]


if __name__ == '__main__':
    user_id = user_id
    tools = VkTools(access_token)
    params = tools.get_profile_info(user_id)
    worksheets = tools.search_worksheet(params, 50)
    worksheet = worksheets.pop()
    photos = tools.get_photos(worksheet['id'])

    pprint(worksheets)

