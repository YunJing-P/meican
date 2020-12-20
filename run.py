from meican_api import Meican

username = ''
password = ''
filter_dict = {
    'work_days': [0, 1, 2, 3, 4],
    'price': 15.0,
    'price_limt': True,
    'ban_keys': [],
    'start_date': '',
    'end_date': '',
    'address': '广州市天河区黄埔大道西122号星辉中心17楼',
    'delay_time': 0.1
}

meican = Meican(username, password, filter_dict)
meican.radom_add()