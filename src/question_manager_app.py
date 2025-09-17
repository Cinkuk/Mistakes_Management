import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QSplitter, QPushButton, QStackedWidget,
                               QLabel, QComboBox, QLineEdit, QTextEdit, QScrollArea,
                               QFrame, QCheckBox, QSpinBox, QFileDialog, QMessageBox,
                               QGridLayout, QSizePolicy, QGroupBox, QInputDialog, QLayout, QListWidget,
                               QListWidgetItem, QDialog, QDialogButtonBox, QFileDialog, QDoubleSpinBox,
                               QListView)
from PySide6.QtCore import Qt, QDateTime, QSize, Signal, QEventLoop, QDir, QEvent
from PySide6.QtGui import QPixmap, QFont, QFontMetrics, QAction, QKeySequence
import json
import os
from datetime import datetime
from time import sleep
import threading

import DataManagement, GlobalData, Exporter, LogManagement

ALLOW_REFRESH = False # if allow loading question data

LOG = LogManagement.Log('user')

Cache = GlobalData.Cache()

def adjust_to_content(combo_box, extra_width=25):
    """
    根据内容调整下拉菜单宽度
    :param combo_box: QComboBox 实例
    :param extra_width: 额外增加的宽度
    """
    fm = combo_box.fontMetrics()
    max_width = 0
    
    # 计算最宽文本的宽度
    for i in range(combo_box.count()):
        text = combo_box.itemText(i)
        width = fm.boundingRect(text).width()
        if width > max_width:
            max_width = width
    
    # 设置新宽度（包括下拉箭头和边距）
    new_width = max_width + extra_width
    combo_box.setMinimumWidth(new_width)
    if combo_box.view():
        combo_box.view().setMinimumWidth(new_width)

class keypointInputDialog(QDialog):
    def __init__(self, ui, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        #self.setWindowTitle("请输入知识点")
        #self.input_label = QLabel("请输入内容:")
        self.input_label = QLabel()
        self.line_edit = QLineEdit()
        self.appendix_label = QLabel()
        self.appendix_label.setWordWrap(True)
        self.notice_label = QLabel('相似知识点:')

        self.line_edit.textChanged.connect(self._on_text_changed)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.input_label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.notice_label)
        layout.addWidget(self.appendix_label)
        layout.addWidget(buttons)

        self.ui = ui
    
    def _on_text_changed(self, content):
        self.on_text_changed(content)
    
    def on_text_changed(self, content):
        #print('enter')
        subject = self.ui.subject_combo.currentText()
        keypoints = self.ui.question_data.keypoint_child
        current_keypoints = []
        relative_keypoints = []
        #print(subject)
        if subject in keypoints.keys():
            current_keypoints = keypoints[subject]
            for item in current_keypoints:
                if content and content in item:
                    relative_keypoints.append(item)
        #print(current_keypoints)
        if relative_keypoints:
            text = ''
            for i in range(len(relative_keypoints)):
                text += relative_keypoints[i]
                if not i % 3 == 2:
                    text += ' ; '
                else:
                    text += '\n'
            #print(relative_keypoints)
            self.setAppendixText(text)
        else:
            text = ''
            self.setAppendixText(text)
        #print(relative_keypoints)

    def setAppendixText(self, text):
        self.appendix_label.setText(text)
        self.adjustSize()

    def textValue(self):
        return self.line_edit.text()
    
    @staticmethod
    def getText(parent=None, title="", label=""):
        dialog = keypointInputDialog(parent)
        dialog.setWindowTitle(title)
        dialog.input_label.setText(label)
        
        ok = dialog.exec_() == QDialog.Accepted
        input_text = dialog.textValue() if ok else ""
        if input_text == "":
            ok = False
        
        return (input_text, ok)
          
class ChooseFile(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_folder = ''
        self.text_folder = ''

        self.setMinimumWidth(600)
        self.setMaximumWidth(600)
        self.setMinimumHeight(200)
        self.setMaximumHeight(200)

        layout = QVBoxLayout()
        grid_widget = QWidget()
        grid = QGridLayout()

        self.label1 = QLabel('请选择图片文件夹Images路径')
        self.label2 = QLabel('请选择文本数据文件夹Text路径')
        self.line1_edit = QLineEdit()
        self.line1_edit.setEnabled(False)
        self.line2_edit = QLineEdit()
        self.line2_edit.setEnabled(False)
        self.line1_btn = QPushButton('...')
        self.line2_btn = QPushButton('...')
        self.ok_btn = QPushButton('确定')

        grid.addWidget(self.label1, 0, 0)
        grid.addWidget(self.line1_edit, 0, 1)
        grid.addWidget(self.line1_btn, 0, 2)

        grid.addWidget(self.label2, 1, 0)
        grid.addWidget(self.line2_edit, 1, 1)
        grid.addWidget(self.line2_btn, 1, 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 4)
        grid.setColumnStretch(2, 0.3)

        self.line1_btn.clicked.connect(lambda : self.select_folder(0))
        self.line2_btn.clicked.connect(lambda : self.select_folder(1))
        self.ok_btn.clicked.connect(lambda : self.close())

        grid_widget.setLayout(grid)
        layout.addWidget(QLabel('请解压软件备份文件, 并分别选择其中的Images和Text文件夹所在路径. 导入后请重启软件.'))
        layout.addWidget(grid_widget)
        layout.addWidget(self.ok_btn)

        self.setLayout(layout)
        self.exec()
    

    def select_folder(self, index):
        folder_path = QFileDialog.getExistingDirectory(
        None,  # 父窗口
        "选择文件夹",  # 对话框标题
        "",  # 起始目录（空表示默认目录）
        QFileDialog.ShowDirsOnly  # 只显示目录
    )
    
        if folder_path:  # 如果用户没有取消选择
            if index == 0:
                self.image_folder = folder_path
                self.line1_edit.setText(folder_path)
            if index == 1:
                self.text_folder = folder_path
                self.line2_edit.setText(folder_path)
        
    @staticmethod
    def get_folders():
        dialog = ChooseFile()
        if dialog.image_folder and dialog.text_folder:
            return (dialog.image_folder, dialog.text_folder)
        else:
            return None

class ImageViewerDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True)
        
        self.load_image(image_path)
        
        scroll.setWidget(self.image_label)
        
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)
    
    def load_image(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            screen_size = QApplication.primaryScreen().availableSize()
            max_width = screen_size.width() * 0.8
            max_height = screen_size.height() * 0.8
            
            scaled_pixmap = pixmap.scaled(
                QSize(max_width, max_height),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.resize(scaled_pixmap.width(), scaled_pixmap.height())
    
    @staticmethod
    def show(image_path):
        window = ImageViewerDialog(image_path)
        window.exec()

class QuestionWidget():
    def __init__(self, question_data, ID, parent):
        self.parent = parent
        self.question_data = question_data
        self.widget = self.create_widget(ID)
    
    def get_question_data(self, ID):
        # return ID, subject, source, times, image, keypoints, note, answer, page, number
        disk = DataManagement.DiskController()
        return disk.read_questions(ID)

    def fill_widget(self, widget, data):
        ID, subject, source, times, image_path, keypoints, note, answer, page, number = data
        if ID:
            widget.ID_label.setText(ID)
        if subject:
            widget.subject_label.setText(subject)
        if source:
            widget.source_label.setText(source)
        if times:
            widget.times_label.setText(str(times))
        if image_path:
            if Cache.if_in(image_path):
                qtimage = Cache.read(image_path)
            else:
                qtimage = QPixmap(image_path)
                Cache.add(image_path, qtimage)
            image_size = qtimage.size()
            label_size = widget.image_label.size()
            # 计算缩放比例
            ratio = 0.75 * min(label_size.width() / image_size.width(), 
                    label_size.height() / image_size.height())

            # 应用缩放
            scaled_size = QSize(image_size.width() * ratio, 
                            image_size.height() * ratio)
            
            pixmap = QPixmap(qtimage).scaled(
                scaled_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
                )
            widget.image_label.setPixmap(pixmap)
        if page:
            self.page_label.setText(page)
        if number:
            self.number_label.setText(number)
        if keypoints:
            points = ' ; '.join(keypoints)
            widget.keypoints_label.setText(points)
        if note:
            widget.notice_label.setText(note)
        if answer:
            widget.answer_label.setText(answer)
    
    def create_widget(self, ID):
        data = self.get_question_data(ID)
        if data is False:
            return QWidget()
        image_path = data[4]

        widget = QFrame()
        layout = QVBoxLayout()
        line1 = QHBoxLayout()
        line2 = QHBoxLayout()
        line3 = QHBoxLayout()
        line4 = QHBoxLayout()
        line5 = QHBoxLayout()

        widget.setFrameShape(QFrame.Box)
        widget.setFrameShadow(QFrame.Plain)
        widget.setLineWidth(1)
        widget.setMidLineWidth(0)
        #widget.setStyleSheet("""
        #            QWidget {
        #                border: 1px solid black;
        #            }
        #        """)
        
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # line 1
        line1.addWidget(QLabel('题目编号:'))
        self.ID_label = QLabel()
        line1.addWidget(self.ID_label)
        line1.addStretch()
        line1.addWidget(QLabel('科目:'))
        self.subject_label = QLabel()
        line1.addWidget(self.subject_label)
        line1.addStretch()
        line1.addWidget(QLabel('来源:'))
        self.source_label = QLabel()
        line1.addWidget(self.source_label)
        line1.addStretch()
        line1.addWidget(QLabel('页码:'))
        self.page_label = QLabel()
        line1.addWidget(self.page_label)
        line1.addStretch()
        line1.addWidget(QLabel('编号:'))
        self.number_label = QLabel()
        line1.addWidget(self.number_label)
        line1.addStretch()
        line1.addWidget(QLabel('错误次数:'))
        self.times_label = QLabel()
        line1.addWidget(self.times_label)
        line1.addStretch()
        self.edit_btn = QPushButton('编辑')
        self.edit_btn.setMaximumWidth(60)
        line1.addWidget(self.edit_btn)
        self.del_btn = QPushButton('删除')
        self.del_btn.setMaximumWidth(60)
        line1.addWidget(self.del_btn)

        self.edit_btn.clicked.connect(self.edit)
        self.del_btn.clicked.connect(lambda : self.delete(self.ID_label.text()))

        # line 2
        self.image_label = QLabel()
        line2.addStretch()
        line2.addWidget(self.image_label)
        line2.addStretch()
        self.image_label.mousePressEvent = lambda event : ImageViewerDialog.show(image_path)

        # line 3
        line3.addWidget(QLabel('知识点: '))
        self.keypoints_label = QLabel()
        line3.addWidget(self.keypoints_label)
        line3.addStretch()

        # line 4
        line4.addWidget(QLabel('备注: '))
        self.notice_label = QLabel()
        line4.addWidget(self.notice_label)
        line4.addStretch()

        # line 5
        line5.addWidget(QLabel('答案: '))
        self.answer_label = QLabel()
        line5.addWidget(self.answer_label)
        line5.addStretch()

        for i, line in enumerate([line1, line2, line3, line4, line5]):
            line.setSpacing(0)
            line.setContentsMargins(12, 0, 12, 0)
            container = QWidget()
            container.setMinimumHeight(30)
            container.setMaximumHeight(30)
            if i == 1:
                container.setMinimumHeight(100)
                container.setMaximumHeight(100)
            container.setLayout(line)
            layout.addWidget(container)

        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        # fill content
        self.fill_widget(self, data)

        return widget

    def edit(self):
        editor = EditWindow(self.question_data, self)
        editor.show()

    def delete(self, ID):
        msg = QMessageBox()
        msg.setWindowTitle('确认删除?')
        msg.setText('确认删除题目(ID: {})?'.format(ID))
        msg.addButton(QMessageBox.Ok)
        cancel = msg.addButton(QMessageBox.Cancel)
        msg.setDefaultButton(cancel)
        rst = msg.exec()
        # delete
        if rst == QMessageBox.Ok:
            subject = self.parent.filter_subject.currentText()
            source = self.parent.filter_source.currentText()
            self.question_data.MetaData.del_bind('ID', [subject, source, ID])
            LOG.write('INFO', f'删除题目 ID: {ID}')
        else:
            # cancel deletion 
            return

    @staticmethod
    def get_widget(question_data, ID, parent):
        widget_class = QuestionWidget(question_data, ID, parent)
        return widget_class.widget


class export_page_question(QWidget):
    """Memory-optimized version of export_page_question with __slots__"""
    __slots__ = ('list_widget_item', 'question_data', 'parent', 'widget', '_data_cache', '_image_path')
    
    def __init__(self, question_data, ID, parent):
        super().__init__()
        self.list_widget_item = None
        self.question_data = question_data
        self.parent = parent
        self._data_cache = None
        self._image_path = None
        self.widget = self.create_widget(ID)

    def set_list_widget_item(self, item):
        self.list_widget_item = item
    
    def mousePressEvent(self, event):
        if self.list_widget_item:
            new_state = Qt.Checked if self.list_widget_item.checkState() == Qt.Unchecked else Qt.Unchecked
            self.list_widget_item.setCheckState(new_state)
        super().mousePressEvent(event)

    def get_question_data(self, ID):
        """Cache the data to avoid repeated disk access"""
        if self._data_cache is None:
            disk = DataManagement.DiskController()
            self._data_cache = disk.read_questions(ID)
        return self._data_cache

    def _create_compact_thumbnail(self, image_path):
        """Create even more compact thumbnail for export view"""
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(80)
        image_label.setMaximumHeight(80)
        
        if image_path:
            self._image_path = image_path
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Smaller thumbnail for export view
                thumbnail = pixmap.scaled(
                    QSize(120, 60),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                image_label.setPixmap(thumbnail)
            
            image_label.mousePressEvent = lambda event: ImageViewerDialog.show(image_path)
        
        return image_label

    def fill_widget(self, widget, data):
        """Streamlined fill widget"""
        ID, subject, source, times, image_path, keypoints, note, answer, page, number = data
        
        widget.ID_label.setText(ID or "")
        widget.subject_label.setText(subject or "")
        widget.source_label.setText(source or "")
        widget.times_label.setText(str(times) if times else "0")
        widget.page_label.setText(page or "")
        widget.number_label.setText(number or "")
        widget.keypoints_label.setText(' ; '.join(keypoints) if keypoints else "")

    def create_widget(self, ID):
        data = self.get_question_data(ID)
        if data is False:
            return QWidget()
        
        ID, subject, source, times, image_path, keypoints, note, answer, page, number = data

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create compact labels
        widget.ID_label = QLabel(ID or "")
        widget.ID_label.setObjectName('ID_label')
        widget.subject_label = QLabel(subject or "")
        widget.source_label = QLabel(source or "")
        widget.times_label = QLabel(str(times) if times else "0")
        widget.page_label = QLabel(page or "")
        widget.number_label = QLabel(number or "")
        widget.keypoints_label = QLabel(' ; '.join(keypoints) if keypoints else "")

        # Compact info line
        line1_container = QWidget()
        line1_container.setMaximumHeight(25)
        line1 = QHBoxLayout(line1_container)
        line1.setSpacing(8)
        line1.setContentsMargins(8, 0, 8, 0)

        info_widgets = [
            ("题目编号:", widget.ID_label),
            ("科目:", widget.subject_label),
            ("来源:", widget.source_label),
            ("页码:", widget.page_label),
            ("编号:", widget.number_label),
            ("错误次数:", widget.times_label)
        ]
        
        for label_text, value_widget in info_widgets:
            line1.addWidget(QLabel(label_text))
            line1.addWidget(value_widget)
            line1.addStretch()

        layout.addWidget(line1_container)

        # Compact image
        line2_container = QWidget()
        line2_container.setMaximumHeight(80)
        line2 = QHBoxLayout(line2_container)
        line2.addStretch()
        widget.image_label = self._create_compact_thumbnail(image_path)
        line2.addWidget(widget.image_label)
        line2.addStretch()
        layout.addWidget(line2_container)

        # Keypoints line
        line3_container = QWidget()
        line3_container.setMaximumHeight(25)
        line3 = QHBoxLayout(line3_container)
        line3.setContentsMargins(8, 0, 8, 0)
        line3.addWidget(QLabel('知识点:'))
        line3.addWidget(widget.keypoints_label)
        line3.addStretch()
        layout.addWidget(line3_container)
        
        widget.mousePressEvent = self.mousePressEvent
        widget.item = self.list_widget_item

        return widget

    @staticmethod
    def get_widget(question_data, ID, parent):
        question_class = export_page_question(question_data, ID, parent)
        return question_class


# Additional memory optimization utilities
class MemoryOptimizedCache:
    """Enhanced cache with memory limits and cleanup"""
    def __init__(self, max_size=100):
        self._cache = {}
        self._access_order = []
        self._max_size = max_size
    
    def add(self, key, value):
        if len(self._cache) >= self._max_size:
            # Remove least recently used
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
        
        self._cache[key] = value
        self._access_order.append(key)
    
    def read(self, key):
        if key in self._cache:
            # Update access order
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def if_in(self, key):
        return key in self._cache
    
    def clear(self):
        self._cache.clear()
        self._access_order.clear()


# Memory monitoring utility
def get_widget_memory_info(widget):
    """Debug utility to check memory usage of widgets"""
    import sys
    size = sys.getsizeof(widget)
    children_size = sum(sys.getsizeof(child) for child in widget.findChildren(QWidget))
    return {"widget_size": size, "children_size": children_size, "total": size + children_size}
        

class Data:
    def __init__(self):
        # read in questions data
        self.questions = dict()
        self.subjects = GlobalData.SUBJECTS
        self.sources = GlobalData.SOURCES
        self.question_types = GlobalData.QUESTION_TYPES
        if 'subjects' in GlobalData.BIND.keys():
            # subject & source
            self.subject_child = GlobalData.BIND['subjects']
        else:
            self.subject_child = dict()
        if 'sources' in GlobalData.BIND.keys():
            # subject->source & ID
            self.source_child = GlobalData.BIND['sources']
        else:
            self.source_child = dict()
        if 'keypoints' in GlobalData.BIND.keys():
            # subject & keypoints
            self.keypoint_child = GlobalData.BIND['keypoints']
        else:
            self.keypoint_child = dict()
        self.MetaData = DataManagement.MetaDataController()

    
    def update_metadata(self):
        #self.subjects, self.sources, self.question_types = self.MetaData.get_metadata()
        # update UI
        self.subject_child = self.MetaData.bind['subjects']

    def add_question(self, question_data):
        ID = question_data['ID']
        index = question_data['index']
        subject = question_data['subject']
        source = question_data['source']

        # bind subject & source; source & ID
        subject_keys = self.subject_child.keys()
        if subject not in subject_keys:
            self.subject_child[subject] = []
            self.MetaData.add_bind('source', [subject, source])
        
        if subject not in self.source_child.keys():
            self.subject_child[subject] = dict() 
        source_keys = self.source_child[subject].keys()
        if source not in source_keys:
            self.source_child[subject][source] = []
        if source not in self.subject_child[subject]:
            self.subject_child[subject].append(source)
        if ID not in self.source_child[subject][source]:
            self.source_child[subject][source].append(ID)
            self.MetaData.add_bind('ID', [subject, source, ID])

        # add question data: ID and index    
        question_keys = self.questions.keys()
        if subject not in question_keys:
            self.questions[subject] = []
        self.questions[subject].append((ID, index))

    def del_question(self, question_data):
        # delete bind of source & ID
        pass
    
    def add_subject(self, subject):
        if subject and not self.MetaData.if_in('subjects', subject):
            self.MetaData.add_subject(subject)
        if subject and subject not in GlobalData.BIND['subjects'].keys():
            GlobalData.BIND['subjects'][subject] = []
            self.subject_child[subject] = []
        if subject not in self.source_child.keys():
            self.source_child[subject] = {}
            GlobalData.BIND['sources'][subject] = {}
        if subject not in self.keypoint_child.keys():
            self.keypoint_child[subject] = []
            GlobalData.BIND['keypoints'][subject] = []
        self.update_metadata()
        return True
    
    def del_subject(self, subject):
        rst = self.MetaData.del_subject(subject)
        self.update_metadata()
        return rst
    
    def add_source(self, subject, source):
        if source and source not in GlobalData.BIND['subjects'][subject]:
            self.MetaData.add_source(source)
            self.MetaData.add_bind('source', [subject, source])
            self.update_metadata()
            return True
        return False
    
    def del_source(self, source):
        rst = self.MetaData.del_source(source)
        self.update_metadata()
        return rst
    
    def add_question_type(self, type):
        if type and not self.MetaData.if_in('question_types', type):
            self.MetaData.add_question_types(type)
            self.update_metadata()
            return True
        return False
    
    def del_question_type(self, type):
        rst = self.MetaData.del_queation_types(type)
        self.update_metadata()
        return rst
    
    def add_keypoints(self, subject, content):
        #print(GlobalData.BIND)
        keys = self.keypoint_child.keys()
        if subject not in keys:
            self.keypoint_child[subject] = []
        if content not in self.keypoint_child[subject]:
            self.keypoint_child[subject].append(content)
        self.MetaData.update_keypoints(self.keypoint_child)
        #print(GlobalData.BIND)
    
    def del_keypoint(self, subject, content):
        keys = self.keypoint_child.keys()
        if subject not in keys:
            return False
        if content not in self.keypoint_child[subject]:
            return True
        self.keypoint_child[subject].remove(content)
        self.MetaData.update_keypoints(self.keypoint_child)
        return True


class SidebarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(10)
        
        # 标题
        #title = QLabel("题目管理系统")
        #title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;")
        #layout.addWidget(title)
        
        # 按钮样式
        btn_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                text-align: left;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        
        # 导航按钮
        self.editor_btn = QPushButton("录入")
        self.editor_btn.setStyleSheet(btn_style)
        
        self.checker_btn = QPushButton("编辑")  
        self.checker_btn.setStyleSheet(btn_style)
        
        self.exporter_btn = QPushButton("导出")
        self.exporter_btn.setStyleSheet(btn_style)

        self.import_btn = QPushButton('导入')
        self.import_btn.setStyleSheet(btn_style)
        
        layout.addWidget(self.editor_btn)
        layout.addWidget(self.checker_btn)
        layout.addWidget(self.exporter_btn)
        layout.addWidget(self.import_btn)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #ecf0f1;")
        
class EditorWidget(QWidget):
    def __init__(self, question_data: Data, parent=None):
        super().__init__(parent)
        self.question_data = question_data
        self.image = ""
        self.setup_ui()
        self.datamanage = self.question_data.MetaData
        self.disk = DataManagement.DiskController()
        # initial metadata
        self.subject_combo.addItems(GlobalData.SUBJECTS)
        self.mark_combo.addItems(GlobalData.QUESTION_TYPES)

        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Line1: 题目来源
        source_group = QGroupBox("题目来源")
        self.new_source_layout = QVBoxLayout()
        source_layout = QHBoxLayout()
        source_layout_widget = QWidget()
        subject_btn_layout = QHBoxLayout()
        subject_btn_layout.setSpacing(0)

        self.subject_combo = QComboBox()

        # 科目下拉
        source_layout.addWidget(QLabel("科目:"))
        self.subject_add_btn = QPushButton("+")
        self.subject_del_btn = QPushButton("-")
        self.source_combo = QComboBox()
        self.source_add_btn = QPushButton("+")
        self.source_del_btn = QPushButton("-")
        self.page_edit = QLineEdit()
        self.mark_combo = QComboBox()
        self.mark_add_btn = QPushButton("+")
        self.mark_del_btn = QPushButton("-")
        self.number_edit = QLineEdit()
        
        #self.subject_combo.setEditable(True)
        self.update_subject_combo()
        self.subject_combo.setMinimumWidth(130)
        self.subject_combo.currentTextChanged.connect(self.update_subject_combo)
        self.subject_combo.currentTextChanged.connect(self.update_from_text)
        self.subject_combo.currentTextChanged.connect(lambda : self.page_edit.clear())
        
        self.subject_add_btn.setMaximumWidth(20)
        self.subject_add_btn.clicked.connect(self.add_subject)
        
        self.subject_del_btn.setMaximumWidth(20)
        self.subject_del_btn.clicked.connect(self.del_subject)

        source_layout.addWidget(self.subject_combo)
        subject_btn_layout.addWidget(self.subject_add_btn)
        subject_btn_layout.addWidget(self.subject_del_btn)
        source_layout.addLayout(subject_btn_layout)
        
        # 来源下拉
        source_layout.addWidget(QLabel("来源:"))
        source_btn_layout = QHBoxLayout()
        source_btn_layout.setSpacing(0)

        
        #self.source_combo.setEditable(True)
        self.update_source_combo()
        self.source_combo.setMinimumWidth(200)
        self.source_combo.currentTextChanged.connect(self.update_from_text)
        self.source_combo.currentTextChanged.connect(lambda : self.page_edit.clear())
        
        self.source_add_btn.setMaximumWidth(20)
        self.source_add_btn.clicked.connect(self.add_source)
        
        self.source_del_btn.setMaximumWidth(20)
        self.source_del_btn.clicked.connect(self.del_source)

        source_layout.addWidget(self.source_combo)
        source_btn_layout.addWidget(self.source_add_btn)
        source_btn_layout.addWidget(self.source_del_btn)
        source_layout.addLayout(source_btn_layout)
        
        # 页数
        source_layout.addWidget(QLabel("页数:"))
        
        self.page_edit.setPlaceholderText("页数")
        self.page_edit.setMinimumWidth(50)
        self.page_edit.setMaximumWidth(70)
        self.page_edit.textChanged.connect(self.update_from_text)
        source_layout.addWidget(self.page_edit)
        
        # 题目类型
        mark_btn_layout = QHBoxLayout()
        mark_btn_layout.setSpacing(0)
        
        
        self.mark_combo.setMinimumWidth(70)
        #self.mark_combo.setEditable(True)
        #adjust_to_content(self.mark_combo)
        self.mark_combo.currentTextChanged.connect(self.update_from_text)
        
        self.mark_add_btn.setMaximumWidth(20)
        self.mark_add_btn.clicked.connect(self.add_mark)
        
        self.mark_del_btn.setMaximumWidth(20)
        self.mark_del_btn.clicked.connect(self.del_mark)

        source_layout.addWidget(QLabel("标记:"))
        source_layout.addWidget(self.mark_combo)
        mark_btn_layout.addWidget(self.mark_add_btn)
        mark_btn_layout.addWidget(self.mark_del_btn)
        source_layout.addLayout(mark_btn_layout)
        
        # 题号
        source_layout.addWidget(QLabel("题号:"))
        
        self.number_edit.setPlaceholderText("题号")
        #self.number_edit.setMaximumWidth(70)
        self.number_edit.textChanged.connect(self.update_from_text)
        source_layout.addWidget(self.number_edit)

        source_layout_widget.setLayout(source_layout)
        self.new_source_layout.addWidget(source_layout_widget)
        
        # 来源文字
        from_widget = QWidget()
        from_layout = QHBoxLayout()
        from_layout.setAlignment(Qt.AlignLeft)
        from_label = QLabel('来源')
        self.from_text = QLabel()
        self.from_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.from_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        from_layout.addWidget(from_label)
        from_layout.addWidget(self.from_text)
        from_widget.setLayout(from_layout)

        self.new_source_layout.addWidget(from_widget)
        source_group.setLayout(self.new_source_layout)
        layout.addWidget(source_group)

        # Line2: 题目图片
        image_group = QGroupBox("题目图片")
        image_layout = QVBoxLayout()
        #image_layout.setContentsMargins(0, 0, 1, 1)
        
        image_btn_layout = QHBoxLayout()
        self.paste_image_btn = QPushButton("粘贴图片")
        self.paste_image_btn.clicked.connect(self.paste_image)
        self.clear_image_btn = QPushButton("清除图片")
        self.clear_image_btn.clicked.connect(self.clear_image)
        image_btn_layout.addWidget(self.paste_image_btn)
        image_btn_layout.addWidget(self.clear_image_btn)
        image_btn_layout.addStretch()
        
        self.image_label = QLabel("未选择图片")
        self.image_label.setStyleSheet("border: 2px dashed #bdc3c7; padding: 20px; text-align: center;")
        self.image_label.setMinimumHeight(150)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        image_layout.addLayout(image_btn_layout)
        image_layout.addWidget(self.image_label)
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)

        # Line3: 知识点 答案
        points_group = QGroupBox()
        points_layout = QHBoxLayout()

        # 知识点
        keypoint_group = QGroupBox('知识点')
        keypoint_layout = QVBoxLayout()
        keypoint_layout.setSpacing(0)
        
        self.keypoints_list = QListWidget()
        self.add_keypoint_btn = QPushButton('+')
        self.add_keypoint_btn.clicked.connect(self.add_keypoint)

        keypoint_layout.addWidget(self.keypoints_list)
        keypoint_layout.addWidget(self.add_keypoint_btn)

        keypoint_group.setLayout(keypoint_layout)
        
        # 答案, 备注
        answer_notice_group = QWidget()
        answer_notice_layout = QVBoxLayout()

        # 答案
        answer_group = QGroupBox("答案")
        answer_layout = QVBoxLayout()
        
        self.answer_edit = QLineEdit()
        self.answer_edit.setPlaceholderText("请输入答案...")
        self.answer_edit.setMaximumHeight(250)

        answer_layout.addWidget(self.answer_edit)
        answer_group.setLayout(answer_layout)

        # 备注
        notice_group = QWidget()
        notice_layout = QVBoxLayout()
        notice_layout.setContentsMargins(0, 0, 0, 0)

        notice_label = QLabel('备注')
        self.notice_edit = QLineEdit()
        self.notice_edit.setPlaceholderText('请输入备注...')
        self.notice_edit.setMinimumHeight(130)
        self.notice_edit.setMaximumHeight(200)

        notice_layout.addWidget(notice_label)
        notice_layout.addWidget(self.notice_edit)
        notice_group.setLayout(notice_layout)

        answer_notice_layout.addWidget(answer_group)
        answer_notice_layout.addStretch()
        answer_notice_layout.addWidget(notice_group)
        answer_notice_group.setLayout(answer_notice_layout)

        points_layout.addWidget(keypoint_group)
        points_layout.addWidget(answer_notice_group)
        points_group.setLayout(points_layout)
        layout.addWidget(points_group)
        
        # 保存按钮
        save_btn = QPushButton("保存题目")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_question)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_from_text(self):
        subject = self.subject_combo.currentText()
        source = self.source_combo.currentText()
        page = 'P' + self.page_edit.text()
        mark = self.mark_combo.currentText()
        number = self.number_edit.text()

        content = ' '.join((subject, source, page, mark, number))
        self.from_text.setText(content)


    def update_subject_combo(self):
        """更新科目下拉框"""
        current_text = self.subject_combo.currentText()
        #print('update action')
        #print(self.question_data.subject_child)
        #print(GlobalData.BIND, GlobalData.SUBJECTS, GlobalData.SOURCES)
        self.source_combo.clear()
        if current_text in self.question_data.subject_child.keys():
            sources = self.question_data.subject_child[current_text]
            self.source_combo.addItems(sources)

    def update_source_combo(self):
        """更新来源下拉框"""
        current_text = self.source_combo.currentText()
        #self.source_combo.clear()
        #self.source_combo.addItems(self.question_data.sources)
        #if current_text in self.question_data.sources:
        #    self.source_combo.setCurrentText(current_text)
    
    def update_mark_combo(self):
        current_text = self.mark_combo.currentText()
        #self.mark_combo.clear()
        #self.mark_combo.addItems(self.question_data.question_types)
        #if current_text in self.question_data.question_types:
        #    self.mark_combo.setCurrentText(current_text)
    
    def confirm_del(self, type, content):
        report_type = {'subject': '科目', 'source': '来源', 'mark': '题目类型'}
        if not content:
            msg = QMessageBox()
            msg.setText(f'{report_type[type]}已空')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            return False
        # 检查Type是否下是否已有数据
        # check_pass = 
        # 已有数据
        # if not check_pass:
        # 弹出窗口提示
        # return False

        msg = QMessageBox()
        msg.setText(f'确认删除{content}?')
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        rst = msg.exec()
        if rst == QMessageBox.Ok:
            return True
        else:
            return False
        
    
    def add_subject(self):
        text, ok = QInputDialog.getText(
            None,
            "请输入科目",
            "请输入内容:")
        if text and ok:
            self.question_data.add_subject(text)
            self.subject_combo.addItem(text)
            self.update_subject_combo()
            self.subject_combo.setCurrentText(text)
            return True
        return False
        

    def del_subject(self):
        current_text = self.subject_combo.currentText()
        check_pass = self.confirm_del('subject', current_text)
        if check_pass:
            rst = self.question_data.del_subject(current_text)
            self.update_subject_combo()
            return rst
        else:
            return False

    def add_source(self):
        text, ok = QInputDialog.getText(
            None,
            "请输入来源",
            "请输入内容:")
        if text and ok:
            self.question_data.add_source(self.subject_combo.currentText(), text)
            self.source_combo.addItem(text)
            #self.update_source_combo()
            self.source_combo.setCurrentText(text)
            return True
        return False

    def del_source(self):
        current_text = self.source_combo.currentText()
        check_pass = self.confirm_del('source', current_text)
        if check_pass:
            rst = self.question_data.del_source(current_text)
            self.update_source_combo()
            return rst
        else:
            return False

    def add_mark(self):
        text, ok = QInputDialog.getText(
            None,
            "请输入题目类型",
            "请输入内容:")
        if text and ok:
            self.question_data.add_question_type(text)
            self.mark_combo.addItem(text)
            self.update_mark_combo()
            self.mark_combo.setCurrentText(text)
            return True
        return False

    def del_mark(self):
        current_text = self.mark_combo.currentText()
        check_pass = self.confirm_del('mark', current_text)
        if check_pass:
            rst = self.question_data.del_question_type(current_text)
            self.update_mark_combo()
            return rst
        else:
            return False
    
    def add_keypoint(self):
        #text, ok = QInputDialog.getText(
        #    None,
        #    '请输入知识点',
        #    '请输入内容')
        text, ok = keypointInputDialog.getText(
            self,
            '请输入知识点',
            '请输入内容'
            )
        if text and ok :
            content = text
        else:
            return 
        item = QListWidgetItem()
        widget = QWidget()
        itemlayout = QHBoxLayout()
        itemlayout.setContentsMargins(10, 2, 10, 2)
        itemlayout.setSpacing(0)
        label = QLabel(content)
        del_btn = QPushButton('×')
        del_btn.clicked.connect(lambda: self.del_keypoint(item))
        itemlayout.addWidget(label)
        itemlayout.addStretch()
        itemlayout.addWidget(del_btn)
        widget.setLayout(itemlayout)
        self.keypoints_list.addItem(item)
        self.keypoints_list.setItemWidget(item, widget)
        item.setSizeHint(widget.sizeHint())
        self.question_data.add_keypoints(self.subject_combo.currentText(), content)


    def del_keypoint(self, item):
        # remove keypoint from current question
        widget = self.keypoints_list.itemWidget(item)
        label = widget.findChild(QLabel)
        content = label.text()
        subject = self.subject_combo.currentText()

        row = self.keypoints_list.row(item)
        self.keypoints_list.takeItem(row)
        #self.question_data.del_keypoint(subject, content)
            
    def clear_image(self):
        self.image = ""
        self.image_label.clear()
        self.image_label.setText("未选择图片")
    
    def paste_image(self):
        # get image from clipboard
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        # show image
        if image:
            return self.show_image(image)
        else:
            return False

    def show_image(self, qtimage):
        # 手动计算保持宽高比的缩放比例
        image_size = qtimage.size()
        label_size = self.image_label.size()

        # 计算缩放比例
        ratio = 0.75 * min(label_size.width() / image_size.width(), 
                label_size.height() / image_size.height())

        # 应用缩放
        scaled_size = QSize(image_size.width() * ratio, 
                        image_size.height() * ratio)
        
        pixmap = QPixmap(qtimage).scaled(
            scaled_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
            )
        self.image_label.setPixmap(pixmap)
        self.image = qtimage
        return True
        
        
    def save_question(self):
        # if question is empty
        if self.image_label.text() in ['未选择图片']:
            msg = QMessageBox()
            msg.setText('请录入题目')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setButtonText(QMessageBox.Ok, '好')
            msg.exec()
            return
        
        subject = self.subject_combo.currentText()
        source = self.source_combo.currentText()
        page = self.page_edit.text()
        mark = self.mark_combo.currentText()
        number = self.number_edit.text()

        # 已经录入
        flag = False
        file = self.question_data.MetaData.access_data_file()
        datas = json.load(file)
        
        if subject in self.question_data.source_child.keys():
            if source in self.question_data.source_child[subject].keys():
                for _ID in self.question_data.source_child[subject][source]:
                    if _ID in datas.keys():
                        if subject == datas[_ID]['subject'] and \
                                source == datas[_ID]['source'] and \
                                page == datas[_ID]['page'] and \
                                mark == datas[_ID]['mark'] and \
                                number == datas[_ID]['number']:
                            datas[_ID]['errortimes'] += 1
                            file.seek(0)
                            json.dump(datas, file, indent=4)
                            file.truncate()

                            msg = QMessageBox()
                            msg.setWindowTitle('重复录入')
                            msg.setText('题目已存在, 错误次数已加一')
                            msg.addButton(QMessageBox.Ok)
                            msg.exec()
                            flag = True
                            break
        self.question_data.MetaData.release_file(file)
        if flag:
            return
        
        # 剩余未获取的题目数据
        ID = self.datamanage.newID()
        image = self.image
        keypoints = []
        answer = self.answer_edit.text()
        notice = self.notice_edit.text()

        

        for i in range(self.keypoints_list.count()):
            item = self.keypoints_list.item(i)
            widget = self.keypoints_list.itemWidget(item)
            if widget:
                for child in widget.findChildren(QLabel):
                    keypoints.append(child.text())
        
        IDStr = '{:06d}'.format(ID)
        index = DataManagement.get_md5(IDStr)
        question_data = {
            'ID': IDStr,
            'index': index,
            'subject': subject,
            'source': source,
            'page': page,
            'mark': mark,
            'number': number,
            'keypoint': keypoints,
            'notice': notice,
            'answer': answer,
            'errortimes': 1,
            'ratio': 0.0,
            'blankrow': 1
            }
        
        self.disk.write_questions(image, question_data)
        self.question_data.add_question(question_data)
        QMessageBox.information(self, "成功", "题目已保存!")
        LOG.write('INFO', f'录入 ID:{ID}')
        
        # 清空表单
        #self.page_edit.clear()
        self.number_edit.clear()
        self.answer_edit.clear()
        self.notice_edit.clear()
        self.clear_image()
        self.keypoints_list.clear()

class EditWindow(EditorWidget):
    def __init__(self, question_data, ui=None):
        super().__init__(question_data)
        self.setWindowModality(Qt.ApplicationModal)
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen_geometry.center().x() - self.width()) // 2,
            (screen_geometry.center().y() - self.height()) // 2
        )

        self.question_data = question_data
        self.ui = ui

        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(QLabel('错误次数'))
        self.times_edit = QLineEdit()
        self.times_edit.setMinimumWidth(70)
        self.times_edit.setMaximumWidth(80)
        layout.addWidget(self.times_edit)
        layout.addStretch()
        widget.setLayout(layout)
        self.new_source_layout.addWidget(widget)

        file = question_data.MetaData.access_data_file()
        metadata = json.load(file)
        data = metadata[ui.ID_label.text()]

        self.subject_combo.setCurrentText(data['subject'])
        self.source_combo.setCurrentText(data['source'])
        self.page_edit.setText(data['page'])
        self.mark_combo.setCurrentText(data['mark'])
        self.number_edit.setText(data['number'])
        self.show_image(ui.image_label.pixmap())
        for keypoint in data['keypoint']:
            item = QListWidgetItem()
            widget = QWidget()
            itemlayout = QHBoxLayout()
            itemlayout.setContentsMargins(10, 2, 10, 2)
            itemlayout.setSpacing(0)
            label = QLabel(keypoint)
            del_btn = QPushButton('×')
            del_btn.clicked.connect(lambda: self.del_keypoint(item))
            itemlayout.addWidget(label)
            itemlayout.addStretch()
            itemlayout.addWidget(del_btn)
            widget.setLayout(itemlayout)
            self.keypoints_list.addItem(item)
            self.keypoints_list.setItemWidget(item, widget)
            item.setSizeHint(widget.sizeHint())
        self.notice_edit.setText(data['notice'])
        self.answer_edit.setText(data['answer'])
        self.times_edit.setText(str(data['errortimes']))

        question_data.MetaData.release_file(file)

    def save_question(self):
        file = self.question_data.MetaData.access_data_file()
        datas = json.load(file)
        data = datas[self.ui.ID_label.text()]
        ID = self.ui.ID_label.text()
        data['subject'] = self.subject_combo.currentText()
        data['source'] = self.source_combo.currentText()
        data['page'] = self.page_edit.text()
        data['mark'] = self.mark_combo.currentText()
        data['number'] = self.number_edit.text()
        data['keypoint'] = []
        for i in range(self.keypoints_list.count()):
            item = self.keypoints_list.item(i)
            widget = self.keypoints_list.itemWidget(item)
            if widget:
                layout = widget.layout()
                if layout and layout.count() > 0:
                    label = layout.itemAt(0).widget()
                    if isinstance(label, QLabel):
                        #print(label.text())
                        data['keypoint'].append(label.text())
        data['notice'] = self.notice_edit.text()
        data['answer'] = self.answer_edit.text()
        data['errortimes'] = int(self.times_edit.text())
        file.seek(0)
        json.dump(datas, file, indent=4)
        file.truncate()
        self.question_data.MetaData.release_file(file)

        self.close()        

class keypoints_filter_window(QWidget):
    def __init__(self, keypoints): 
        super().__init__()
        self.keypoints = keypoints
        self.selected_results = []
        layout = QVBoxLayout()

        self.setWindowTitle("知识点筛选")
        self.setWindowModality(Qt.ApplicationModal)
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen_geometry.center().x() - self.width()) // 2,
            (screen_geometry.center().y() - self.height()) // 2
        )

        self.list = QListWidget()
        
        top_widget = QWidget()
        top_layout = QHBoxLayout()
        select_all_btn = QPushButton('全选')
        select_all_btn.setMinimumWidth(20)
        unselect_all_btn = QPushButton('全不选')
        unselect_all_btn.setMinimumWidth(20)
        self.search_edit = QLineEdit()
        self.search_edit.setMinimumWidth(100)
        top_layout.addWidget(select_all_btn)
        top_layout.addWidget(unselect_all_btn)
        top_layout.addWidget(self.search_edit)
        top_layout.addStretch()
        top_widget.setLayout(top_layout)

        layout.addWidget(top_widget)
        layout.addWidget(self.list)

        ok_btn = QPushButton('确定')
        ok_btn.setMinimumWidth(20)
        btn_widget = QWidget()
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        btn_widget.setLayout(btn_layout)
        layout.addWidget(btn_widget)

        self.setLayout(layout)

        select_all_btn.clicked.connect(self.select_all)
        unselect_all_btn.clicked.connect(self.unselect_all)
        ok_btn.clicked.connect(self.on_ok_clicked)
        self.search_edit.textChanged.connect(self.searchLine_changed)
        self.list.itemChanged.connect(self.on_item_changed)

        self.refresh_keypoint()

    def on_ok_clicked(self):
        self.close()

    def select_all(self):
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setCheckState(Qt.Checked)

    def unselect_all(self):
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setCheckState(Qt.Unchecked)

    def searchLine_changed(self):
        self.refresh_keypoint()

    def refresh_keypoint(self):
        search_target = self.search_edit.text()
        results = []
        # filter candidate keypoints
        if search_target != '':
            for keypoint in self.keypoints:
                if search_target in keypoint:
                    results.append(keypoint)
        else:
            results = self.keypoints
            
        current_selected = set(self.selected_results)
        
        # clear window
        self.list.clear()

        # add candidate
        for keypoint in results:
            item = QListWidgetItem(keypoint)
            # recover status
            if keypoint in current_selected:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            self.list.addItem(item)

    def on_item_changed(self, item):
        text = item.text()
        if item.checkState() == Qt.Checked:
            if text not in self.selected_results:
                self.selected_results.append(text)
        else:
            if text in self.selected_results:
                self.selected_results.remove(text)

    def closeEvent(self, event):
        self.finished = True
        event.accept()
        if hasattr(self, '_loop'):
            self._loop.quit()

    def exec(self):
        self.show()
        self._loop = QEventLoop()
        self._loop.exec_()
        return self.selected_results
    
    @staticmethod
    def get_filter_result(keypoints):
        window = keypoints_filter_window(keypoints)
        window.exec()
        return window.selected_results

class CheckerWidget(QWidget):
    def __init__(self, question_data, parent=None):
        super().__init__(parent)
        self.question_data = question_data
        self.setup_ui()
        self.update_combo()
        self.refresh_questions()
        self.IDs = []
        self.ID_keypoint = dict()
        self.subject_IDs = []
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("题目查看")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 筛选条件
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("科目:"))
        
        self.filter_subject = QComboBox()
        self.filter_subject.setMinimumWidth(130)
        self.filter_subject.addItem("全部")
        self.filter_subject.addItems(self.question_data.subjects)
        self.filter_subject.currentTextChanged.connect(self.update_combo)
        self.filter_subject.currentTextChanged.connect(self.refresh_questions)
        self.filter_subject.currentTextChanged.connect(self.refresh_ID_keypoint)
        filter_layout.addWidget(self.filter_subject)
        
        filter_layout.addWidget(QLabel("来源:"))
        self.filter_source = QComboBox()
        self.filter_source.setMinimumWidth(130)
        self.filter_source.addItem("全部")
        self.filter_source.currentTextChanged.connect(self.refresh_questions)
        filter_layout.addWidget(self.filter_source)

        filter_layout.addWidget(QLabel("页码筛选:"))
        self.page_edit = QLineEdit()
        self.page_edit.setMinimumWidth(200)
        self.page_edit.setEnabled(True)
        self.page_edit.setPlaceholderText('在当前结果中输入页码筛选')
        self.page_edit.returnPressed.connect(self.filter_by_page)

        self.filter_keypoint = QPushButton('筛选知识点')
        self.filter_keypoint.clicked.connect(self.set_filter)
        filter_layout.addWidget(self.page_edit)
        filter_layout.addWidget(self.filter_keypoint)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 题目列表
        self.list_widget = QListWidget()
        self.list_widget.setResizeMode(QListView.Adjust)
        self.list_widget.setVerticalScrollMode(QListView.ScrollPerPixel)

        scroll_bar = self.list_widget.verticalScrollBar()
        scroll_bar.setSingleStep(13)
        scroll_bar.setPageStep(10)
        
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
    
    def refresh_ID_keypoint(self):
        subject = self.filter_subject.currentText()
        if subject != '全部':
            self.ID_keypoint = dict()
            IDs = []
            for source in self.question_data.source_child[subject].keys():
                IDs.extend(self.question_data.source_child[subject][source])
            self.subject_IDs = IDs

            file = self.question_data.MetaData.access_data_file()
            datas = json.load(file)
            self.question_data.MetaData.release_file(file)

            for ID in IDs:
                if ID in datas.keys():
                    self.ID_keypoint[ID] = datas[ID]['keypoint']
        else:
            return
        
    def update_combo(self):
        # 刷新科目和来源combo
        subject = self.filter_subject.currentText()
        self.filter_source.clear()
        self.filter_source.addItem('全部')
        if subject != '全部' and subject != '':
            self.filter_source.addItems(self.question_data.subject_child[subject])
        self.filter_source.setCurrentText('全部')

    def refresh_questions(self):
        if not ALLOW_REFRESH:
            return
        # 获取当前ID列表
        subject = self.filter_subject.currentText()
        source = self.filter_source.currentText()
        IDs = []
        if subject == '全部':
            newesID = GlobalData.NEWEST_ID
            for id in range(1, newesID + 1):
                IDs.append('{:06d}'.format(id))
        else:
            if source != '全部':
                if source in GlobalData.BIND['sources'][subject]:
                    IDs = GlobalData.BIND['sources'][subject][source]
            else:
                sources = GlobalData.BIND['sources'][subject].keys()
                for item in sources:
                    IDs.extend(GlobalData.BIND['sources'][subject][item])
        self.IDs = IDs
        # 清空滚动区域
        self.list_widget.clear()

        # 逐个题目添加进窗口
        for ID in IDs:
            widget = QuestionWidget.get_widget(self.question_data, ID, self)
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
        
    def filter_by_page(self):
        # access to question data
        file = self.question_data.MetaData.access_data_file()
        datas = json.load(file)
        self.question_data.MetaData.release_file(file)
        # filter by page
        page = self.page_edit.text()
        if page == '':
            self.refresh_questions()
            return
            
        newIDs = []
        for ID in self.IDs:
            if ID in datas.keys() and page in datas[ID]['page']:
                newIDs.append(ID)
        self.IDs = newIDs
        
        # refresh window 
        # 清空滚动区域
        self.list_widget.clear()

        # 逐个题目添加进窗口
        for ID in self.IDs:
            widget = QuestionWidget.get_widget(self.question_data, ID, self)
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def set_filter(self):
        if self.filter_subject.currentText() == '全部':
            msg = QMessageBox()
            msg.setWindowTitle('请选择科目')
            msg.setText('请选择科目后再筛选知识点')
            msg.addButton(QMessageBox.Ok)
            msg.exec()
        else:
            keypoints = self.question_data.keypoint_child[self.filter_subject.currentText()]
            filter_result = keypoints_filter_window.get_filter_result(keypoints) # keypoints
            # 筛选指定知识点
            #self.IDs = filter_result
            newIDs = []
            for ID in self.subject_IDs:
                if ID in self.ID_keypoint.keys():
                    ID_keypoint = self.ID_keypoint[ID]
                    if set(ID_keypoint) & set(filter_result):
                        newIDs.append(ID)
            self.IDs = newIDs

            # refresh window
            # 清空滚动区域
            self.list_widget.clear()

            # 逐个题目添加进窗口
            for ID in self.IDs:
                widget = QuestionWidget.get_widget(self.question_data, ID, self)
                item = QListWidgetItem()
                item.setSizeHint(widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)

class ExporterWidget(QWidget):
    def __init__(self, question_data, parent=None):
        super().__init__(parent)
        self.question_data = question_data
        self.selected_questions = list()
        self.IDs = []
        self.ID_keypoint = dict()
        self.subject_IDs = []

        self.setup_ui()
        self.update_combo()
        self.refresh_questions()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("题目导出")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 筛选和操作栏
        top_layout = QHBoxLayout()
        
        # 筛选
        top_layout.addWidget(QLabel("科目:"))
        self.filter_subject = QComboBox()
        self.filter_subject.setMinimumWidth(130)
        self.filter_subject.addItem("全部")
        self.filter_subject.addItems(self.question_data.subjects)
        self.filter_subject.currentTextChanged.connect(self.update_combo)
        self.filter_subject.currentTextChanged.connect(self.refresh_questions)
        self.filter_subject.currentTextChanged.connect(self.refresh_ID_keypoint)
        top_layout.addWidget(self.filter_subject)
        
        top_layout.addWidget(QLabel("来源:"))
        self.filter_source = QComboBox()
        self.filter_source.setMinimumWidth(130)
        self.filter_source.addItem("全部")
        self.filter_source.currentTextChanged.connect(self.refresh_questions)
        top_layout.addWidget(self.filter_source)

        top_layout.addWidget(QLabel("页码筛选:"))
        self.page_edit = QLineEdit()
        self.page_edit.setMinimumWidth(200)
        self.page_edit.setEnabled(True)
        self.page_edit.setPlaceholderText('在当前结果中输入页码筛选')
        self.page_edit.returnPressed.connect(self.filter_by_page)
        self.filter_keypoint = QPushButton("筛选知识点")
        self.filter_keypoint.clicked.connect(self.set_filter)
        top_layout.addWidget(self.page_edit)
        top_layout.addWidget(self.filter_keypoint)
        
        top_layout.addStretch()
        
        # 操作按钮
        top_layout2 = QHBoxLayout()
        top_layout2.setContentsMargins(10, 0, 10, 0)
        top_layout2.setSpacing(10)
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setMaximumWidth(60)
        self.select_all_btn.clicked.connect(self.select_all)
        self.unselect_all_btn = QPushButton("全不选")
        self.unselect_all_btn.setMaximumWidth(60)
        self.unselect_all_btn.clicked.connect(self.unselect_all)
        self.export_btn = QPushButton("导出")
        self.export_btn.setMaximumWidth(60)
        self.export_btn.clicked.connect(self.export_questions)
        self.blank_row_ctl = QSpinBox()
        self.blank_row_ctl.setRange(1, 40)
        self.blank_row_ctl.setValue(10)
        self.blank_row_ctl.setSingleStep(1)
        self.blank_row_ctl.setMinimumWidth(50)
        self.blank_row_ctl.setMinimumHeight(30)
        self.ratio_ctl = QDoubleSpinBox()
        self.ratio_ctl.setRange(0.1, 1.0)
        self.ratio_ctl.setSingleStep(0.01)
        self.ratio_ctl.setDecimals(2)
        self.ratio_ctl.setValue(0.7)
        self.backup_btn = QPushButton("备份")
        self.backup_btn.clicked.connect(self.backup_questions)
        
        top_layout2.addWidget(self.select_all_btn)
        top_layout2.addWidget(self.unselect_all_btn)
        top_layout2.addWidget(QLabel('每题之间空行数:'))
        top_layout2.addWidget(self.blank_row_ctl)
        top_layout2.addWidget(QLabel('题目显示大小比例: '))
        top_layout2.addWidget(self.ratio_ctl)
        top_layout2.addWidget(self.export_btn)
        top_layout2.addWidget(self.backup_btn)
        top_layout2.addStretch()
        
        layout.addLayout(top_layout)
        layout.addLayout(top_layout2)
        
        # 题目列表
        self.list_widget = QListWidget()
        self.list_widget.setResizeMode(QListView.Adjust)
        self.list_widget.setVerticalScrollMode(QListView.ScrollPerPixel)
        self.list_widget.itemChanged.connect(self.on_item_changed)

        scroll_bar = self.list_widget.verticalScrollBar()
        scroll_bar.setSingleStep(13)
        scroll_bar.setPageStep(10)
        
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        
    def update_combo(self):
        # 刷新科目和来源combo
        subject = self.filter_subject.currentText()
        self.filter_source.clear()
        self.filter_source.addItem('全部')
        if subject != '全部' and subject != '':
            self.filter_source.addItems(self.question_data.subject_child[subject])
        self.filter_source.setCurrentText('全部')

    def refresh_questions(self):
        global ALLOW_REFRESH
        if not ALLOW_REFRESH:
            return
        subject = self.filter_subject.currentText()
        source = self.filter_source.currentText()
        IDs = []
        if subject == '全部':
            newesID = GlobalData.NEWEST_ID
            for id in range(1, newesID + 1):
                IDs.append('{:06d}'.format(id))
        else:
            if source != '全部':
                if source in GlobalData.BIND['sources'][subject]:
                    IDs = GlobalData.BIND['sources'][subject][source]
            else:
                sources = GlobalData.BIND['sources'][subject].keys()
                for item in sources:
                    IDs.extend(GlobalData.BIND['sources'][subject][item])
        self.IDs = IDs
        # 清空滚动区域
        self.list_widget.clear()

        # 逐个题目添加进窗口
        for ID in self.IDs:
            item = QListWidgetItem()
            widget = export_page_question.get_widget(self.question_data, ID, self)
            widget.set_list_widget_item(item)
            widget = widget.widget
            item.setCheckState(Qt.Unchecked)
            item.setSizeHint(widget.sizeHint())

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
            if ID in self.selected_questions:
                item.setCheckState(Qt.Checked)

    def refresh_ID_keypoint(self):
        subject = self.filter_subject.currentText()
        if subject != '全部':
            self.ID_keypoint = dict()
            IDs = []
            for source in self.question_data.source_child[subject].keys():
                IDs.extend(self.question_data.source_child[subject][source])
            self.subject_IDs = IDs

            file = self.question_data.MetaData.access_data_file()
            datas = json.load(file)
            self.question_data.MetaData.release_file(file)

            for ID in IDs:
                if ID in datas.keys():
                    self.ID_keypoint[ID] = datas[ID]['keypoint']
        else:
            return

    def filter_by_page(self):
        # access to question data
        file = self.question_data.MetaData.access_data_file()
        datas = json.load(file)
        self.question_data.MetaData.release_file(file)
        # filter by page
        page = self.page_edit.text()
        if page == '':
            self.refresh_questions()
            return
            
        newIDs = []
        for ID in self.IDs:
            if ID in datas.keys() and page in datas[ID]['page']:
                newIDs.append(ID)
        self.IDs = newIDs
        
        # refresh window 
        # 清空滚动区域
        self.list_widget.clear()

        # 逐个题目添加进窗口
        for ID in self.IDs:
            widget = QuestionWidget.get_widget(self.question_data, ID, self)
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def set_filter(self):
        if self.filter_subject.currentText() == '全部':
            msg = QMessageBox()
            msg.setWindowTitle('请选择科目')
            msg.setText('请选择科目后再筛选知识点')
            msg.addButton(QMessageBox.Ok)
            msg.exec()
        else:
            keypoints = self.question_data.keypoint_child[self.filter_subject.currentText()]
            filter_result = keypoints_filter_window.get_filter_result(keypoints) # keypoints
            # 筛选指定知识点
            #self.IDs = filter_result
            newIDs = []
            for ID in self.subject_IDs:
                if ID in self.ID_keypoint.keys():
                    ID_keypoint = self.ID_keypoint[ID]
                    if set(ID_keypoint) & set(filter_result):
                        newIDs.append(ID)
            self.IDs = newIDs

            # refresh window
            # 清空滚动区域
            self.list_widget.clear()

            # 逐个题目添加进窗口
            for ID in self.IDs:
                item = QListWidgetItem()
                widget = export_page_question.get_widget(self.question_data, ID, self)
                widget.set_list_widget_item(item)
                widget = widget.widget
                item.setCheckState(Qt.Unchecked)
                item.setSizeHint(widget.sizeHint())

                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)
                if ID in self.selected_questions:
                    item.setCheckState(Qt.Checked)
            
    def select_all(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Checked)

    def unselect_all(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Unchecked)
    
    def on_item_changed(self, item):
        widget = self.list_widget.itemWidget(item)
        ID_label = widget.findChild(QLabel, 'ID_label')
        if ID_label:
            ID = ID_label.text()
            if item.checkState() == Qt.Checked:
                if ID not in self.selected_questions:
                    self.selected_questions.append(ID)
            else:
                if ID in self.selected_questions:
                    self.selected_questions.remove(ID)
        #print(self.selected_questions)

    def export_questions(self):
        export_dir = QFileDialog.getExistingDirectory(
            None,
            "请选择题目导出位置",
            QDir.homePath(),
            QFileDialog.ShowDirsOnly
        )
        docx = Exporter.DOCX()
        statue, filepath = docx.output(self.IDs, export_dir, self.blank_row_ctl.value(), self.ratio_ctl.value())
        if statue:
            msg = QMessageBox()
            msg.setWindowTitle('导出完成')
            msg.setText(f'导出成功\n文件已经导出至: {filepath}')
            msg.addButton(QMessageBox.Ok)
            msg.exec()
            LOG.write('INFO', '导出题目, ID: {}'.format(' , '.join(self.IDs)))
        else:
            msg = QMessageBox()
            msg.setWindowTitle('导出失败')
            msg.setText(f'导出失败\n发生未知错误, 请检查目标路径有无存取权限')
            msg.addButton(QMessageBox.Ok)
            msg.exec()
            LOG.write('ERROR', '导出失败')
            

        
    
    def backup_questions(self):
        export_dir = QFileDialog.getExistingDirectory(
            None,
            "请选择备份文件导出位置",
            QDir.homePath(),
            QFileDialog.ShowDirsOnly
        )
        
        if not export_dir:  # 用户取消了选择
            return
        
        try:
            status, size = DataManagement.DiskController.backup(export_dir)
            if status:
                QMessageBox.information(
                    None,
                    "备份完成",
                    f"备份已成功保存到:\n{export_dir}\n文件大小: {size}",
                    QMessageBox.Ok
                )
                LOG.write('INFO', '备份文件')
        except Exception:
            LOG.write('ERROR', '备份文件失败')
            

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.question_data = Data()
        self.setup_ui()
        
    def setup_ui(self):
        #self.setWindowTitle("题目管理系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 侧边栏
        self.sidebar = SidebarWidget()
        splitter.addWidget(self.sidebar)
        
        # 内容区域
        self.content_stack = QStackedWidget()
        splitter.addWidget(self.content_stack)
        
        # 页面
        self.editor_page = EditorWidget(self.question_data)
        self.checker_page = CheckerWidget(self.question_data)
        self.exporter_page = ExporterWidget(self.question_data)
        
        self.content_stack.addWidget(self.editor_page)
        self.content_stack.addWidget(self.checker_page)
        self.content_stack.addWidget(self.exporter_page)
        
        # 设置分割器比例
        splitter.setSizes([200, 1000])
        
        # 连接信号
        self.sidebar.editor_btn.clicked.connect(self.switch_0)
        self.sidebar.checker_btn.clicked.connect(self.switch_1)
        self.sidebar.exporter_btn.clicked.connect(self.switch_2)
        self.sidebar.import_btn.clicked.connect(self.import_data)
        
        # 默认显示Editor页面
        self.switch_page(0)
    
    def switch_0(self):
        global ALLOW_REFRESH
        ALLOW_REFRESH = False
        self.switch_page(0)

    def switch_1(self):
        global ALLOW_REFRESH
        ALLOW_REFRESH = True
        self.switch_page(1)
    
    def switch_2(self):
        global ALLOW_REFRESH
        ALLOW_REFRESH = True
        self.switch_page(2)

    def switch_page(self, index):
        self.content_stack.setCurrentIndex(index)
        
        # 更新按钮样式
        buttons = [self.sidebar.editor_btn, self.sidebar.checker_btn, self.sidebar.exporter_btn]
        for i, btn in enumerate(buttons):
            if i == index:
                btn.setStyleSheet(btn.styleSheet() + "background-color: #2980b9;")
            else:
                btn.setStyleSheet(btn.styleSheet().replace("background-color: #2980b9;", ""))
                
        # 刷新页面数据
        if index == 1:
            self.checker_page.refresh_questions()
        elif index == 2:
            self.exporter_page.refresh_questions()
        
        # 同步更新Editor的下拉选项
        if hasattr(self, 'editor_page'):
            #self.editor_page.update_subject_combo()
            #self.editor_page.update_source_combo()
            a=0
        
    def import_data(self):
        rst = ChooseFile.get_folders()
        if rst:
            image_folder, text_folder = rst
            DataManagement.DiskController.import_data(image_folder, text_folder)
            msg = QMessageBox()
            msg.setWindowTitle('导入成功')
            msg.setText('导入成功, 请重启软件')
            msg.addButton(QMessageBox.Ok)
            msg.exec()

def asyn_initial_cache():
    while QApplication.instance() is None:
        sleep(1)
    disk = DataManagement.DiskController()
    thread = threading.Thread(target=disk.asyn_initial_cache)
    thread.start()

def main():
    thread = threading.Thread(target=asyn_initial_cache)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 设置应用样式
    app.setStyleSheet("""
        QWidget {
            font-size: 12px;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            margin: 10px 0;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QComboBox, QLineEdit, QTextEdit {
            border: 1px solid #bdc3c7;
            border-radius: 3px;
            padding: 5px;
            min-height: 20px;
        }
        QComboBox:focus, QLineEdit:focus, QTextEdit:focus {
            border-color: #3498db;
        }
    """)
    
    window = MainWindow()
    window.show()

    thread.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    pass