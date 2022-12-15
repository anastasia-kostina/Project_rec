import pandas as pd
import numpy as np


def prefilter_items(data, item_features, take_n_popular=5000):
    # Уберем самые популярные товары (их и так купят)
    popularity = data.groupby('item_id')['user_id'].nunique().reset_index() / data['user_id'].nunique()
    popularity.rename(columns={'user_id': 'share_unique_users'}, inplace=True)

    top_popular = popularity[popularity['share_unique_users'] > 0.5].item_id.tolist()
    data = data[~data['item_id'].isin(top_popular)]

    # Уберем самые НЕ популярные товары (их и так НЕ купят)
    top_notpopular = popularity[popularity['share_unique_users'] < 0.01].item_id.tolist()
    data = data[~data['item_id'].isin(top_notpopular)]

    # Уберем товары, которые не продавались за последние 12 месяцев
    data = data[~((data['quantity'] == 0) & (data['week_no'] <= 12 * 4))]

    # Уберем не интересные для рекомендаций категории (department)
    item_features_department = pd.DataFrame(item_features.groupby('department')['item_id']. \
                                            nunique().sort_values(ascending=False).reset_index())

    item_features_department_top = item_features_department[
        item_features_department['item_id'] > 50].department.tolist()

    item_features_notpopular = item_features[
        ~item_features['department'].isin(item_features_department_top)].item_id.unique().tolist()

    data = data[~data['item_id'].isin(item_features_notpopular)]

    # Уберем слишком дешевые товары (на них не заработаем). 1 покупка из рассылок стоит 60 руб.
    data['price'] = data['sales_value'] / (np.maximum(data['quantity'], 1))
    data = data[data['price'] > data['price'].quantile(0.20)]

    # Уберем слишком дорогие товары
    data = data[data['price'] < data['price'].quantile(0.99995)]

    # Возьмем топ-5000
    popularity_top = data.groupby('item_id')['quantity'].sum().reset_index()
    popularity_top.rename(columns={'quantity': 'n_sold'}, inplace=True)
    top_n = popularity_top.sort_values('n_sold', ascending=False).head(take_n_popular).item_id.tolist()
    # Заведем фиктивный item_id (если юзер покупал товары из топ-5000, то он "купил" такой товар)
    # data.loc[~data['item_id'].isin(top_n), 'item_id'] = 999999
    data = data[data['item_id'].isin(top_n)]
    return data
