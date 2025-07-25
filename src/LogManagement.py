# manage log file
# add program operations to log file
# add program exceptions and errors to log file
# receive messages from others components and write in log file

import os
from time import localtime, strftime
def get_timestamp():
    return strftime("%Y-%m-%d %H:%M:%S", localtime()) 

import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
lib_path = os.path.join(project_root, 'Lib')
sys.path.append(lib_path)
import GlobalData

class LogFile(object):
    def __init__(self):
        self.log_filename = os.path.join(GlobalData.DATA_ROOT_PATH, 'log.txt')

    def write(self, role, type, content):
        # role: who execute the operation
        # type: INFO, WARNING, ERROR
        # content: timestamp, detailed operation
        format = '{} role: {} [{}]: {}\n'
        write_content = format.format(get_timestamp(),
                                      role,
                                      type,
                                      content)
        with open(self.log_filename, 'a', encoding='utf-8') as file:
            file.write(write_content)


class Log(object):
    def __init__(self, subscriber: str):
        self.subscriber = subscriber
        self.writer = LogFile()
    
    def write(self, type, content):
        self.writer.write(self.subscriber, type, content)
