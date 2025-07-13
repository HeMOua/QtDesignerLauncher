#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6界面设计器启动器
主程序入口
"""

import sys
import os
import logging
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui_launcher import DesignerLauncher

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "icon.png")  # 或 .ico


def setup_logging():
    """设置日志记录"""
    # 获取程序运行目录
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的环境
        app_dir = Path(sys.executable).parent
    else:
        # 开发环境
        app_dir = Path(__file__).parent

    log_file = app_dir / "launcher.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 忽略键盘中断
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # 记录异常到日志
    logger = logging.getLogger(__name__)
    logger.error("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))

    # 显示用户友好的错误信息
    error_msg = f"""程序发生错误，请查看日志文件获取详细信息。

错误类型: {exc_type.__name__}
错误信息: {str(exc_value)}

日志文件位置: {Path(sys.executable if getattr(sys, 'frozen', False) else __file__).parent / 'launcher.log'}
"""

    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        QMessageBox.critical(None, "程序错误", error_msg)
    except:
        # 如果Qt界面也无法显示，直接打印到控制台
        print(error_msg)


def main():
    """主函数"""
    # 设置日志记录
    logger = setup_logging()
    logger.info("程序启动")

    # 设置全局异常处理器
    sys.excepthook = handle_exception

    try:
        app = QApplication(sys.argv)

        # 设置应用程序信息
        app.setApplicationName("PyQt6界面设计器启动器")
        app.setApplicationVersion("1.0.1")
        app.setOrganizationName("HeMOua")

        # 设置窗口图标
        app.setWindowIcon(QIcon(ICON_PATH))

        # 记录运行环境信息
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"运行环境: {'PyInstaller打包' if getattr(sys, 'frozen', False) else '开发环境'}")
        logger.info(f"程序路径: {sys.executable if getattr(sys, 'frozen', False) else __file__}")

        # 创建主窗口
        window = DesignerLauncher()
        window.show()

        logger.info("主窗口已显示")

        # 运行应用程序
        exit_code = app.exec()
        logger.info(f"程序退出，退出码: {exit_code}")
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"主函数发生异常: {str(e)}", exc_info=True)
        try:
            QMessageBox.critical(None, "启动错误", f"程序启动失败:\n{str(e)}")
        except:
            print(f"程序启动失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
