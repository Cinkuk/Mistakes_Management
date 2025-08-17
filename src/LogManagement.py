# manage log file
# add program operations to log file
# add program exceptions and errors to log file
# receive messages from others components and write in log file

import os
import sys
import traceback
from time import localtime, strftime
def get_timestamp():
    return strftime("%Y-%m-%d %H:%M:%S", localtime()) 

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

ERROR_LOG = Log('GlobalException')
def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常捕获"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 允许 Ctrl+C 正常退出
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # 写入到日志文件
    ERROR_LOG.write('ERROR', f"未捕获异常:\n{error_message}")

    # 如果想同时在控制台显示，可以加上这一行
    print(f"程序发生未捕获异常，已写入日志文件:\n{error_message}")

sys.excepthook = handle_exception