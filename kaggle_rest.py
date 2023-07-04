import subprocess
import sys

# Устанавливаем библиотеки, если они не установлены
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install("requests")

install("pandas")

install("numpy")

install("kaggle")

import requests
from zipfile import ZipFile
import io
import pandas as pd
import numpy as np
import kaggle

kaggle.api.authenticate()

# Скачиваем и разархивируем файл
kaggle.api.dataset_download_files('himanshupoddar/zomato-bangalore-restaurants', path='./', unzip=True)

df = pd.read_csv('zomato.csv')

# Делаем копию датасета
data = df.copy()

# Фильтруем лишние столбцы
column_to_drop = ['online_order', 'book_table', 'reviews_list', 'menu_item', 'listed_in(type)', 'listed_in(city)', 'url', 'phone']
data.drop(columns=column_to_drop, axis=1,inplace=True)

# удаляем дубли в address
data.drop_duplicates(subset='address', inplace = True)

# меняем название
data.rename(columns={'approx_cost(for two people)': 'avg_cost_2'}, inplace=True)

# обрабатываем пропуски
data['rate'] = data['rate'].replace('NEW',np.NaN)
data['rate'] = data['rate'].replace('-',np.NaN)

data.dropna(subset=['rate', 'votes'], inplace = True)

# приводим рейтинг к норм виду
data['rate'] = data.loc[:,'rate'].replace('[ ]','',regex = True)
data['rate'] = data['rate'].astype(str)
data['rate'] = data['rate'].apply(lambda r: r.replace('/5',''))
data['rate'] = data['rate'].apply(lambda r: float(r))

# топ 75
top_75 = data[['name', 'address', 'rate', 'votes']]
top_75 = top_75.sort_values(by=['rate', 'votes'], ascending = False)
top_75 = top_75.head(75)
top_75.to_excel('top_75.xlsx', index=False)

# топ блюд
df_dishes = data.dropna(subset='dish_liked')

# Создание словаря для хранения блюд и их популярности
dishes = {}

# Подсчет популярности блюд
for index, row in df_dishes.iterrows():
    dish_list = row['dish_liked'].split(',')
    for dish in dish_list:
        dish = dish.strip()
        if dish in dishes:
            dishes[dish] += 1
        else:
            dishes[dish] = 1

# Сортировка словаря по убыванию значений
sorted_dishes = sorted(dishes.items(), key=lambda x: x[1], reverse=True)

# Выбор топ 5% блюд
top_5_percent = int(len(sorted_dishes) * 0.05)
top_dishes = sorted_dishes[:top_5_percent]

# Создание датафрейма с топ 5% блюдами и их популярностью
top_dishes_df = pd.DataFrame(top_dishes, columns=['Dish', 'Popularity'])

top_dishes_df.to_excel('top_dishes.xlsx', index=False)

# 10 рандомных ресторанов
random_rest = data.dropna(subset='avg_cost_2')

random_rest['avg_cost_2'] = random_rest['avg_cost_2'].str.replace(',','')
random_rest['avg_cost_2'] = random_rest['avg_cost_2'].astype(int)

# столбец с чеком на одного посетителя
random_rest['avg_cost'] = random_rest['avg_cost_2']/2
random_rest['avg_cost'] = random_rest['avg_cost'].astype(int)

# 10 рандомных ресторанов
random_rest = random_rest.query('avg_cost > 0')

# API-ключ Open Exchange Rates
api_key = '62fafc8af18a4ff99dbee8e54434bd9d'

# Функция для получения актуального курса обмена валюты
def get_exchange_rate(base_currency, target_currency):
    url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}"
    response = requests.get(url)
    df_exchange = response.json()
    rates = df_exchange['rates']
    base_rate = rates[base_currency]
    target_rate = rates[target_currency]
    exchange_rate = target_rate / base_rate
    return exchange_rate

# Конвертация валюты в евро
def convert_to_euro(price, exchange_rate):
    return price * exchange_rate

# Конвертация валюты в доллары
def convert_to_dollar(price, exchange_rate):
    return price * exchange_rate

# Установка базовой валюты
base_currency = 'INR'

# Получение актуального курса обмена INR к EUR и USD
exchange_rate_eur = get_exchange_rate(base_currency, 'EUR')
exchange_rate_usd = get_exchange_rate(base_currency, 'USD')

# Создание новых столбцов с конвертированными значениями
random_rest['price_eur'] = round(random_rest['avg_cost'].apply(lambda x: convert_to_euro(x, exchange_rate_eur)), 2)
random_rest['price_usd'] = round(random_rest['avg_cost'].apply(lambda x: convert_to_dollar(x, exchange_rate_usd)), 2)

random_rest = random_rest[['name', 'rate', 'avg_cost', 'price_eur', 'price_usd']]
random_rest = random_rest.sample(10)

random_rest.to_excel('random_rest.xlsx', index=False)