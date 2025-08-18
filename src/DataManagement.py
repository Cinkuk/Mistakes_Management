# manage data ranging from questions, subjects, sources, questions' types

import os
import sys
import json
import shutil
import zipfile
from datetime import datetime
from hashlib import md5
from PySide6.QtGui import QPixmap

import GlobalData, LogManagement

LOG = LogManagement.Log('DataManage')

def get_md5(content: str):
    return md5(content.encode('utf-8')).hexdigest()

class MetaDataController(object):
    def __init__(self):
        self.subjects = GlobalData.SUBJECTS
        self.sources = GlobalData.SOURCES
        self.question_types = GlobalData.QUESTION_TYPES
        self.keypoints = GlobalData.KEYPOINTS
        self.bind = GlobalData.BIND
        self.disk = DiskController()

        if 'subjects' not in self.bind.keys():
            self.bind['subjects'] = dict()
        if 'sources' not in self.bind.keys():
            self.bind['sources'] = dict()
        if 'keypoints' not in self.bind.keys():
            self.bind['keypoints'] = dict()
        GlobalData.BIND = self.bind
        #print('initial MetaData')
        #print(GlobalData.BIND)
    
    def get_metadata(self) -> tuple[list, list, list]:
        return (self.subjects, self.sources, self.question_types)
    
    def write(self):
        #print('write action')
        #print(self.subjects, self.sources, self.question_types, self.keypoints, self.bind)
        #print(GlobalData.BIND)
        GlobalData.SUBJECTS = self.subjects
        GlobalData.SOURCES = self.sources
        GlobalData.QUESTION_TYPES = self.question_types
        GlobalData.KEYPOINTS = self.keypoints
        GlobalData.BIND = self.bind

        self.disk.write_metadatas(self.subjects, self.sources, self.question_types, self.bind)

        #print(self.bind)
        #print(GlobalData.BIND)

    def if_in(self, target: str, content: str) -> bool:
        if target == 'subjects':
            return content in self.subjects
        elif target == 'sources':
            return content in self.sources
        elif target == 'question_types':
            return content in self.question_types
        else:
            raise ValueError('Invalid Target Value')
    
    def _add(self, target: list, subject: str) -> bool:
        if subject not in target:
            target.append(subject)
            self.write()
            #self.disk.read_metadatas()
            return True
        return False
    
    def _del(self, target: list, subject: str) -> bool:
        if subject not in target:
            return False
        target.remove(subject)
        self.write()
        #self.disk.read_metadatas()
        return True

    def add_subject(self, subject: str) -> bool:
        return self._add(self.subjects, subject)
    
    def del_subject(self, subject: str) -> bool:
        return self._del(self.subjects, subject)

    def add_source(self, source: str) -> bool:
        return self._add(self.sources, source)

    def del_source(self, source: str) -> bool:
        return self._del(self.sources, source)

    def add_question_types(self, type: str) -> bool:
        return self._add(self.question_types, type)

    def del_queation_types(self, type: str) -> bool:
        return self._del(self.question_types, type)
    
    def update_keypoints(self, keypoints_bind: dict) -> bool:
        self.bind['keypoints'] = keypoints_bind
        self.write()

    # type: 1) source(subject-source); 2) ID(source->ID)
    def add_bind(self, type: str, bind: list) -> bool:
        if type == 'source':
            subject = bind[0]
            source = bind[1]
            if subject not in self.bind['subjects'].keys():
                self.bind['subjects'][subject] = [source]
            if source not in self.bind['subjects'][subject]:
                self.bind['subjects'][subject].append(source)
            self.write()
            return True
        elif type == 'ID':
            subject = bind[0]
            source = bind[1]
            ID = bind[2]
            if subject not in self.bind['sources'].keys():
                self.bind['sources'][subject] = [source]
            if source not in self.bind['sources'][subject].keys():
                self.bind['sources'][subject][source] = [ID]
            if ID not in self.bind['sources'][subject][source]:
                self.bind['sources'][subject][source].append(ID)
                        
            self.write()
            return True
        else:
            return False

    def del_bind(self, type:str, bind: list) -> bool:
        if type == 'ID':
            subject = bind[0]
            source = bind[1]
            ID = bind[2]
            # delete metadata
            if subject != '全部':
                if source != '全部':
                    if ID in self.bind['sources'][subject][source]:
                        self.bind['sources'][subject][source].remove(ID)
                else:
                    for source in self.bind['sources'][subject].keys():
                        if ID in self.bind['sources'][subject][source]:
                            self.bind['sources'][subject][source].remove(ID)
                            break
            else:
                for subject in self.bind['sources'].keys():
                    for source in self.bind['sources'][subject].keys():
                        if ID in self.bind['sources'][subject][source]:
                            self.bind['sources'][subject][source].remove(ID)
                            break
            self.write()
            # delete question_data
            file = self.access_data_file()
            datas = json.load(file)
            if ID in datas.keys():
                datas.pop(ID)
                file.seek(0)
                json.dump(datas, file, indent=4)
                file.truncate()
            self.release_file(file)
            # delete index
            image_folder = self.disk.image_folder
            text_folder = self.disk.text_folder
            index = dict()
            image_name = ''
            with open(os.path.join(text_folder, 'index'), 'r+', encoding='utf-8') as file:
                index = json.load(file)
                image_name = index[ID]
                index.pop(ID)
                file.seek(0)
                json.dump(index, file, indent=4)
                file.truncate()
            # delete image
            image_name += '.png'
            os.remove(os.path.join(image_folder, image_name))
            


    def read_in(self):
        questions, subjects, sources, question_types, bind, keypoint_child = self.disk.read_metadatas()
        subject_child = bind['subject']
        sources_child = bind['sources']
        combine = (questions, subjects, sources, question_types, subject_child, sources_child, keypoint_child)
        return combine
    
    def newID(self):
        GlobalData.NEWEST_ID += 1
        return GlobalData.NEWEST_ID
    
    def access_data_file(self):
        return self.disk.access_data_file()
    
    def release_file(self, file):
        self.disk.release_file(file)


class DiskController(object):
    def __init__(self):
        self.root_path = GlobalData.DATA_ROOT_PATH
        self.image_folder = os.path.join(self.root_path, 'Images')
        self.text_folder = os.path.join(self.root_path, 'Text')
        self.index_file = os.path.join(self.root_path, 'index')

        # initial folder
        dirs = os.listdir(self.root_path)
        if 'Images' not in dirs:
            os.mkdir(self.image_folder)
        if 'Text' not in dirs:
            os.mkdir(self.text_folder)
        text_dirs = os.listdir(self.text_folder)
        if 'question_data' not in text_dirs:
            self.new_file('question_data', self.text_folder)
        if 'metadata' not in text_dirs:
            self.new_file('metadata', self.text_folder)
        if 'index' not in text_dirs:
            self.new_file('index', self.text_folder)
        if 'log.txt' not in dirs:
            self.new_file('log.txt', self.root_path)
    
    def new_file(self, file, folder):
        with open(folder+'/'+file, 'w', encoding='utf-8') as file:
            file.write('')
    
    def read_metadatas(self):
        metadata_file = os.path.join(self.text_folder, 'metadata')
        metadatas = dict()
        flag = False
        with open(metadata_file, 'r', encoding='utf-8') as file:
            if os.path.getsize(metadata_file) != 0:
                metadatas = json.load(file)
                flag = True
        if flag:
            subjects = metadatas['subjects']
            sources = metadatas['sources']
            question_types = metadatas['question_types']
            bind = metadatas['bind']
            newestID = metadatas['newestID']

            GlobalData.SUBJECTS =subjects
            GlobalData.SOURCES = sources
            GlobalData.QUESTION_TYPES = question_types
            GlobalData.BIND = bind
            GlobalData.NEWEST_ID = newestID
            LOG.write('INFO', '读入元数据成功')
        else:
            LOG.write('WARNING', '元数据文件为空')
            
    
    def write_metadatas(self, subjects, sources, question_types, bind):
        newestID = GlobalData.NEWEST_ID
        metadata = {
            'subjects': subjects,
            'sources': sources,
            'question_types': question_types,
            'bind': bind,
            'newestID': newestID
            }
        metadata_file = os.path.join(self.text_folder, 'metadata')
        with open(metadata_file, 'w', encoding='utf-8') as file:
            json.dump(metadata, file, indent=4)
        LOG.write('INFO', '写入元数据')
    
    def read_questions(self, ID):
        # return 
        # ID, subject, source, times, image_path, keypoints, note, answer, page, number
        metadatas = dict()
        indexs = dict()
        # read in text data
        dirs = os.listdir(self.text_folder)
        images = os.listdir(self.image_folder)
        if 'question_data' in dirs and 'index' in dirs:
            with open(os.path.join(self.text_folder, 'question_data'), 'r', encoding='utf-8') as file:
                metadatas = json.load(file)
            with open(os.path.join(self.text_folder, 'index'), 'r', encoding='utf-8') as file:
                indexs = json.load(file)
        else:
            return False
        if ID not in metadatas.keys() or ID not in indexs.keys():
            return False
        # extract target data
        data = metadatas[ID]
        image_index = indexs[ID] + '.png'
        image_path = os.path.join(self.image_folder, image_index)
        subject = data['subject']
        source = data['source']
        times = data['errortimes']
        keypoints = data['keypoint']
        page = data['page']
        number = ' '.join([data['mark'], data['number']])
        note = data['notice']
        answer = data['answer']

        return ID, subject, source, times, image_path, keypoints, note, answer, page, number
    
    def write_questions(self, qtimage, questiondata):
        ID = questiondata['ID']
        
        # save image
        image_path = os.path.join(self.image_folder, questiondata['index']+'.png')
        qtimage.save(image_path, 'PNG')
        # save other data
        json_file = os.path.join(self.text_folder, 'question_data')
        with open(json_file, 'r', encoding='utf-8') as file:
            if os.path.getsize(json_file) == 0:
                existing_data = dict()
            else:
                existing_data = json.load(file)
        # append data
        existing_data[ID] = questiondata
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, indent=4)
        
        LOG.write('INFO', '存入题目, ID: {}'.format(ID))
        index_file = os.path.join(self.text_folder, 'index')
        with open(index_file, 'r', encoding='utf-8') as file:
            if os.path.getsize(index_file) == 0:
                existing_index = dict()
            else:
                existing_index = json.load(file)
        existing_index[ID] = questiondata['index']
        with open(index_file, 'w', encoding='utf-8') as file:
            json.dump(existing_index, file, indent=4)

        return True
    
    def access_data_file(self):
        file = open(os.path.join(self.text_folder, 'question_data'), 'r+', encoding='utf-8')
        return file
    
    def release_file(self, file):
        file.close()
        return True
    
    @staticmethod
    def import_data(image_folder, text_folder):
        image_root = os.path.join(GlobalData.DATA_ROOT_PATH, 'Images')
        text_root = os.path.join(GlobalData.DATA_ROOT_PATH, 'Text')
        images = os.listdir(image_folder)
        text_files = os.listdir(text_folder)
        try:
            for file in images:
                shutil.copyfile(os.path.join(image_folder, file), 
                                os.path.join(image_root, file))
            for file in text_files:
                shutil.copyfile(os.path.join(text_folder, file),
                                os.path.join(text_root, file))
            
            LOG.write('INFO', '从{}, {}导入数据'.format(image_folder, text_folder))
        except:
            LOG.write('ERROR', 'OS Error 写入失败')
    
    @staticmethod
    def backup(output_path):
        disk = DiskController()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        zip_filename = f"{timestamp}-backup.zip"
        temp_zip_path = os.path.join(output_path, 'TEMP-'+zip_filename)
        
        try:
            for folder in [disk.image_folder, disk.text_folder]:
                if not os.path.isdir(folder):
                    raise FileNotFoundError(f"源文件夹不存在: {folder}")
            
            if not os.path.isdir(output_path):
                raise FileNotFoundError(f"输出路径不存在: {output_path}")
            
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for folder in [disk.image_folder, disk.text_folder]:
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.isfile(file_path):
                                arcname = os.path.relpath(file_path, os.path.dirname(folder))
                                zipf.write(file_path, arcname)
            
            final_zip_path = os.path.join(output_path, zip_filename)
            
            if os.path.exists(final_zip_path):
                os.remove(final_zip_path)
            
            os.rename(temp_zip_path, final_zip_path)
            
            file_size = os.path.getsize(final_zip_path) / (1024 * 1024)
            size_str = f"{file_size:.2f} MB"
            
            return True, size_str
        
        except Exception:
            if os.path.exists(temp_zip_path):
                try:
                    os.remove(temp_zip_path)
                except:
                    pass
            return False, ''

if __name__ == '__main__':
    a = os.path.dirname(os.path.abspath(__file__))
    print(os.path.dirname(a))