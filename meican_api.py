import requests
import datetime
import logging
import random
import time

logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
class Meican:
    def __init__(self, username, password, filter_dict) -> None:
        self.base_url = 'https://meican.com/'
        self.base_params = {
            'client_id': 'Xqr8w0Uk4ciodqfPwjhav5rdxTaYepD',    # 看着是美餐固定的client信息
            'client_secret': 'vD11O6xI9bG3kqYRu9OyPAHkRGxLh4E',
        }
        self.username = username
        self.password = password
        self.filter_dict = filter_dict
        if 6 == datetime.datetime.today().weekday():
            self.start_date = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            self.end_date = (datetime.datetime.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            self.start_date = datetime.datetime.today().strftime("%Y-%m-%d")
            sub_days = 6 - datetime.datetime.today().weekday()
            self.end_date = (datetime.datetime.today() + datetime.timedelta(days=sub_days)).strftime("%Y-%m-%d")
        if '' == self.filter_dict['start_date']: self.filter_dict['start_date'] = self.start_date
        if '' == self.filter_dict['end_date']: self.filter_dict['end_date'] = self.end_date


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
        time.sleep(self.filter_dict['delay_time'])
        if None == headers:headers = {'cookie': self.cookie}
        r = requests.post(url=url, headers=headers, data=data)
        if 200 == r.status_code:
            return r
        else:
            logging.critical('POST请求响应码异常，back:{}，url：{}，data：{}，header：{}'.format(r.text, url, data, headers))
            raise ValueError('POST请求响应码异常')

    def get(self, url, headers=None) -> object:
        time.sleep(self.filter_dict['delay_time'])
        if None == headers:headers = {'cookie': self.cookie}
        r = requests.get(url=url, headers=headers)
        if 200 == r.status_code:
            return r
        else:
            logging.critical('GET请求响应码异常，back:{}，url：{}，header：{}'.format(r.text, url, headers))
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
        return restaurant_dict
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
        dish_dict = []
        for i in response.json()['dishList']:
            if i['isSection']:
                continue
            if self.filter_dict['price_limt'] and i['originalPriceInCent']/100 > self.filter_dict['price']:
                continue
            dish_dict.append({'id': i['id'], 'name': i['name'], 'price': i['originalPriceInCent']/100})
        return dish_dict
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
        return response.json()['addressList']
    # get_address('452451')

    # 提交订单
    def add_order(self, tabUniqueId, AddressUniqueId, targetTime, dishId):
        '''
            tabUniqueId: 点餐段唯一值，show_ordered()里返回
            AddressUniqueId: 地址唯一值，get_address()里返回
            targetTime: 点餐段时间值，show_ordered()里返回
            dishId: 菜品id，show_dishes()里返回
        '''
        part_url = 'preorder/api/v2.1/orders/add'
        headers = {
            'cookie': self.cookie,
            'Context-Type': 'application/x-www-form-urlencoded'
        }
        arg_dict = {
            'corpAddressRemark': '',
            'corpAddressUniqueId': AddressUniqueId,
            'order': '[{{"count":1,"dishId":{}}}]'.format(str(dishId)),
            'remarks': '[{{"dishId":"{0}","remark":""}}]'.format(str(dishId)),
            'tabUniqueId': tabUniqueId,
            'targetTime': targetTime,
            'userAddressUniqueId': AddressUniqueId
        }
        response = self.post(self.build_url(part_url, {}), arg_dict, headers=headers)
        logging.info(response.json())
        return

    # 批量下单
    def radom_add(self):
        self.set_cookie()
        all_address = []
        ordered_dict = self.show_ordered(self.filter_dict['start_date'], self.filter_dict['end_date'])
        for date, date_items in ordered_dict.items():
            # 过滤掉非工作日
            if datetime.datetime.strptime(date, "%Y-%m-%d").weekday() in self.filter_dict['work_days']:
                for time_part, dish_part in date_items.items():
                    # 过滤掉已点餐日期
                    if 'None' != dish_part['dish']:
                        continue
                    restaurants = self.show_restaurants(dish_part['tabUniqueId'], dish_part['target_time'])
                    all_dish = []
                    for restaurant, rest_id in restaurants.items():
                        all_dish += self.show_dishes(dish_part['tabUniqueId'], dish_part['target_time'], rest_id)
                    address_list = self.get_address(dish_part['namespace'])
                    address_dict = {}
                    for address_item in address_list:
                        all_address.append(address_item['address'])
                        address_dict[address_item['address']] = address_item['uniqueId']
                    
                    final_addressId = ''
                    for address in address_dict.keys():
                        if address == self.filter_dict['address']:
                            final_addressId = address_dict[address]
                    # TODO: 默认地址匹配不上时，给用户选择
                    selected = random.sample(all_dish, 1)
                    logging.info('{}-{}-{}'.format(date, time_part, selected[0]['name']))
                    self.add_order(dish_part['tabUniqueId'], final_addressId, dish_part['target_time'], selected[0]['id'])
        

