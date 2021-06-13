import requests
import sqlite3
import json
import os
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def countData(con, objName):
    cursor = con.cursor()
    cursor.execute(f'select count(*) from {objName}')
    result = cursor.fetchone()
    print(f'{result[0]} rows\n')


def showData(con, objName):
    cursor = con.cursor()
    print(bcolors.OKBLUE + '-_'*20 + '\n' + objName + '\n' + '-_'*20 + '\n'
            + bcolors.ENDC)
    cursor.execute(f'select * from {objName}')
    title = [i[0] for i in cursor.description]
    print(title)
    for row in cursor.fetchall()[0:3]:
    # for row in cursor.fetchall():
        print(row[0:100])
    countData(con, objName)


def db_init(con):
    cursor = con.cursor()
    cursor.execute('drop table if exists DWH_DIM_EVENTS_HIST')
    cursor.execute('''
        create table if not exists DWH_DIM_EVENTS_HIST(
            id integer primary key,
            name varchar(128),
            short_description varchar(1024),
            description varchar(1024),
            is_free bool,
            price number,
            start_dt date,
            end_dt date,
            image_name varchar(256),
            category_name varchar(128),
            category_sysname varchar(128),
            organization_name varchar(128),
            address_street varchar(128)
        );
    ''')
    cursor.execute('''
        create table if not exists DWH_FACT_CATEGORIES(
            sysname varchar(128),
            name varchar(128)
        );
    ''')
    con.commit()


def load2db(con, arr_dict):
    cursor = con.cursor()
    # print(json.dumps(arr_dict[0], sort_keys=False, indent=2, ensure_ascii=False))
    cursor.executemany('''
        insert into DWH_DIM_EVENTS_HIST (
            id, name, short_description, description, is_free, price, start_dt,
            end_dt, image_name, category_name, category_sysname,
            organization_name, address_street
        ) values (
            :id, :name, :short_description, :description, :is_free, :price, :start_dt,
            :end_dt, :image_name, :category_name, :category_sysname,
            :organization_name, :address_street
        );
    ''', arr_dict)
    cursor.execute('''
        insert into DWH_FACT_CATEGORIES (
            sysname,
            name
        ) select distinct category_sysname,category_name
        from DWH_DIM_EVENTS_HIST;
    ''')
    con.commit()


def download_image(url, filename):
    filename = './app/static/images/' + filename
    if not os.path.isfile(filename):
        response = requests.get(url)
        # sleep(randrange(5) + 1)
        if response.status_code == 200:
            content = response.content
        else:
            return False
        with open(filename, mode='wb') as localfile:
            localfile.write(content)
        localfile.close()
    return True


def get_data(con):
    headers = {'X-API-KEY':
            '746318251363e687cf159b3b87bc1cb33e33d35b03433a36abc5d08032144c7a'}
    date_from = datetime.now().strftime('%Y-%m-%d')
    date_to = (datetime.now() + relativedelta(months=+1)).strftime('%Y-%m-%d')
    ft = '''{"data.general.start": {"$gt":"{date_from}"},
    "data.general.end": {"$lt":"{date_to}"},
    "data.general.places[].locale.name":{"$eq":"Казань"}
    }'''.replace('{date_from}', date_from).replace('{date_to}', date_to)
    payload = {'f': ft, 'o': 'data.general.start', 'l': 10}
    r = requests.get('https://opendata.mkrf.ru/v2/events/$', params=payload,
            headers=headers)
    r_dict = r.json()
    # print(json.dumps(r.json(), indent=4, ensure_ascii=False))
    if len(r_dict['data']) != 0:
        np = r_dict.get('nextPage')
        arr_dict = []
        i = 0
        # while (np and i < 1):
        while (np):
            # print('_'*30 + ' page ' + '_'*30)
            # print(r_dict['nextPage'])
            print(r_dict['total'])
            for it in r_dict['data']:
                # print('_'*30 + ' event ' + '_'*30)
                # print(json.dumps(it, sort_keys=False, indent=4, ensure_ascii=False))
                d = {}
                d['id'] = it['nativeId']
                d['name'] = it['data']['general']['name']
                d['short_description'] = it['data']['general']['shortDescription']
                d['description'] = it['data']['general']['description']
                d['is_free'] = it['data']['general']['isFree']
                if "price" in it['data']['general']:
                    d['price'] = it['data']['general']['price']
                else:
                    d['price'] = 0
                d['start_dt'] = it['data']['general']['start']
                d['end_dt'] = it['data']['general']['end']
                d['image_name'] = it['data']['general']['image']['title']
                download_image(it['data']['general']['image']['url'], d['image_name'])
                d['category_name'] = it['data']['general']['category']['name']
                d['category_sysname'] = it['data']['general']['category']['sysName']
                d['organization_name'] = it['data']['general']['organization']['name']
                d['address_street'] = it['data']['general']['places'][0]['address']['street']
                arr_dict.append(d)
            r = requests.get(np, headers=headers)
            r_dict = r.json()
            np = r_dict.get('nextPage')
            i += 1
        load2db(con, arr_dict)
    # print(r)


if __name__ == "__main__":
    con = sqlite3.connect('app.db')
    db_init(con)
    get_data(con)
    showData(con, 'DWH_FACT_CATEGORIES')
    # showData(con, 'DWH_DIM_EVENTS_HIST')
