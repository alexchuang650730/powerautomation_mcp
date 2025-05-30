# Mac视觉校准工具使用指南

## 简介

Mac视觉校准工具(MacVisualCalibrator)是一个专为Mac环境设计的工具，用于校准和测试自动网页监控的视觉抓取区域。它能够动态识别网页元素位置，适应不同屏幕分辨率和浏览器窗口大小，特别针对manus.im网站的工作列表和操作列表区域进行优化。

## 安装依赖

在使用Mac视觉校准工具前，请确保已安装必要的依赖：

```bash
pip install pillow
```

## 基本用法

### 1. 获取最新代码

首先确保您已获取最新代码：

```bash
cd powerautomation_mcp
git pull origin main
```

### 2. 运行校准工具

基本命令格式：

```bash
python -m mcp_tool.mac_visual_calibrator [参数]
```

### 3. 查看帮助信息

```bash
python -m mcp_tool.mac_visual_calibrator --help
```

## 命令行参数

Mac视觉校准工具支持以下命令行参数：

| 参数 | 说明 |
|------|------|
| `--config CONFIG` | 指定配置文件路径 |
| `--output_dir OUTPUT_DIR` | 指定输出目录路径 |
| `--simple_mode` | 使用简化模式（不使用AppleScript） |
| `--manual_regions` | 使用手动区域标定模式 |

## 使用示例

### 基本校准

```bash
python -m mcp_tool.mac_visual_calibrator
```

### 指定输出目录

```bash
python -m mcp_tool.mac_visual_calibrator --output_dir "/Users/username/Desktop/calibration_output"
```

### 使用简化模式

如果您遇到AppleScript权限问题，可以使用简化模式：

```bash
python -m mcp_tool.mac_visual_calibrator --simple_mode
```

### 手动区域标定

如果自动区域检测不准确，可以使用手动区域标定模式：

```bash
python -m mcp_tool.mac_visual_calibrator --manual_regions
```

### 组合使用参数

```bash
python -m mcp_tool.mac_visual_calibrator --output_dir "/Users/username/Desktop/calibration_output" --manual_regions
```

## 校准流程

1. **准备工作**：运行校准工具前，请确保您的浏览器已打开并访问了manus.im网站
2. **捕获屏幕**：工具会自动捕获全屏截图
3. **检测浏览器**：工具会检测浏览器窗口位置和当前URL
4. **创建网格**：生成带网格的校准图像，帮助理解坐标系统
5. **检测区域**：自动或手动标定工作列表和操作列表区域
6. **保存结果**：将校准结果保存到指定目录，并更新配置文件

## 输出文件

校准完成后，工具会在指定的输出目录（默认为`~/mcp_logs/`）生成以下文件：

- **校准截图**：带网格的截图，帮助理解坐标系统
- **区域标记图**：标记了工作列表和操作列表区域的截图
- **区域内容图**：提取的区域内容图像
- **配置文件**：更新后的配置文件，供自动监控模块使用

## 常见问题

### 1. AppleScript权限问题

**问题**：运行时出现"获取活动浏览器信息失败"错误

**解决方案**：
- 授予终端（或您运行Python的应用程序）访问系统事件的权限：
  1. 打开系统偏好设置 > 安全性与隐私 > 隐私
  2. 选择左侧的"辅助功能"或"自动化"
  3. 确保终端应用程序在右侧列表中并被勾选
- 或者使用简化模式：`--simple_mode`

### 2. 区域检测不准确

**问题**：自动检测的区域不准确

**解决方案**：
- 使用手动区域标定模式：`--manual_regions`
- 确保浏览器窗口完全可见，不被其他窗口遮挡
- 确保已访问manus.im网站

### 3. 输出目录不存在

**问题**：指定的输出目录不存在

**解决方案**：
- 确保目录已存在：`mkdir -p /path/to/output/dir`
- 或使用已存在的目录

## 高级配置

如果需要更高级的配置，可以创建自定义配置文件：

```json
{
  "log_dir": "/Users/username/custom_logs",
  "browser_window_title_pattern": ".*manus\\.im.*",
  "work_list_pattern": "work[-_\\s]*list|task[-_\\s]*list",
  "action_list_pattern": "action[-_\\s]*list|operation[-_\\s]*list",
  "calibration_grid_size": 10,
  "detection_confidence_threshold": 0.7,
  "default_work_list_region": [0.05, 0.2, 0.45, 0.8],
  "default_action_list_region": [0.55, 0.2, 0.95, 0.8]
}
```

然后使用`--config`参数指定配置文件：

```bash
python -m mcp_tool.mac_visual_calibrator --config "/path/to/custom_config.json"
```

## 与自动监控集成

校准完成后，自动监控模块会使用校准结果自动检测和抓取manus.im网站上的工作列表和操作列表。

要启动自动监控：

```bash
python -m mcp_tool.auto_web_monitor --start
```

## 技术支持

如有任何问题或需要技术支持，请联系开发团队或提交GitHub issue。
