import requests
import time

VK_API_URL = 'https://api.vk.com/method/'
YA_API_URL = 'https://cloud-api.yandex.net/v1/disk/resources/'


class VKuser:
    def __init__(self, token, version='5.131'):
        self.params = {'access_token': token, 'v': version}
        self.id = None
        self.name = ''
        self.fname = ''
        self.path = ''
        self.photo_count = 0
        self.photos = {}

    def get_info(self, user=None):
        resp = requests.get(VK_API_URL + 'users.get', params=self.params | {'user_id': user}).json()['response']
        if len(resp) > 0:
            self.id = resp[0]['id']
            self.name = resp[0]['first_name']
            self.fname = resp[0]['last_name']
            self.path = self.name + '_' + self.fname + '_(id' + str(self.id) + ')_VK_profile_photos/'
            return True
        else:
            return False

    def get_profile_photos(self, count=5):
        _params = {'owner_id': self.id, 'album_id': 'profile', 'rev': 0, 'extended': 1, 'photo_size': 1, 'count': count}
        resp = requests.get(VK_API_URL + 'photos.get', params=self.params | _params)
        if resp.status_code == 200:
            self.photo_count = resp.json()['response']['count']
            self.photos = resp.json()['response']['items']
        return resp.status_code


class YaDiskUploader:
    def __init__(self, token):
        self.token = token

    def make_dir(self, ya_disk_file_path):
        headers = {'Content-Type': 'application/json', 'Authorization': 'OAuth ' + self.token}
        params = {'path': ya_disk_file_path}
        requests.put(YA_API_URL, headers=headers, params=params)

    def upload(self, file_path, file_data):
        headers = {'Content-Type': 'application/json', 'Authorization': 'OAuth ' + self.token}
        params = {'path': file_path, 'overwrite': 'true'}
        url = requests.get(YA_API_URL + 'upload', headers=headers, params=params)
        if url.status_code == 200:
            resp = requests.put(url.json()['href'], data=file_data)
            return resp.status_code
        else:
            return url.status_code


with open('tt.txt') as file:
    y_token = file.readline().strip()
    v_token = file.readline().strip()

person = VKuser(v_token)
if not person.get_info(input('Введите пользователя ВКонтакте (id/screen_name): ')):
    print("Пользователь не найден!")
    exit(404)
foto_count = input('Введите количество фотографий для скачивания (5): ')
if foto_count == '':
    foto_count = 5

print(person.name, person.fname)
code = person.get_profile_photos(count=foto_count)
if code != 200:
    print('Ошибка получения данных -', code)
    exit(code)
print('Всего фотографий в профайле -', person.photo_count)
print('Фотографий для скачивания -', len(person.photos))
fotos = []
for foto in person.photos:
    f_date = time.gmtime(foto['date'])
    fotos.append({'likes': foto['likes']['count'],
                  'name': str(foto['likes']['count']) + '.jpg',
                  'date': str(f_date.tm_mday) + '_' + str(f_date.tm_mon) + '_' + str(f_date.tm_year),
                  'time': str(f_date.tm_hour) + ':' + str(f_date.tm_min) + ':' + str(f_date.tm_sec),
                  'url': foto['sizes'][-1]['url'],
                  'height': foto['sizes'][-1]['height'],
                  'width': foto['sizes'][-1]['width']
                  })

fotos.sort(key=lambda a: a['likes'])
for i in range(len(fotos)-1):
    if fotos[i]['likes'] == fotos[i+1]['likes']:
        if fotos[i]['date'] == fotos[i+1]['date']:
            fotos[i]['name'] = str(fotos[i]['likes']) + '-' + fotos[i]['date'] + '_' + fotos[i]['time'] + '.jpg'
            fotos[i+1]['name'] = str(fotos[i+1]['likes']) + '-' + fotos[i+1]['date'] + '_' + fotos[i+1]['time'] + '.jpg'
        else:
            fotos[i]['name'] = str(fotos[i]['likes']) + '-' + fotos[i]['date'] + '.jpg'
            fotos[i+1]['name'] = str(fotos[i+1]['likes']) + '-' + fotos[i+1]['date'] + '.jpg'

ya_disk = YaDiskUploader(y_token)
ya_disk.make_dir(person.path)
result = []
i = 0
for foto in fotos:
    i += 1
    print(i, 'фото - Скачиваем.', end='')
    jpeg = requests.get(foto['url'])
    if jpeg.status_code == 200:
        print(' Загружаем на YandexDisk.', end='')
        code = ya_disk.upload(person.path + foto['name'], jpeg.content)
        if code == 201:
            result.append(' {"file_name": "' + foto['name'] + '",\n')
            result.append('  "size": "' + str(foto['height']) + 'x' + str(foto['width']) + '"},\n')
            print(' Ok')
        else:
            print(' Ошибка загрузки -', code)
    else:
        print(' Ошибка скачивания -', jpeg.status_code)
print('Загружено', len(result) // 2, 'фото')

result[0] = '[' + result[0][1:]
result[-1] = result[-1][:-2] + ']'
with open('result.json', 'w') as file:
    file.writelines(result)
