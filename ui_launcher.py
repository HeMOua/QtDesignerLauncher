#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6界面设计器启动器
主界面类
"""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QPushButton, QLabel, QLineEdit,
                             QFileDialog, QTextEdit, QGroupBox, QProgressBar,
                             QMessageBox, QStatusBar, QFrame, QSplitter,
                             QCheckBox, QMenuBar, QMenu)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QPixmap, QAction
from utils import (find_designer_path, convert_ui_to_py, test_designer_executable,
                   save_config, load_config, get_system_info, check_pyqt6_installation)

logger = logging.getLogger(__name__)


class ConvertThread(QThread):
    """UI转换线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, ui_file, output_dir):
        super().__init__()
        self.ui_file = ui_file
        self.output_dir = output_dir

    def run(self):
        try:
            logger.info(f"转换线程启动: {self.ui_file}")
            self.progress.emit("开始转换...")
            success, message = convert_ui_to_py(self.ui_file, self.output_dir)
            self.finished.emit(success, message)
        except Exception as e:
            logger.error(f"转换线程异常: {str(e)}", exc_info=True)
            self.finished.emit(False, f"转换过程中发生错误: {str(e)}")


class DesignerLauncher(QMainWindow):
    """PyQt6界面设计器启动器主窗口"""

    def __init__(self):
        super().__init__()
        logger.info("初始化主窗口")

        self.designer_path = None
        self.convert_thread = None
        self.config = load_config()

        try:
            self.init_ui()
            self.init_menu()
            self.init_designer_path()
            logger.info("主窗口初始化完成")
        except Exception as e:
            logger.error(f"主窗口初始化失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "初始化错误", f"主窗口初始化失败:\n{str(e)}")

    def init_menu(self):
        """初始化菜单栏"""
        try:
            menubar = self.menuBar()

            # 帮助菜单
            help_menu = menubar.addMenu('帮助(&H)')

            # 系统信息
            system_info_action = QAction('系统信息(&S)', self)
            system_info_action.triggered.connect(self.show_system_info)
            help_menu.addAction(system_info_action)

            # 查看日志
            view_log_action = QAction('查看日志(&L)', self)
            view_log_action.triggered.connect(self.view_log)
            help_menu.addAction(view_log_action)

            help_menu.addSeparator()

            # 关于
            about_action = QAction('关于(&A)', self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)

        except Exception as e:
            logger.error(f"菜单初始化失败: {str(e)}")

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("PyQt6界面设计器启动器 v1.0.1")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 创建标题
        title_label = QLabel("PyQt6界面设计器启动器")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                margin: 10px 0;
                background-color: transparent;
            }
        """)
        main_layout.addWidget(title_label)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)

        # Qt Designer 启动区域
        designer_group = self.create_designer_group()
        splitter.addWidget(designer_group)

        # UI转换区域
        convert_group = self.create_convert_group()
        splitter.addWidget(convert_group)

        # 设置分割器比例
        splitter.setSizes([200, 400])

        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")

    def create_designer_group(self):
        """创建Qt Designer启动组"""
        group = QGroupBox("Qt Designer 启动器")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # Designer路径显示
        path_layout = QHBoxLayout()
        path_label = QLabel("Designer路径:")
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("正在检测Qt Designer路径...")

        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_designer_path)
        browse_btn.setMaximumWidth(80)

        test_btn = QPushButton("测试")
        test_btn.clicked.connect(self.test_designer_path)
        test_btn.setMaximumWidth(60)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        path_layout.addWidget(test_btn)
        layout.addLayout(path_layout)

        # 自动检测复选框
        self.auto_detect_cb = QCheckBox("启动时自动检测Designer路径")
        self.auto_detect_cb.setChecked(self.config.get('auto_detect', True))
        self.auto_detect_cb.stateChanged.connect(self.save_settings)
        layout.addWidget(self.auto_detect_cb)

        # 启动按钮
        button_layout = QHBoxLayout()
        self.launch_btn = QPushButton("🎨 启动 Qt Designer")
        self.launch_btn.clicked.connect(self.launch_designer)
        self.launch_btn.setEnabled(False)
        self.launch_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 12px 24px;
                background-color: #27ae60;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(self.launch_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        return group

    def create_convert_group(self):
        """创建UI转换组"""
        group = QGroupBox("UI文件转换器")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # 文件选择区域
        file_layout = QGridLayout()

        # UI文件选择
        ui_label = QLabel("UI文件:")
        self.ui_file_edit = QLineEdit()
        self.ui_file_edit.setPlaceholderText("选择要转换的.ui文件")
        ui_browse_btn = QPushButton("选择文件")
        ui_browse_btn.clicked.connect(self.browse_ui_file)

        file_layout.addWidget(ui_label, 0, 0)
        file_layout.addWidget(self.ui_file_edit, 0, 1)
        file_layout.addWidget(ui_browse_btn, 0, 2)

        # 输出目录选择
        output_label = QLabel("输出目录:")
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录（默认为UI文件同目录）")
        output_browse_btn = QPushButton("选择目录")
        output_browse_btn.clicked.connect(self.browse_output_dir)

        file_layout.addWidget(output_label, 1, 0)
        file_layout.addWidget(self.output_dir_edit, 1, 1)
        file_layout.addWidget(output_browse_btn, 1, 2)

        layout.addLayout(file_layout)

        # 转换按钮
        convert_layout = QHBoxLayout()
        self.convert_btn = QPushButton("🔄 转换为Python文件")
        self.convert_btn.clicked.connect(self.convert_ui_file)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
                background-color: #e74c3c;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)

        convert_layout.addStretch()
        convert_layout.addWidget(self.convert_btn)
        convert_layout.addStretch()
        layout.addLayout(convert_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 输出信息
        self.output_text = QTextEdit()
        self.output_text.setPlaceholderText("转换信息将在这里显示...")
        layout.addWidget(self.output_text)

        return group

    def init_designer_path(self):
        """初始化Designer路径"""
        if self.auto_detect_cb.isChecked():
            QTimer.singleShot(100, self.detect_designer_path)
        else:
            # 尝试从配置加载
            saved_path = self.config.get('designer_path')
            if saved_path and os.path.exists(saved_path):
                self.designer_path = saved_path
                self.path_edit.setText(saved_path)
                self.launch_btn.setEnabled(True)
                self.statusBar.showMessage("已加载保存的Designer路径")

    def detect_designer_path(self):
        """检测Designer路径"""
        try:
            self.statusBar.showMessage("正在检测Qt Designer路径...")
            self.output_text.append("🔍 开始检测Qt Designer路径...")

            path = find_designer_path()

            if path:
                self.designer_path = path
                self.path_edit.setText(path)
                self.path_edit.setStyleSheet("")
                self.launch_btn.setEnabled(True)
                self.statusBar.showMessage("Qt Designer路径检测成功")
                self.output_text.append(f"✅ Qt Designer检测成功: {path}")
            else:
                self.path_edit.setText("未找到Qt Designer")
                self.path_edit.setStyleSheet("QLineEdit { color: #e74c3c; }")
                self.statusBar.showMessage("未找到Qt Designer，请手动指定路径")
                self.output_text.append("❌ 未找到Qt Designer，请手动指定路径")

        except Exception as e:
            logger.error(f"Designer路径检测失败: {str(e)}", exc_info=True)
            self.output_text.append(f"❌ Designer路径检测失败: {str(e)}")

    def test_designer_path(self):
        """测试Designer路径"""
        if not self.designer_path:
            QMessageBox.warning(self, "警告", "请先选择Designer路径！")
            return

        try:
            self.statusBar.showMessage("正在测试Designer路径...")
            if test_designer_executable(self.designer_path):
                QMessageBox.information(self, "测试成功", "Designer路径有效！")
                self.output_text.append(f"✅ Designer路径测试成功: {self.designer_path}")
            else:
                QMessageBox.warning(self, "测试失败", "Designer路径无效或无法执行！")
                self.output_text.append(f"❌ Designer路径测试失败: {self.designer_path}")
        except Exception as e:
            logger.error(f"Designer路径测试异常: {str(e)}")
            QMessageBox.critical(self, "测试错误", f"测试过程中发生错误:\n{str(e)}")

    def save_settings(self):
        """保存设置"""
        try:
            self.config['auto_detect'] = self.auto_detect_cb.isChecked()
            if self.designer_path:
                self.config['designer_path'] = self.designer_path
            save_config(self.config)
        except Exception as e:
            logger.error(f"保存设置失败: {str(e)}")

    def browse_designer_path(self):
        """浏览Designer路径"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择Qt Designer执行文件",
                "",
                "可执行文件 (*.exe);;所有文件 (*.*)" if platform.system() == "Windows" else "所有文件 (*.*)"
            )

            if file_path:
                self.designer_path = file_path
                self.path_edit.setText(file_path)
                self.path_edit.setStyleSheet("")
                self.launch_btn.setEnabled(True)
                self.save_settings()
                self.output_text.append(f"📁 已选择Designer路径: {file_path}")
        except Exception as e:
            logger.error(f"浏览Designer路径失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"选择文件时发生错误:\n{str(e)}")

    def launch_designer(self):
        """启动Qt Designer"""
        if not self.designer_path or not os.path.exists(self.designer_path):
            QMessageBox.warning(self, "错误", "Qt Designer路径无效！")
            return

        try:
            logger.info(f"启动Designer: {self.designer_path}")
            subprocess.Popen([self.designer_path], cwd=os.path.dirname(self.designer_path))
            self.statusBar.showMessage("Qt Designer已启动")
            self.output_text.append(f"✅ Qt Designer已成功启动: {self.designer_path}")
        except Exception as e:
            logger.error(f"启动Designer失败: {str(e)}")
            QMessageBox.critical(self, "启动失败", f"无法启动Qt Designer:\n{str(e)}")
            self.statusBar.showMessage("Qt Designer启动失败")
            self.output_text.append(f"❌ Qt Designer启动失败: {str(e)}")

    def browse_ui_file(self):
        """浏览UI文件"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择UI文件",
                "",
                "Qt UI文件 (*.ui);;所有文件 (*.*)"
            )

            if file_path:
                self.ui_file_edit.setText(file_path)
                # 自动设置输出目录为UI文件所在目录
                if not self.output_dir_edit.text():
                    self.output_dir_edit.setText(os.path.dirname(file_path))
                self.output_text.append(f"📁 已选择UI文件: {file_path}")
        except Exception as e:
            logger.error(f"浏览UI文件失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"选择文件时发生错误:\n{str(e)}")

    def browse_output_dir(self):
        """浏览输出目录"""
        try:
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "选择输出目录"
            )

            if dir_path:
                self.output_dir_edit.setText(dir_path)
                self.output_text.append(f"📁 已选择输出目录: {dir_path}")
        except Exception as e:
            logger.error(f"浏览输出目录失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"选择目录时发生错误:\n{str(e)}")

    def convert_ui_file(self):
        """转换UI文件"""
        try:
            ui_file = self.ui_file_edit.text().strip()
            output_dir = self.output_dir_edit.text().strip()

            if not ui_file:
                QMessageBox.warning(self, "警告", "请选择要转换的UI文件！")
                return

            if not os.path.exists(ui_file):
                QMessageBox.warning(self, "警告", "UI文件不存在！")
                return

            if not output_dir:
                output_dir = os.path.dirname(ui_file)
                self.output_dir_edit.setText(output_dir)

            # 禁用转换按钮，显示进度条
            self.convert_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 无限进度条

            # 清空输出文本
            self.output_text.clear()

            # 启动转换线程
            self.convert_thread = ConvertThread(ui_file, output_dir)
            self.convert_thread.progress.connect(self.on_convert_progress)
            self.convert_thread.finished.connect(self.on_convert_finished)
            self.convert_thread.start()

        except Exception as e:
            logger.error(f"转换UI文件失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "转换错误", f"启动转换时发生错误:\n{str(e)}")
            self.convert_btn.setEnabled(True)
            self.progress_bar.setVisible(False)

    def on_convert_progress(self, message):
        """转换进度更新"""
        self.output_text.append(f"⏳ {message}")
        self.statusBar.showMessage(message)

    def on_convert_finished(self, success, message):
        """转换完成"""
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.output_text.append(f"✅ {message}")
            self.statusBar.showMessage("转换完成")
            QMessageBox.information(self, "成功", message)
        else:
            self.output_text.append(f"❌ {message}")
            self.statusBar.showMessage("转换失败")
            QMessageBox.critical(self, "转换失败", message)

    def show_system_info(self):
        """显示系统信息"""
        try:
            info = get_system_info()
            pyqt_status, pyqt_version = check_pyqt6_installation()

            info_text = f"""系统信息:
操作系统: {info['system']} {info['version']}
Python版本: {info['python']}
系统架构: {info['architecture']}
运行环境: {'PyInstaller打包' if info['frozen'] else '开发环境'}
可执行文件: {info['executable']}

PyQt6状态: {'已安装' if pyqt_status else '未安装'}
PyQt6版本: {pyqt_version if pyqt_version else 'N/A'}

Designer路径: {self.designer_path if self.designer_path else '未设置'}
"""

            QMessageBox.information(self, "系统信息", info_text)
        except Exception as e:
            logger.error(f"显示系统信息失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"获取系统信息失败:\n{str(e)}")

    def view_log(self):
        """查看日志"""
        try:
            from utils import get_app_data_dir
            log_file = get_app_data_dir() / "launcher.log"

            if log_file.exists():
                # 尝试用系统默认程序打开日志文件
                if platform.system() == "Windows":
                    os.startfile(str(log_file))
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(log_file)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(log_file)])
            else:
                QMessageBox.information(self, "提示", "日志文件不存在")
        except Exception as e:
            logger.error(f"查看日志失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"打开日志文件失败:\n{str(e)}")

    def show_about(self):
        """显示关于信息"""
        about_text = """PyQt6界面设计器启动器 v1.0.1

一个简单易用的PyQt6界面设计器启动工具

功能特性:
• 启动Qt Designer
• UI文件转换为Python代码
• 中文界面
• 自动路径检测

作者: HeMOua
GitHub: https://github.com/HeMOua/pyqt-designer-launcher

基于PyQt6开发
"""
        QMessageBox.about(self, "关于", about_text)

    def closeEvent(self, event):
        """关闭事件"""
        try:
            self.save_settings()
            logger.info("程序正常关闭")
            event.accept()
        except Exception as e:
            logger.error(f"关闭事件处理失败: {str(e)}")
            event.accept()