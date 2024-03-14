import numpy as np
import yaml


def read_config(config_path: str) -> dict:
    with open(config_path, "r") as file:
        cfg = yaml.load(file, Loader=yaml.SafeLoader)
        return cfg


def get_unique(data: list):
    data = np.array(data)
    _, idx = np.unique(data, return_index=True)
    return data[np.sort(idx)]
