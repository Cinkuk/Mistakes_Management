import os
import sys

import GlobalData, DataManagement, Exporter, LogManagement
import question_manager_app

# initial data
def initial_data():
    # initial global variable
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    GlobalData.PROJECT_ROOT_PATH = project_root
    GlobalData.DATA_ROOT_PATH = project_root
    # initial folder
    dataManage = DataManagement.DiskController()
    # initial metadata and questions' data
    dataManage.read_metadatas()
    #dataManage.read_questions()

if __name__ == '__main__':
    log = LogManagement.Log('main')
    log.write('INFO', 'launch APP')
    initial_data()
    #print(GlobalData.BIND)
    question_manager_app.main()
