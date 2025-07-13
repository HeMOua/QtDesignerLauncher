#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import os
import sys
import platform
import subprocess
import logging
import json
from pathlib import Path
from PyQt6.QtCore import QStandardPaths

logger = logging.getLogger(__name__)


def get_app_data_dir():
    """获取应用程序数据目录"""
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的环境
        app_dir = Path(sys.executable).parent
    else:
        # 开发环境
        app_dir = Path(__file__).parent

    return app_dir


def get_config_file():
    """获取配置文件路径"""
    config_dir = get_app_data_dir()
    return config_dir / "config.json"


def save_config(config_data):
    """保存配置"""
    try:
        config_file = get_config_file()
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        logger.info(f"配置已保存到: {config_file}")
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")


def load_config():
    """加载配置"""
    try:
        config_file = get_config_file()
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"配置已加载: {config_file}")
            return config
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}")

    return {}


def is_pyinstaller_environment():
    """检测是否为PyInstaller打包环境"""
    return getattr(sys, 'frozen', False)


def find_designer_path():
    """查找Qt Designer路径"""
    logger.info("开始检测Qt Designer路径")

    # 首先尝试从配置文件加载
    config = load_config()
    saved_path = config.get('designer_path')
    if saved_path and os.path.exists(saved_path):
        logger.info(f"从配置文件加载Designer路径: {saved_path}")
        return saved_path

    system = platform.system()
    logger.info(f"操作系统: {system}")
    logger.info(f"运行环境: {'PyInstaller打包' if is_pyinstaller_environment() else '开发环境'}")

    # 检测策略列表
    detection_strategies = [
        _check_path_designer,
        _check_common_paths_designer,
        _check_python_site_packages,
    ]

    for strategy in detection_strategies:
        try:
            path = strategy()
            if path:
                logger.info(f"通过 {strategy.__name__} 找到Designer: {path}")
                # 保存到配置文件
                config['designer_path'] = path
                save_config(config)
                return path
        except Exception as e:
            logger.warning(f"{strategy.__name__} 检测失败: {str(e)}")

    logger.warning("未找到Qt Designer")
    return None


def _check_path_designer():
    """检查PATH环境变量中的designer"""
    logger.debug("检查PATH环境变量中的designer")

    try:
        if platform.system() == "Windows":
            result = subprocess.run(["where", "designer"],
                                    capture_output=True, text=True, check=True, timeout=10)
        else:
            result = subprocess.run(["which", "designer"],
                                    capture_output=True, text=True, check=True, timeout=10)

        if result.stdout.strip():
            path = result.stdout.strip().split('\n')[0]
            if os.path.exists(path):
                return path

    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.debug(f"PATH检查失败: {str(e)}")

    return None


def _check_common_paths_designer():
    """检查常见安装路径"""
    logger.debug("检查常见安装路径")

    system = platform.system()

    if system == "Windows":
        common_paths = [
            r"C:\Qt\*\mingw*\bin\designer.exe",
            r"C:\Qt\*\msvc*\bin\designer.exe",
            r"C:\Qt\Tools\QtCreator\bin\designer.exe",
            r"C:\Program Files\Qt\*\mingw*\bin\designer.exe",
            r"C:\Program Files\Qt\*\msvc*\bin\designer.exe",
            r".\Qt\bin\designer.exe",
            r"..\Qt\bin\designer.exe"
        ]
    elif system == "Darwin":  # macOS
        common_paths = [
            "/usr/local/bin/designer",
            "/opt/homebrew/bin/designer",
            "/Applications/Qt*/*/clang_64/bin/designer",
            "/usr/local/Qt*/*/clang_64/bin/designer",
        ]
    else:  # Linux
        common_paths = [
            "/usr/bin/designer",
            "/usr/local/bin/designer",
            "/opt/Qt*/*/gcc_64/bin/designer",
            "/usr/lib/qt6/bin/designer",
            "/usr/lib/x86_64-linux-gnu/qt6/bin/designer",
        ]

    # 扩展通配符路径
    expanded_paths = []
    for path_pattern in common_paths:
        if '*' in path_pattern:
            try:
                import glob
                expanded = glob.glob(path_pattern)
                expanded_paths.extend(expanded)
            except Exception as e:
                logger.debug(f"通配符扩展失败 {path_pattern}: {str(e)}")
        else:
            expanded_paths.append(path_pattern)

    # 检查每个路径
    for path in expanded_paths:
        if os.path.exists(path):
            return path

    return None


def _check_python_site_packages():
    """检查Python site-packages中的designer"""
    logger.debug("检查Python site-packages中的designer")

    try:
        import site
        site_packages = site.getsitepackages()

        for site_pkg in site_packages:
            site_path = Path(site_pkg)

            # 检查qt6_applications
            qt_apps_path = site_path / "qt6_applications" / "Qt" / "bin"
            if platform.system() == "Windows":
                designer_path = qt_apps_path / "designer.exe"
            else:
                designer_path = qt_apps_path / "designer"

            if designer_path.exists():
                return str(designer_path)

    except Exception as e:
        logger.debug(f"site-packages检查失败: {str(e)}")

    return None


def test_designer_executable(designer_path):
    """测试Designer可执行文件是否有效"""
    try:
        logger.debug(f"测试Designer可执行文件: {designer_path}")
        result = subprocess.run([designer_path, "-h"],
                                capture_output=True, text=True,
                                timeout=10, check=True)
        logger.debug(f"Designer版本信息: {result.stdout}")
        return True
    except Exception as e:
        logger.warning(f"Designer测试失败: {str(e)}")
        return False


def convert_ui_to_py(ui_file, output_dir):
    """将UI文件转换为Python文件"""
    logger.info(f"开始转换UI文件: {ui_file}")

    try:
        # 获取UI文件名（不含扩展名）
        ui_filename = Path(ui_file).stem
        py_filename = f"{ui_filename}.py"
        output_file = Path(output_dir) / py_filename

        logger.info(f"输出文件: {output_file}")

        # 构建pyuic6命令
        if is_pyinstaller_environment():
            # 在打包环境中，尝试直接使用pyuic6模块
            try:
                from PyQt6.uic import compileUi
                with open(ui_file, 'r', encoding='utf-8') as ui_f:
                    with open(output_file, 'w', encoding='utf-8') as py_f:
                        compileUi(ui_f, py_f, execute=True)

                if output_file.exists():
                    logger.info("UI转换成功 (使用compileUi)")
                    return True, f"转换成功！\nUI文件: {ui_file}\nPython文件: {output_file}"

            except Exception as e:
                logger.warning(f"compileUi转换失败: {str(e)}")

        # 标准命令行方式
        cmd = [
            sys.executable, "-m", "PyQt6.uic.pyuic",
            "-x",  # 生成额外的测试代码
            ui_file,
            "-o", str(output_file)
        ]

        logger.debug(f"执行命令: {' '.join(cmd)}")

        # 执行转换
        result = subprocess.run(cmd, capture_output=True, text=True,
                                check=True, timeout=30)

        # 检查输出文件是否创建成功
        if output_file.exists():
            logger.info("UI转换成功")
            return True, f"转换成功！\nUI文件: {ui_file}\nPython文件: {output_file}"
        else:
            logger.error("转换失败：输出文件未创建")
            return False, "转换失败：输出文件未创建"

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        logger.error(f"转换失败: {error_msg}")
        return False, f"转换失败：{error_msg}"
    except subprocess.TimeoutExpired:
        logger.error("转换超时")
        return False, "转换超时，请检查UI文件是否有效"
    except Exception as e:
        logger.error(f"转换过程中发生错误: {str(e)}", exc_info=True)
        return False, f"转换过程中发生错误：{str(e)}"


def check_pyqt6_installation():
    """检查PyQt6是否已安装"""
    try:
        import PyQt6
        logger.info(f"PyQt6版本: {PyQt6.QtCore.PYQT_VERSION_STR}")
        return True, PyQt6.QtCore.PYQT_VERSION_STR
    except ImportError:
        logger.error("PyQt6未安装")
        return False, None


def get_system_info():
    """获取系统信息"""
    info = {
        "system": platform.system(),
        "version": platform.version(),
        "python": sys.version,
        "architecture": platform.architecture()[0],
        "frozen": is_pyinstaller_environment(),
        "executable": sys.executable,
    }

    logger.info(f"系统信息: {info}")
    return info