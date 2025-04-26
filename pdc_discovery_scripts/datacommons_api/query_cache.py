'''
A cache for query results.
'''

import os
import pickle

from typing import Type
from typing import TypeVar
from typing import Generic

from pydantic import BaseModel


T = TypeVar('T', bound=BaseModel)

_CACHE_LOCATION = os.path.expanduser('~/.cache/datacommons_api')
os.makedirs(_CACHE_LOCATION, exist_ok=True)


def _path(key: str) -> str:
    return os.path.join(_CACHE_LOCATION, f'{key}.pickle')


class QueryCache(Generic[T]):
    '''
    A cache for query results.
    '''
    key: str
    model: Type[T]
    data: T | None

    def __init__(self, key: str, model: Type[T]):
        self.key = key
        self.model = model
        self.data = None

    def __enter__(self):
        if self.exists:
            with open(_path(self.key), 'rb') as f:
                self.data = pickle.load(f)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @property
    def exists(self) -> bool:
        '''
        Check if the cache exists.
        '''
        return os.path.isfile(_path(self.key))

    def update(self, data: T):
        '''
        Update the cache with the given data.
        '''
        self.data = data

        with open(_path(self.key), 'wb') as f:
            pickle.dump(data, f)

    @staticmethod
    def clear_all():
        '''
        Clear all cache files.
        '''
        for filename in os.listdir(_CACHE_LOCATION):
            os.remove(os.path.join(_CACHE_LOCATION, filename))
