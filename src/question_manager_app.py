import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QSplitter, QPushButton, QStackedWidget,
                               QLabel, QComboBox, QLineEdit, QTextEdit, QScrollArea,
                               QFrame, QCheckBox, QSpinBox, QFileDialog, QMessageBox,
                               QGridLayout, QSizePolicy, QGroupBox, QInputDialog, QLayout, QListWidget,
                               QListWidgetItem)
from PySide6.QtCore import Qt, QDateTime, QSize
from PySide6.QtGui import QPixmap, QFont, QFontMetrics
import json
import os
from datetime import datetime

import DataManagement, GlobalData

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
        if 'source' in GlobalData.BIND.keys():
            # source & ID
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
        source_keys = self.source_child.keys()
        if source not in source_keys:
            self.source_child[source] = []
        if source not in self.subject_child[subject]:
            self.subject_child[subject].append(source)
        if ID not in  self.source_child[source]:
            self.source_child[source].append(ID)
            self.MetaData.add_bind('ID', [source, ID])

        # add question data: ID and index    
        question_keys = self.questions.keys()
        if subject not in question_keys:
            self.questions[subject] = []
        self.questions[subject].append((ID, index))

    def del_question(self, question_data):
        # delete bind of source & ID
        pass
        
    def get_questions(self, subject=None, source=None):
        filtered = self.questions
        if subject and subject != "全部":
            filtered = [q for q in filtered if q.get('subject') == subject]
        if source and source != "全部":
            filtered = [q for q in filtered if q.get('source') == source]
        return sorted(filtered, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def add_subject(self, subject):
        if subject and not self.MetaData.if_in('subjects', subject):
            self.MetaData.add_subject(subject)
            self.update_metadata()
            return True
        return False
    
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
        print(GlobalData.BIND)
    
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
        
        layout.addWidget(self.editor_btn)
        layout.addWidget(self.checker_btn)
        layout.addWidget(self.exporter_btn)
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
        new_source_layout = QVBoxLayout()
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
        new_source_layout.addWidget(source_layout_widget)
        
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

        new_source_layout.addWidget(from_widget)
        source_group.setLayout(new_source_layout)
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
        
        self.answer_edit = QTextEdit()
        self.answer_edit.setPlaceholderText("请输入答案...")
        self.answer_edit.setMaximumHeight(250)

        answer_layout.addWidget(self.answer_edit)
        answer_group.setLayout(answer_layout)

        # 备注
        notice_group = QWidget()
        notice_layout = QVBoxLayout()
        notice_layout.setContentsMargins(0, 0, 0, 0)

        notice_label = QLabel('备注')
        self.notice_edit = QTextEdit()
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
        text, ok = QInputDialog.getText(
            None,
            '请输入知识点',
            '请输入内容')
        if text and ok :
            content = text
        else:
            return 
        item = QListWidgetItem()
        widget = QWidget()
        itemlayout = QHBoxLayout()
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
        self.question_data.del_keypoints(subject, content)
            
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
        ID = self.datamanage.newID()
        subject = self.subject_combo.currentText()
        source = self.source_combo.currentText()
        page = self.page_edit.text()
        mark = self.mark_combo.currentText()
        number = self.number_edit.text()
        image = self.image
        keypoints = []
        answer = self.answer_edit.toPlainText()
        notice = self.notice_edit.toPlainText()

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
            'notice': notice, # 新增输入备注notice的plainTextEdit
            'answer': answer,
            'errortimes': 1,
            'ratio': 0.0,
            'blankrow': 1
            }
        
        self.disk.write_questions(image, question_data)
        self.question_data.add_question(question_data)
        QMessageBox.information(self, "成功", "题目已保存!")
        
        # 清空表单
        #self.page_edit.clear()
        self.number_edit.clear()
        self.answer_edit.clear()
        self.notice_edit.clear()
        self.clear_image()
        self.keypoints_list.clear()

class CheckerWidget(QWidget):
    def __init__(self, question_data, parent=None):
        super().__init__(parent)
        self.question_data = question_data
        self.setup_ui()
        #self.refresh_questions()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("题目查看器")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 筛选条件
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("科目:"))
        
        self.filter_subject = QComboBox()
        self.filter_subject.addItem("全部")
        self.filter_subject.addItems(self.question_data.subjects)
        self.filter_subject.currentTextChanged.connect(self.refresh_questions)
        filter_layout.addWidget(self.filter_subject)
        
        filter_layout.addWidget(QLabel("书籍:"))
        self.filter_source = QComboBox()
        self.filter_source.addItem("全部")
        self.filter_source.addItems(self.question_data.sources)
        self.filter_source.currentTextChanged.connect(self.refresh_questions)
        filter_layout.addWidget(self.filter_source)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 题目列表
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)
        
    def refresh_questions(self):
        # 清空现有内容
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)
            
        # 更新筛选选项
        self.update_filter_options()
            
        # 获取筛选后的题目
        questions = self.question_data.get_questions(
            self.filter_subject.currentText(),
            self.filter_source.currentText()
        )
        
        # 显示题目
        for i, question in enumerate(questions):
            question_widget = self.create_question_widget(question, i + 1)
            self.scroll_layout.addWidget(question_widget)
            
        self.scroll_layout.addStretch()
        
    def update_filter_options(self):
        """更新筛选选项，与问题数据保持同步"""
        # 更新科目筛选
        current_subject = self.filter_subject.currentText()
        self.filter_subject.clear()
        self.filter_subject.addItem("全部")
        self.filter_subject.addItems(self.question_data.subjects)
        if current_subject in self.question_data.subjects or current_subject == "全部":
            self.filter_subject.setCurrentText(current_subject)
            
        # 更新书籍筛选
        current_source = self.filter_source.currentText()
        self.filter_source.clear()
        self.filter_source.addItem("全部")
        self.filter_source.addItems(self.question_data.sources)
        if current_source in self.question_data.sources or current_source == "全部":
            self.filter_source.setCurrentText(current_source)
        
    def create_question_widget(self, question, index):
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setStyleSheet("QFrame { border: 1px solid #bdc3c7; border-radius: 5px; padding: 10px; margin: 5px; }")
        
        layout = QVBoxLayout()
        
        # 题目信息
        info_text = f"第{index}题 - {question.get('subject', '')} - {question.get('source', '')} - 第{question.get('page', '')}页 - {question.get('type', '')} - {question.get('mark', '')}{question.get('number', '')}"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(info_label)
        
        # 答案
        if question.get('answer'):
            answer_label = QLabel(f"答案: {question['answer']}")
            answer_label.setWordWrap(True)
            layout.addWidget(answer_label)
            
        # 时间
        if question.get('timestamp'):
            time_str = datetime.fromisoformat(question['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            time_label = QLabel(f"创建时间: {time_str}")
            time_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            layout.addWidget(time_label)
            
        widget.setLayout(layout)
        return widget

class ExporterWidget(QWidget):
    def __init__(self, question_data, parent=None):
        super().__init__(parent)
        self.question_data = question_data
        self.selected_questions = set()
        self.setup_ui()
        #self.refresh_questions()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("题目导出器")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 筛选和操作栏
        top_layout = QHBoxLayout()
        
        # 筛选
        top_layout.addWidget(QLabel("筛选:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("全部")
        self.filter_combo.addItems(self.question_data.subjects)
        self.filter_combo.currentTextChanged.connect(self.refresh_questions)
        top_layout.addWidget(self.filter_combo)
        
        top_layout.addWidget(QLabel("书籍:"))
        self.source_filter = QComboBox()
        self.source_filter.addItem("全部")
        self.source_filter.addItems(self.question_data.sources)
        self.source_filter.currentTextChanged.connect(self.refresh_questions)
        top_layout.addWidget(self.source_filter)
        
        top_layout.addStretch()
        
        # 操作按钮
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all)
        self.preview_btn = QPushButton("预览")
        self.preview_btn.clicked.connect(self.preview_export)
        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export_questions)
        
        top_layout.addWidget(self.select_all_btn)
        top_layout.addWidget(self.preview_btn)
        top_layout.addWidget(self.export_btn)
        
        layout.addLayout(top_layout)
        
        # 题目列表
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)
        
    def refresh_questions(self):
        # 清空现有内容
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)
            
        self.selected_questions.clear()
        
        # 更新书籍筛选选项
        current_source = self.source_filter.currentText()
        self.source_filter.clear()
        self.source_filter.addItem("全部")
        self.source_filter.addItems(self.question_data.sources)
        if current_source in self.question_data.sources or current_source == "全部":
            self.source_filter.setCurrentText(current_source)
            
        # 获取筛选后的题目
        questions = self.question_data.get_questions(
            self.filter_combo.currentText(),
            self.source_filter.currentText()
        )
        
        # 显示题目
        for i, question in enumerate(questions):
            question_widget = self.create_export_question_widget(question, i)
            self.scroll_layout.addWidget(question_widget)
            
        self.scroll_layout.addStretch()
        
    def create_export_question_widget(self, question, index):
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setStyleSheet("QFrame { border: 1px solid #bdc3c7; border-radius: 5px; padding: 10px; margin: 5px; }")
        
        layout = QHBoxLayout()
        
        # 左侧选择框
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(lambda state, idx=index: self.toggle_question_selection(idx, state))
        layout.addWidget(checkbox)
        
        # 中部题目信息
        info_layout = QVBoxLayout()
        
        # 题目来源
        source_text = f"{question.get('subject', '')} - {question.get('source', '')} - 第{question.get('page', '')}页"
        source_label = QLabel(source_text)
        source_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        info_layout.addWidget(source_label)
        
        # 题目详情
        detail_text = f"{question.get('type', '')} - {question.get('mark', '')}{question.get('number', '')}"
        if question.get('answer'):
            detail_text += f" | 答案: {question['answer'][:50]}{'...' if len(question.get('answer', '')) > 50 else ''}"
        detail_label = QLabel(detail_text)
        detail_label.setWordWrap(True)
        info_layout.addWidget(detail_label)
        
        layout.addLayout(info_layout)
        
        # 右侧缩放比例
        scale_layout = QVBoxLayout()
        scale_layout.addWidget(QLabel("缩放比例:"))
        scale_spin = QSpinBox()
        scale_spin.setRange(10, 200)
        scale_spin.setValue(100)
        scale_spin.setSuffix("%")
        scale_layout.addWidget(scale_spin)
        
        layout.addLayout(scale_layout)
        
        widget.setLayout(layout)
        return widget
        
    def toggle_question_selection(self, index, state):
        if state == Qt.Checked:
            self.selected_questions.add(index)
        else:
            self.selected_questions.discard(index)
            
    def select_all(self):
        # 切换全选状态
        total_questions = self.scroll_layout.count() - 1  # 减去stretch
        if len(self.selected_questions) == total_questions:
            # 当前全选，则取消全选
            self.selected_questions.clear()
            for i in range(total_questions):
                widget = self.scroll_layout.itemAt(i).widget()
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
        else:
            # 全选
            self.selected_questions = set(range(total_questions))
            for i in range(total_questions):
                widget = self.scroll_layout.itemAt(i).widget()
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
                    
    def preview_export(self):
        if not self.selected_questions:
            QMessageBox.warning(self, "警告", "请先选择要预览的题目!")
            return
        QMessageBox.information(self, "预览", f"已选择 {len(self.selected_questions)} 道题目进行预览")
        
    def export_questions(self):
        if not self.selected_questions:
            QMessageBox.warning(self, "警告", "请先选择要导出的题目!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出题目", "", "LaTeX文件 (*.tex);;PDF文件 (*.pdf)")
        
        if file_path:
            # 这里应该实现实际的导出逻辑
            QMessageBox.information(self, "导出成功", f"已导出 {len(self.selected_questions)} 道题目到 {file_path}")

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
        self.sidebar.editor_btn.clicked.connect(lambda: self.switch_page(0))
        self.sidebar.checker_btn.clicked.connect(lambda: self.switch_page(1))
        self.sidebar.exporter_btn.clicked.connect(lambda: self.switch_page(2))
        
        # 默认显示Editor页面
        self.switch_page(0)
        
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

def main():
    app = QApplication(sys.argv)
    
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
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()