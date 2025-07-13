# PyQt6界面设计器启动器

一个简单易用的PyQt6界面设计器启动工具，提供图形化界面来启动Qt Designer和转换UI文件。

## 功能特性

- 🎨 **启动Qt Designer**: 一键启动PyQt6界面设计器
- 🔄 **UI文件转换**: 将.ui文件转换为Python代码文件
- 🇨🇳 **中文界面**: 完全中文化的用户界面
- 🎯 **人性化设计**: 简洁美观的界面设计
- 🔍 **自动检测**: 自动检测系统中的Qt Designer路径

## 系统要求

- Python 3.7+
- PyQt6
- Qt Designer (通常随PyQt6-tools安装)

## 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/HeMOua/pyqt-designer-launcher.git
cd pyqt-designer-launcher
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行程序**
```bash
python main.py
```

## 使用说明

### 启动Qt Designer

1. 程序启动后会自动检测系统中的Qt Designer路径
2. 如果检测失败，可以点击"浏览"按钮手动选择Qt Designer可执行文件
3. 点击"启动 Qt Designer"按钮即可启动界面设计器

### 转换UI文件

1. 点击"选择文件"按钮选择要转换的.ui文件
2. 选择输出目录（可选，默认为UI文件所在目录）
3. 点击"转换为Python文件"按钮开始转换
4. 转换完成后会在输出区域显示结果信息

## 项目结构

```
pyqt-designer-launcher/
├── main.py                 # 主程序入口
├── ui_launcher.py          # 主界面类
├── utils.py               # 工具函数
├── requirements.txt       # 依赖列表
└── README.md             # 项目说明
```

## 常见问题

### Q: UI转换失败怎么办？

A: 请检查：
1. 选择的文件是否为有效的.ui文件
2. 输出目录是否有写入权限
3. PyQt6是否正确安装

### Q: 支持哪些操作系统？

A: 支持Windows、macOS和Linux系统。

## 开发说明

本项目使用PyQt6开发，主要文件说明：

- `main.py`: 应用程序入口点
- `ui_launcher.py`: 主窗口界面实现
- `utils.py`: 工具函数，包括路径检测和文件转换功能

## 贡献

欢迎提交Issues和Pull Requests来改进这个项目！

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 联系方式

如有问题或建议，请通过GitHub Issues联系。