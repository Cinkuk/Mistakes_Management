# Global Data
# store of metadata, questions and struct

# metadata
SUBJECTS = []
SOURCES = []
QUESTION_TYPES = []
BIND = dict()
KEYPOINTS = dict()
NEWEST_ID = 0

# questions
QUESTIONS = []

# struct
class question(object):
    def __init__(self, question_data):
        self.data = question_data

# constant
DATA_ROOT_PATH = ''
PROJECT_ROOT_PATH = ''

def get_root_path():
    return DATA_ROOT_PATH