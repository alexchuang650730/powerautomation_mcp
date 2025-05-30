# 跨平台视觉校准工具使用指南

## 简介

跨平台视觉校准工具（Visual Calibrator）是一个用于校准和测试自动网页监控的视觉抓取区域的工具，支持Windows和Mac环境。该工具可以动态识别网页元素位置，适应不同屏幕分辨率和浏览器窗口大小。

## 安装

### 前提条件

- Python 3.6+
- pip 包管理器

### 步骤1：克隆仓库

```bash
# 克隆仓库
git clone <repository_url>
cd powerautomation_mcp
```

### 步骤2：安装依赖

```bash
# 安装依赖
pip install -r requirements.txt
```

Windows平台需要的主要依赖：
- pillow：图像处理
- pyautogui：屏幕截图
- pygetwindow：窗口检测
- pywin32：Windows API访问（可选）
- pyperclip：剪贴板操作

Mac平台需要的主要依赖：
- pillow：图像处理
- pyperclip：剪贴板操作

### 步骤3：确保模块结构正确

确保`mcp_tool`目录中有`__init__.py`文件：

```bash
# 检查__init__.py是否存在
ls -la mcp_tool/

# 如果不存在，创建它
touch mcp_tool/__init__.py
```

## 使用方法

### 基本用法

```bash
# Windows平台
python -m mcp_tool.visual_calibrator --output_dir "C:\Users\YourName\Desktop\calibration"

# Mac平台
python -m mcp_tool.visual_calibrator --output_dir "/Users/username/Desktop/calibration"
```

### 命令行参数

工具支持以下命令行参数：

- `--config`：指定配置文件路径
- `--output_dir`：指定输出目录路径
- `--simple_mode`：使用简化模式（不使用平台特定API）
- `--manual_regions`：使用手动区域标定模式

### 示例

#### 使用手动区域标定模式

```bash
python -m mcp_tool.visual_calibrator --output_dir "/path/to/output" --manual_regions
```

#### 使用简化模式

```bash
python -m mcp_tool.visual_calibrator --output_dir "/path/to/output" --simple_mode
```

#### 指定配置文件

```bash
python -m mcp_tool.visual_calibrator --config "/path/to/config.json" --output_dir "/path/to/output"
```

## 工作流程

1. 运行工具前，请确保浏览器已打开并访问了manus.im网站
2. 工具会自动捕获屏幕截图并检测浏览器窗口
3. 如果使用手动区域标定模式，工具会生成带网格的截图并提示您输入区域坐标
4. 工具会可视化标记检测到的区域，并提取区域内容
5. 最后，工具会更新自动监控配置并保存结果

## 输出文件

工具会在指定的输出目录中生成以下文件：

- `screenshot_*.png`：原始屏幕截图
- `grid_*.png`：带网格的屏幕截图
- `marked_*.png`：带标记的屏幕截图
- `work_list_*.png`：工作列表区域截图
- `action_list_*.png`：操作列表区域截图
- `auto_web_monitor_config.json`：自动监控配置文件

## 常见问题

### 模块未找到错误

如果遇到"No module named mcp_tool.visual_calibrator"错误，请尝试以下解决方案：

1. 确保`mcp_tool`目录中有`__init__.py`文件
2. 确保您已经从GitHub拉取了最新代码
3. 确保您在正确的目录中运行命令
4. 尝试设置PYTHONPATH环境变量：

```bash
# Windows
set PYTHONPATH=C:\path\to\powerautomation_mcp
python -m mcp_tool.visual_calibrator

# Mac/Linux
export PYTHONPATH=/path/to/powerautomation_mcp
python -m mcp_tool.visual_calibrator
```

### 权限问题

#### Windows平台

如果遇到权限问题，请尝试以管理员身份运行命令提示符或PowerShell。

#### Mac平台

如果遇到"Operation not permitted"错误，请确保您已授予终端屏幕录制权限：

1. 打开系统偏好设置
2. 点击安全性与隐私
3. 点击隐私选项卡
4. 在左侧列表中选择"屏幕录制"
5. 确保终端应用程序在右侧列表中并被勾选

### 浏览器窗口检测失败

如果浏览器窗口检测失败，请尝试使用简化模式：

```bash
python -m mcp_tool.visual_calibrator --simple_mode --output_dir "/path/to/output"
```

## 开发者信息

### 架构

该工具采用面向对象的设计，主要包含以下类：

- `VisualCalibrator`：基类，包含所有平台通用的功能
- `WindowsVisualCalibrator`：Windows平台特定实现
- `MacVisualCalibrator`：Mac平台特定实现

### 测试

运行单元测试：

```bash
cd powerautomation_mcp
python -m unittest discover tests
```

### 贡献

欢迎提交问题报告和功能请求。如果您想贡献代码，请遵循以下步骤：

1. Fork仓库
2. 创建您的特性分支
3. 提交您的更改
4. 推送到分支
5. 创建新的Pull Request

## 许可证

[许可证信息]

## 联系方式

如有任何问题或建议，请联系[联系信息]。
