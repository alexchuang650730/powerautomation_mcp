# 图形化区域选择工具使用指南

## 简介

图形化区域选择工具(GUI Region Selector)是一个用于直观选择屏幕区域的工具，提供类似Mac截图的交互体验。用户可以直接在屏幕上拖动选择区域，实时查看坐标和尺寸信息，无需手动输入坐标。该工具支持Windows和Mac平台，是视觉校准工具的升级版本。

## 特点

- **直观的拖动选择**：直接在屏幕上拖动鼠标选择区域
- **实时反馈**：显示坐标和尺寸信息
- **跨平台支持**：同时支持Windows和Mac平台
- **用户友好界面**：清晰的操作指引和键盘快捷键
- **自动保存配置**：选择完成后自动保存到配置文件

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

主要依赖：
- pillow：图像处理
- tkinter：GUI界面（Python标准库，通常已预装）

## 使用方法

### 基本用法

```bash
# Windows平台
python mcp_tool/gui_region_selector.py --output_dir "C:\Users\YourName\Desktop\calibration"

# Mac平台
python mcp_tool/gui_region_selector.py --output_dir "/Users/username/Desktop/calibration"
```

### 命令行参数

工具支持以下命令行参数：

- `--output_dir`：指定输出目录路径
- `--config`：指定配置文件路径

### 操作步骤

1. 运行工具后，会自动截取全屏并显示
2. 拖动鼠标选择"工作列表"区域
3. 按Enter确认并继续
4. 拖动鼠标选择"操作列表"区域
5. 按Enter确认并完成
6. 配置文件会自动保存到指定目录

### 键盘快捷键

- `Enter`：确认当前区域并继续下一个
- `Esc`：取消当前选择

## 工作流程

1. 工具启动后会自动捕获全屏截图
2. 用户通过拖动鼠标选择第一个区域（工作列表）
3. 确认后继续选择第二个区域（操作列表）
4. 所有区域选择完成后，工具自动保存配置文件
5. 配置文件可直接用于自动网页监控工具

## 输出文件

工具会在指定的输出目录中生成以下文件：

- `screenshot_*.png`：原始屏幕截图
- `auto_web_monitor_config.json`：自动监控配置文件，包含选择的区域坐标

## 常见问题

### 截图不完整

**问题**：在某些高分辨率显示器上，截图可能不完整。

**解决方案**：
- Windows：确保使用最新版本的PIL库
- Mac：确保已授予终端屏幕录制权限

### 界面显示异常

**问题**：在某些环境下，界面元素可能显示异常。

**解决方案**：
- 调整显示器分辨率
- 更新Python和tkinter版本

### 配置文件未生成

**问题**：完成区域选择后，配置文件未生成。

**解决方案**：
- 确保指定的输出目录存在且有写入权限
- 检查是否完成了所有区域的选择（工作列表和操作列表）

## 与自动网页监控工具集成

选择完区域后，可以直接使用生成的配置文件运行自动网页监控工具：

```bash
python mcp_tool/auto_web_monitor.py --config "/path/to/output_dir/auto_web_monitor_config.json" --start
```

## 开发者信息

### 架构

该工具采用面向对象的设计，主要包含以下类：

- `GUIRegionSelector`：基类，包含所有平台通用的GUI功能
- `WindowsGUIRegionSelector`：Windows平台特定实现
- `MacGUIRegionSelector`：Mac平台特定实现

### 扩展

如果您想添加新的区域类型，可以修改`region_names`列表：

```python
self.region_names = ["work_list", "action_list", "new_region"]
```

## 许可证

[许可证信息]

## 联系方式

如有任何问题或建议，请联系[联系信息]。
