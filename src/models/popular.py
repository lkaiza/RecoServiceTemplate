# from itertools import cycle, islice
import dill
import pandas as pd

from .base import BaseRecommender

class Popular(BaseRecommender):
    def __init__(self, config=None, max_k=10, days=30, item_column="item_id", dt_column="date"):
        self.config = config
        
        if self.config is None:
            self.max_k = max_k
            self.days = days
            self.item_column = item_column
            self.dt_column = dt_column
            self.recommendations = []
        
        else:
            self.__load_models()

    def fit(self, df):
        min_date = df[self.dt_column].max().normalize() - pd.DateOffset(
            days=self.days
        )
        self.recommendations = (
            df.loc[df[self.dt_column] > min_date, self.item_column]
            .value_counts()
            .head(self.max_k)
            .index.values
        )
        return self

    def recommend(self, n=10):
        return self.recommendations[:n]

    def __load_models(self):
        try:
            with open(self.config[f'popular']['model_path'], 'rb') as f:
                model = dill.load(f)
            
            self.max_k = model.max_k
            self.days = model.days
            self.item_column = model.item_column
            self.dt_column = model.dt_column
            self.recommendations = model.recommendations

        except FileNotFoundError:
            print('models folder is empty')

# class Popular(BaseRecommender):
#     def __init__(
#         self,
#         max_k=10,
#         days=30,
#         item_column="item_id",
#         dt_column="date",
#     ):
#         self.max_k = max_k
#         self.days = days
#         self.item_column = item_column
#         self.dt_column = dt_column
#         self.recommendations = []

#     def fit(self, df):
#         min_date = df[self.dt_column].max().normalize() - pd.DateOffset(
#             days=self.days
#         )
#         self.recommendations = (
#             df.loc[df[self.dt_column] > min_date, self.item_column]
#             .value_counts()
#             .head(self.max_k)
#             .index.values
#         )
#         return self

#     def recommend(self, n=10):
#         return self.recommendations[:n]