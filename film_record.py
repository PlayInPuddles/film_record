# ---------------------- 导入需要的模块 ---------------------- #

import requests, json, datetime, re
from bs4 import BeautifulSoup
import pandas as pd


# ----------------------- 全局性的设置 ----------------------- #

# 头部信息
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
headers = {
    'User-Agent': user_agent
}

# time_out = 25
# proxy = "113.116.50.182:808"
# proxies = {
#     "http": proxy,
#     "https": proxy,
# }

# 建立一个session
session = requests.session()

today = datetime.date.today().strftime('%Y%m%d')

# ---------- 获取公示列表及公示时间(film_record_list) ---------- #

# 输入起始日期，输出起始日期之间发布的公示详情页url和公示的发布日期
# 日期格式为string，形式如"20200108"
# 默认获取2019年1月1日至今的所有数据
def get_film_record_list(start_date='20190101', end_date=today):

    # 电影项目备案公示列表页目前只有2页，暂时先放进一个list
    # 以后等页数多了，方便寻找翻页规律后再行更新
    urls = ['http://www.chinafilm.gov.cn/chinafilm/channels/167.shtml',
            'http://www.chinafilm.gov.cn/chinafilm/channels/167_2.shtml']
    # 建立一个空DataFrame，用来存放结果数据
    detail_pages_df = pd.DataFrame(columns=('detail_page_url', 'ann_date'))

    for url in urls:
        res = session.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        detail_pages = soup.find('ul',class_='m2ru1 m2ru11').find_all('li')

        for i in range(len(detail_pages)):
            detail_page_url = 'http://www.chinafilm.gov.cn' + detail_pages[i].find('a',class_='m2r_a')['href']
            # 获取公示发布时间并转化为"20191231"形式
            ann_date = detail_pages[i].find_all('span')[1].text
            ann_date = "".join(ann_date.split("-"))
            # 把数据存入DataFrame
            detail_pages_df = detail_pages_df.append({'detail_page_url':detail_page_url, 
                                                      'ann_date':ann_date}, 
                                                      ignore_index=True)

    return detail_pages_df.loc[(detail_pages_df['ann_date'] > start_date) & \
                               (detail_pages_df['ann_date'] < end_date)]

# Test
# print(get_film_record_list())


# ---------- 获取每次公示的电影列表(film_record_detail) ---------- #

# 输入起始日期，
# 输出对应的影片详情页url、公示的发布日期、公示时间区间
def get_film_record_detail(start_date='20190101', end_date=today):
    # 建立一个空DataFrame，用来存放结果数据
    film_detail_df = pd.DataFrame(columns=['url', 'date_range', 'ann_date'])

    detail_pages_df = get_film_record_list(start_date, end_date)
    # 拿到上一环节得到的列表，开始遍历
    for i in range(len(detail_pages_df)):
        res = session.get(detail_pages_df.loc[i][0],headers=headers)
        res.encoding = 'UTF-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        # 获取公示时间区间
        date_range = soup.find('div', id='body').find_all('p')[2].text[:18]
        # 获取公示发布时间
        ann_date = detail_pages_df.loc[i][1]

        # 获取每次公示的所有影片列表
        tables = soup.find_all('div',class_='hmc4Table')
        # 获取每种影片类型下的影片列表
        for table in tables:
            urls = table.find_all('a',class_='kk')
            for url in urls:
                url = 'http://www.chinafilm.gov.cn' + url['href']
                film_detail_df = film_detail_df.append({'url': url, 
                                                        'date_range': date_range,
                                                        'ann_date': ann_date}, 
                                                        ignore_index=True)

    return film_detail_df
                

# Test
# print(get_film_record_detail(start_date='20200101'))
# Test to_csv
# film_detail_df = get_film_record_detail(start_date='20200101')
# film_detail_df.to_csv('test.csv',index = False)

# ------------ 获取每部公示电影的具体信息(film_info) ------------ #

# 输入起始日期，
# 输出对应的影片的:
# rec_no        备案立项号
# film_name     影片名称
# rec_org       备案单位
# script_writer 编剧
# rec_result    备案结果
# rec_area      备案地
# classified    影片分类
# date_range    公示期间
# ann_date      公示发布时间
# outline       梗概
def get_film_info(start_date='20190101', end_date=today):
    # 新建一个空df
    columns = ['rec_no', 'film_name', 'rec_org', 'script_writer', 'rec_result', 
               'rec_area', 'classified', 'date_range', 'ann_date', 'outline']
    film_info_df = pd.DataFrame(columns=columns)

    # 获取上一环节得到的列表，开始遍历
    film_detail_df = get_film_record_detail(start_date, end_date)
    for i in range(len(film_detail_df)):
        url = film_detail_df.loc[i][0]
        date_range = film_detail_df.loc[i][1]
        ann_date = film_detail_df.loc[i][2]

        # 获取当前时间戳
        time_stamp = datetime.datetime.now().timestamp()
        time_stamp_13 = ''.join(str(time_stamp).split('.'))[:13]
        # 获取ID
        ID = re.search(r'\d+', url).group()
        # 生成参数
        params = {'ID': ID,
                  '': '',
                  time_stamp_13: ''}

        payload = {"value":"Dry7AkKkNA5znUnNjBtm2UwoT5vm0504UJFr14eOz5MCWAoc1IUDT2L0LzXimjJcTm46XxjPOjLDtYxy0slash0Zrx1S5CsokSwW9B5oRHokJFHUNQbGhM0add00slash0P0thBSvio0slash0W7pxlMIqGbYRSalMj0slash0ixM0add0sufwNu3Xj0slash0EKqjzmzBKo9Vm90qU5ehmDEBxO0add0tuApg2JcYK0slash0NeYW3C0add0p6ipPtGM0add0zg30add07vq5wGGy1buFR5mKj5fsytbDL2KMMr2sH9JDrIWtJx0slash0CHTFNzRb4TTU0slash09Bj8e3zmuOwEYzR4YjiOWM2r68wQ1Pl4TY0slash0OEIjT1NpokCd40add09c0slash0h5HwV0KibW6wuzs1XV9oCSeoELOAjTHkDhPm3BYWXRQ8drAtvL0add0I8zsPI0slash08ZkbXAJqR0add0AD7yeYBGyOR9Ajvg2maeOVYeF1sxQvW0slash02LF7M0add0dLUu7BRuFj5pDUNUUeLZw5Ixm0slash0GnuQReKbA2O55PxS35shJnBJgtndcB3qoA0add0dLVrTPQIfwDRcILUibIDqa4ktyGUGbVoKlmJu9V2aj0slash0Hy4vNXy3DedK5FTqiZPgTiguzLXWjSdOZHB8DCJLVFcJJxpcoIiCwEQICY0add0WWAPbQILIQf6ltxwQifkAhBUmQwebMELMQOiaimyddTXIFjEEJNpsjLfeF0add0agnrra36jtE1dNI0add0JwveDHiOgBgY3PyRXqX4M70add0oS0slash03W0slash0B0add006bFtTh9MUMS9lfXgv1RpwOOC0slash0p9Dmijn0add04UxWIF2dnQ7Usko7uzFEBcX5W6o0slash09QG3d80add0cruxdeEzBHIUNubgy4Oc5aF0ZBS7SmKTgoCxZYcmgxnYkBg1o0slash06mPeOUEtfmR2DqMcfQcO9y0nuVz9z40slash0QorfVbqGrkFPvV90slash0fTT0Q2vku0xoly1HQsro9yXZ7DlPpkB0bRoDqISaOV5eccqofAf0slash0KCVgHFEzeKleaVCRIfh1wC5UPJUzOtoNjp2AzLZKVoBAh5PTqviFYLOFxKtAMPAvH3cez20ivUXhypAgVLJBUnIPuF5MAEirMsYC6svL4QuZ0add0qEEyfZ6ds7rIoKYHZyuRpmikn9DIw96dPsZyT4ZRwTwxN1KtRjMkO1v90add0MCHfKJxB8JXvwmhMnZP6cwXANYabiZZpiZpuR4wdRQGHq7VjFf0V0qDErSbEqa21CrKPH08n6AMRcU9rLioVXCbH0FcgZh7yqJRfDUTMyPKxGpCpOmQnMwMNASx6U5cbLtjoPRrqG1CZH8Lbbi0add0tj3o4wsQ79XUG7XHuCDBB4a4YLYAe0slash0cuE7dnS0PpYyrFp0slash03nDwzm0CHK0dch1S5YU3tD7yzMGccFGAy7rtbryzgHa6c40mYArv1Pwne5MaDsxUafY0gXKvrDREnBYCAGDWnuo0slash0UKPyQzCie0wL0add09qRs4rH20slash0bA8V6eAtiWuNg5UTC5F3DNrMGwoz1KjPUtuFT1dyFi4ClahlTVujkPvaJAbbhA0slash0W0naoHbZh3RJAPhfs42HVz2L9UPJbBdmOF4UvTY10add0bIhKUPonpJzAhgfooTK9Cz7G9a58Hq1I0slash0FC6na20slash00slash0mYHd6E4xk100slash0YZFyEQmhtsFybr0eKW6GveuMJ3Iq1JLWYh6hXrU5EcIZmwTo0slash00UNDo0slash0iVbrxMa8T6mDOsW9ryYn0add0nLFQr8n9slb5CY0slash0lgnTRSIbmwIrpXgX0slash0kqT66lPDuxSKhxHtobVPUAXLWXIynmzWuhjnNL0add0TlsLM2qZJhiR7MEhHhXplm5nwSd4fLIXWzMlgXkDXKVSnX91z7FgSzuf0add0Ezbj3Tt4Fjk0add0EosjODfcS6anzLNWIfAX6XbltShWOgY6kix9PMrBwU6S3sP8db9PjWMRHpXR8Wj7yaMoloFtOfHqnDvsGgxqXzjzeH1YG0LeI0qmHP0add0DkOQFAcc4sO8gXfIEYtCxYnDakCAJ2wFKDDYksbGPJue0slash0W6EefKKyww69WSA4bxR8ZwC22kuIP3IMzA5oCjvWif1jgqIf7dMGRVEoJnm0JPO3zHAbZ7wLPzGmSedzGPNad9c2rKNYtrpCvNGEzpWUHv0slash0IdJeD0slash0KE3ymFf60BwWpKrB82vK0f9OdNbKandv1mOYpAgEhnZ6nqORFsQG6qkbS8lQfbX7zlEEgzZpRkJksdu0slash0aW0dFKDxxxWgAsREoAMhB1iTEC0slash0CP9ug1mWFEAbpGB0add0PLeOvqY0add04OmjvlbTyMB8bGy7wMqoC1HO0HIaufTCMdyhFou0sAxx4Kwuagakw0add0JO3Cd7O0add0JM59WZyenofvWVfWHj0add0r70slash0iA1hXLB6GOak4brY8Ux1fZX0add0LXJFBp4cCnKzR2NJR2G0slash0b0slash0lZ5Pj1U0add0Xn0add0vAGqR8xnzuRRoLcICPowOJAmnY2X570add0KEDW0slash01kmjj0slash0Yzot7vLbVysJYSjl0Q9y0slash0Q4LSZZnPgOsBq99QVClg0GPVRPW0slash0SZsrwHRF5msEnSk69iEdyuvU9zSBf0slash02Huk6LSjNa70RWsHiqLvH2NfX24dE0xlY42l9mbYdS5gNsCOXai3JYd9J6geA0add0w7xKsqesvbxsNwSOAJ80HT1MA9lOdtl4b37af9ZBlgF8xkzr6SJK1K5LgIRE16EIuhbQvPrQ3dVI7VX9C41DXbvLVmr5QNhkXCiaHopovXV9i0add0YM0slash0y4ZM7yNCD86rbxXxZ4FvHoUH1iOmt6HueKOSqGo4JYjsoru0add00slash00add098z6oRPzjUSNFFJcGwGzAKWMIHfDfOugjEji72oxrQv3JrRXH6aYe0bV7tNTyGW9jnpgZeQgF5UycxiLKDOQs9ucym7Xy54hctO0add0kOk0add0td2ssji8D14080add0abKMX7QS9F2d5p5BL7ZHaJsolo2UVndQ1orcQW87nayUdsiOR0uVfStpdgxVXCno5EbwvXFiOOT8Tn5gHqMBWY5o0slash0vLZHhfpuM6akBWUdzNuA0eWEeO0slash0YjOZ7EumGVSjLcnPyIVADHWjPurXtLCJXkPhmbLgxXahJxsLF68ceXGb0add06EyCAKwAOBMinu0rKgwlAR0x2NJdjsspBOJ3vmXMlXlzh0add01LSLslw0slash0f3yV0add00KaVPxF0slash02jZ1HekL2GERbR2R4JKj0hYJsqJ06v8QFdkPGY0add0W0hrQx50add0pdxYCL0add0jQRiiVZ4lMTvBYq7OkWfY1JhY0add0ExCe49R8MRzfj3IvGU4vG7TEmpqOOYJKb7ySW0add00rK6Uw1NfNSGvsV0Gz2AJ742BYQbt3rp00slash0A7jRobkxNISSoI1XeyZ70add0UDIBMEL45TeMbTS10slash0DothFdju16eGN0add0ZJjNTfesMwtU8hV2iQoDHn0slash0EvjEEsND7Oav5BPbz86WbgqLBsnCdSnbuJcvtH0vTiMlv1odLraKEREHlZ5ouATT3t57E20add05VyEAP6K0add0AKBjFItmRwbTT4dJW35ktOxam0leqobGKr2rZJaV4G0add0j9VcaM8S0add0BKu10slash0fXBjVNOhUirbLNA0add0RqTao5bgkINRNpppy4RtOhOBGBtSAMSvYE5X4tISUIQeCmDiG0slash0ntTkexCr75uQn2nCBGs9ydFCc0add0TwHltjmbl0add0RFntzSnyeK8imAo9WZEFtIf0h6HO1xrEoBrAXyHk0add01rpMiHHQcxwiyDXmsOrMNKJS8BLVYEVPE6vDXqvioVywWrG0hlCfN7R6BONeKJvJI8zpZQR7v5SE3ws0add00add0O0Hup1Gz3GIHqQd8mlpIA6TP4soWD7c4aaHeKjj12dT0slash0M4OLL6hZeCA3ZSvKUfBMlfFZhqA8qKvEinjWDxfBus061qX2MTgGMrHKNSAyjFeA1TqPFI576qIc9S0add0U4G77k10secret0",
                   "page":1}

        res = session.post('http://59.252.100.27/api/sys/stl/actions/dynamic?',
                           headers=headers, 
                           data=json.dumps(payload),
                           params=params, 
                           allow_redirects=True)
        soup = BeautifulSoup(json.loads(res.text)['html'],'html.parser')
        tds = soup.find_all('td')

        rec_no = tds[3].text
        film_name = tds[5].text
        rec_org = tds[7].text
        script_writer = tds[9].text
        rec_result = tds[11].text
        rec_area = tds[13].text
        classified = tds[1].text
        # date_range = # 公示期间
        # ann_date =  # 公告时间
        outline = tds[15].text[4:]

        film_info_df = film_info_df.append({'rec_no': rec_no, 
                                            'film_name': film_name, 
                                            'rec_org': rec_org, 
                                            'script_writer': script_writer, 
                                            'rec_result': rec_result, 
                                            'rec_area': rec_area, 
                                            'classified': classified, 
                                            'date_range': date_range, 
                                            'ann_date': ann_date, 
                                            'outline': outline}, 
                                            ignore_index=True)
    return film_info_df


# # Test
# result = get_film_info(start_date='20200101')
# print(result)
# result.to_csv('test.csv', index=False)

# ---------- 封装 ---------- #
