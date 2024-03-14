import dill
import pandas as pd
import numpy as np
from itertools import chain


class kNN:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.users_mapping, self.users_inv_mapping = None, None
        self.__load_models()
        self.train = self.__load_train_data()
        self.mapper = self.__generate_implicit_recs_mapper(
            N=self.config['knn']['n_users'],
        )

    def recommend(self, user_ids, n_recs=10):
        recs = pd.DataFrame({
            'user_id': user_ids
        })
        recs['similar_user_id'], recs['similarity'] = zip(
            *recs['user_id'].map(self.mapper)
        )
        recs = recs.set_index('user_id').apply(pd.Series.explode).reset_index()
        recs = recs[recs['user_id'] != recs['similar_user_id']]
        recs = self.__join_watched(recs)
        return recs[:min(n_recs, len(recs))]

    def __generate_implicit_recs_mapper(self, N):
        def _recs_mapper(user):
            user_id = self.users_mapping[user]
            recs = self.model.similar_items(user_id, N=N)
            if recs == tuple():
                return ([], [])
            return (
                [self.users_inv_mapping[user] for user in recs[0]],
                [sim for sim in recs[1]],
            )

        return _recs_mapper

    def __join_watched(self, recs_df):
        similar_users_items = [
            self.train[key] for key in recs_df['similar_user_id'].values if not np.isnan(key) 
        ]
        return np.unique(list(chain.from_iterable(similar_users_items))).tolist()

    def __load_models(self):
        try:
            with open(self.config['knn']['model_path'], 'rb') as f:
                self.model = dill.load(f)

            with open(
                self.config['knn']['users_mapping_path'],
                'rb',
            ) as f:
                self.users_mapping = dill.load(f)

            with open(
                self.config['knn']['users_inv_mapping_path'],
                'rb',
            ) as f:
                self.users_inv_mapping = dill.load(f)
        except FileNotFoundError:
            print('models folder is empty')

    def __load_train_data(self):
        user_item_dict = None
    # try:
        interactions = pd.read_csv(
            self.config['data']['interactions_path'])
        interactions.drop(
            [
                'last_watch_dt',
                'total_dur',
            ],
            inplace=True,
            axis=1,
        )

        interactions['rank'] = interactions.groupby(
            'user_id').cumcount() + 1
        interactions = interactions[interactions['rank'] < 11]
        user_item_dict = interactions.groupby('user_id')[
            'item_id'
        ].apply(list).to_dict()
        # except FileNotFoundError:
        #     print('data folder is empty')
        return user_item_dict