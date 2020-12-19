import requests
import datetime
import logging

logging.basicConfig(level = logging.CRITICAL,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
class Meican:
    def __init__(self, username, password) -> None:
        self.base_url = 'https://meican.com/'
        self.base_params = {
            'client_id': 'Xqr8w0Uk4ciodqfPwjhav5rdxTaYepD',    # 看着是美餐固定的client信息
            'client_secret': 'vD11O6xI9bG3kqYRu9OyPAHkRGxLh4E',
        }
        self.username = username
        self.password = password

    # 拼接url函数
    def build_url(self, part_url, ext_params) -> str:
        kv_list = []
        params_cp = self.base_params.copy()
        for k in ext_params.keys():
            kv_list.append('{}={}'.format(k, ext_params[k]))
        for k in params_cp.keys():
            kv_list.append('{}={}'.format(k, params_cp[k]))
        return self.base_url + part_url + '?' + '&'.join(kv_list)

    def post(self, url, data, headers=None) -> object:
        if None == headers:headers = {'cookie': self.cookie}
        r = requests.post(url=url, headers=headers, data=data)
        if 200 == r.status_code:
            return r
        else:
            logging.critical('POST请求响应码异常，url：{}，data：{}，header：{}'.format(url, data, headers))
            raise ValueError('POST请求响应码异常')

    def get(self, url, headers=None) -> object:
        if None == headers:headers = {'cookie': self.cookie}
        r = requests.get(url=url, headers=headers)
        if 200 == r.status_code:
            return r
        else:
            logging.critical('GET请求响应码异常，url：{}，header：{}'.format(url, headers))
            raise ValueError('GET请求响应码异常')

    def set_cookie(self) -> None:
        # 登录拿到cookie
        arg_dict = {
            'grant_type': 'password',
            'meican_credential_type': 'password',
            'password': self.password,
            'username': self.username,
            'username_type': 'username'
        }
        headers = {'Context-Type': 'application/x-www-form-urlencoded'}
        part_url = 'preference/preorder/api/v2.0/oauth/token'
        ext_params = {'remember': 'true'}
        response = self.post(self.build_url(part_url, ext_params), arg_dict, headers)
        cookies = response.cookies.items()
        cookie_str = ''
        for k, v in cookies:
            cookie_str += '{}={};'.format(k, v)
        self.cookie = cookie_str
        if self.cookie:
            logging.info('获取cookie成功：{}'.format(self.cookie))
        else:
            logging.critical('获取cookie失败')
            raise ValueError('获取cookie失败')


    # 查看已点菜单
    def show_ordered(self, begin_date, end_date):
        '''
            begin_date: 起始时间，格式 2020-12-19
            end_date: 结束时间，只能查本周&d+7集合，格式 2020-12-19
        '''
        part_url = 'preorder/api/v2.1/calendaritems/list'
        ext_params = {
            'withOrderDetail': 'false',
            'beginDate': begin_date,
            'endDate': end_date,    # 
        }
        response = self.get(self.build_url(part_url, ext_params))
        ordered_dict = {}
        for i in response.json()['dateList']:
            ordered_dict[i['date']] = {}
            for j in i['calendarItemList']:
                try:
                    dish = j['corpOrderUser']['restaurantItemList'][0]['dishItemList'][0]['dish']['name']
                except:
                    dish = 'None'
                ordered_dict[i['date']][j['title']] = {
                    'tabUniqueId': j['userTab']['uniqueId'],
                    'dish': dish,
                    'target_time': datetime.datetime.fromtimestamp(j['targetTime']/1000).strftime("%Y-%m-%d %H:%M"),
                    'namespace': j['userTab']['corp']['namespace']
                }

        # 输出给用户看的 随时可以屏蔽
        print('当前已点')
        for i in ordered_dict.keys():
            print_str = ''
            print_str += i + ': '
            for j in ordered_dict[i].keys():
                print_str += ordered_dict[i][j]['dish'] + ' '
            print(print_str)
        return ordered_dict

    # 查询餐厅列表
    def show_restaurants(self, tabUniqueId, targetTime):
        '''
            tabUniqueId: 点餐段唯一值，show_ordered()里返回
            targetTime: 点餐段时间值，show_ordered()里返回
        '''
        restaurants_url = 'preorder/api/v2.1/restaurants/list'
        ext_params = {
            'tabUniqueId': tabUniqueId,
            'targetTime': targetTime,
        }
        response = self.get(self.build_url(restaurants_url, ext_params))
        restaurant_dict = {}
        if not response.json()['restaurantList']:
            logging.info('{}时间段餐厅列表为空'.format(targetTime))
        for i in response.json()['restaurantList']:
            restaurant_dict[i['name']] = i['uniqueId']
        print(restaurant_dict)
    # show_restaurants('67f3bce3-3758-4b88-834e-7dfdee5cbde5', '2020-12-19 15:30')

    # 查询餐厅菜牌
    def show_dishes(self, tabUniqueId, targetTime, rest_id):
        '''
            tabUniqueId: 点餐段唯一值，show_ordered()里返回
            targetTime: 点餐段时间值，show_ordered()里返回
            rest_id: 餐厅唯一标识，show_restaurants()里返回
        '''
        part_url = 'preorder/api/v2.1/restaurants/show'
        ext_params = {
            'tabUniqueId': tabUniqueId,
            'targetTime': targetTime.replace(' ', '+'),    # 时间多了个+
            'restaurantUniqueId': rest_id,
        }
        response = self.get(self.build_url(part_url, ext_params))
        dish_dict = {}
        n = 0
        for i in response.json()['dishList']:
            if i['isSection']:
                continue
            dish_dict[str(n)] = {'id': i['id'], 'name': i['name'], 'price': i['originalPriceInCent']/100}
            n += 1
        print(dish_dict)
    # show_dishes('67f3bce3-3758-4b88-834e-7dfdee5cbde5', '2020-12-19 15:30', '30a1c2')

    # 获取地址
    def get_address(self, namespace):
        '''
            namespace: 点餐段标识，show_ordered()里返回
        '''
        part_url = 'preorder/api/v2.1/corps/show'
        ext_params = {
            'namespace': namespace
        }
        response = self.get(self.build_url(part_url, ext_params))
        print(response.json()['addressList'])
    # get_address('452451')

    # 提交订单
    def add_order(self, tabUniqueId, AddressUniqueId, targetTime):
        '''
            tabUniqueId: 点餐段唯一值，show_ordered()里返回
            AddressUniqueId: 地址唯一值，get_address()里返回
            targetTime: 点餐段时间值，show_ordered()里返回
        '''
        part_url = 'preorder/api/v2.1/orders/add'
        headers = {
            'cookie': self.cookie,
            'Context-Type': 'application/x-www-form-urlencoded'
        }
        arg_dict = {
            'corpAddressRemark': '',
            'corpAddressUniqueId': AddressUniqueId,
            'order': '[{"count":1,"dishId":159542297}]',
            'remarks': '[{"dishId":"159542297","remark":""}]',
            'tabUniqueId': tabUniqueId,
            'targetTime': targetTime,
            'userAddressUniqueId': AddressUniqueId
        }
        response = self.post(self.build_url(part_url, {}), arg_dict, headers=headers)
        print(response.json())


