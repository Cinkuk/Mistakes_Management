# Global Data
# store of metadata, questions and struct

from sys import getsizeof

# metadata
SUBJECTS = []
SOURCES = []
QUESTION_TYPES = []
BIND = dict()
KEYPOINTS = dict()
NEWEST_ID = 0
KEYPOINTS_GROUP = dict() # dict[subject][group_name]

# questions
QUESTIONS = []

# constant
DATA_ROOT_PATH = ''
PROJECT_ROOT_PATH = ''

CACHE = dict() # path : QPixmap

class Cache():
    def __init__(self):
        global CACHE
        self.capacity = 400 * 1024 * 1024 # byte, 400MB
    
    def if_in(self, path):
        return path in CACHE
    
    def read(self, path):
        return CACHE[path]

    def add(self, path, qtimage):
        if getsizeof(CACHE) > self.capacity:
            for path in list(CACHE.keys())[:20]:
                del CACHE[path]
        CACHE[path] = qtimage

    def delete(self, path):
        if self.if_in(path):
            del CACHE[path]

def get_root_path():
    return DATA_ROOT_PATH