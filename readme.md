# 错题管理 Exam Mistakes Management​

* 本项目的PySide6框架部分使用了AI辅助编程 *

## 功能
 - 录入错题: 题目目前只允许以图片形式录入
 - 编辑: 允许编辑已录入的错题
 - 导出: 允许筛选错题并导出为docx

## 依赖库
 - PySide6
 - python-docx

## 开发环境
 - Python 3.12.9
 - macOS Sequoia 15.5

## 文件结构
```
src/
├── main.py                   # 主程序
├── DataManagement.py         # 磁盘交互
├── Exporter.py               # docx文件导出
├── GlobalData.py             # 类间共用变量
├── LogManagement.py          # 日志管理
├── question_manager_app.py   # PySide界面
└── docxdemo.py               # python-docx使用demo
release.sh                    # Nuitka发布脚本
```

## Nuitka使用 (AI生成)
 - 如果你使用macOS, 不需要更改release.sh
 - 如果你使用LinuxWindows, 请遵照以下修改.
 - Linux:
 - 删除该行 ```--macos-create-app-bundle \```
 - 删除该行 ```--macos-app-name=QuestionManager \```
 - Windows:
 - 删除该行 ```--macos-create-app-bundle \```
 - 删除该行 ```--macos-app-name=QuestionManager \```
 - 该行 ```--disable-console \ ``` 更改为 ```--windows-disable-console \ ```


Tips: 这个软件是作者为了方便复习开发的, 希望能够帮助到同样有需要的你!
