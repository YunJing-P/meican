from meican_api import Meican
username = ''
password = ''
meican = Meican(username, password)
meican.set_cookie()
print(meican.show_ordered('2020-12-18', '2020-12-21'))
meican.show_restaurants('41f3fc49-df6f-456a-84ac-007eec743cab', '2020-12-21 08:30')
# meican.show_dishes('67f3bce3-3758-4b88-834e-7dfdee5cbde5', '2020-12-19 15:30', 'a1f080')
# meican.get_address('423493')