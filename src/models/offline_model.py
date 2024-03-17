import dill
import pandas as pd


class OfflineModel:
    def __init__(self, model_name, config):
        self.model_name = model_name
        self.config = config
        self.recos, self.users_mapping = None, None
        self.__load_models()

    def recommend(self, user_id, n_recs=10):
        return self.recos[user_id]

    def __load_models(self):
        try:
            with open(self.config[f'{self.model_name}']['model_path'], 'rb') as f:
                self.recos = dill.load(f)
            self.users_mapping = self.recos.keys()
        except FileNotFoundError:
            print('models folder is empty')