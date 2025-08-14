# Global Data
# store of metadata, questions and struct

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

def get_root_path():
    return DATA_ROOT_PATH