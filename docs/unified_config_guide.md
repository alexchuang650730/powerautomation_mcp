# 统一配置指南

## 简介

PowerAutomation MCP工具包现在支持统一配置格式，使视觉校准工具和CLI功能能够共享同一份配置文件。这种统一的配置方式简化了工具的使用和维护，同时确保了不同功能模块之间的一致性。

## 配置文件位置

默认配置文件位置：`~/.powerautomation_mcp/config.json`

您也可以通过以下方式指定配置文件位置：

1. 命令行参数：`--config /path/to/config.json`
2. 环境变量：`MCP_CONFIG_PATH=/path/to/config.json`

## 配置文件结构

统一配置文件包含以下主要部分：

```json
{
  "// 基础配置": "通用配置项",
  "platform": "darwin",
  "log_dir": "/Users/username/mcp_logs",
  
  "// 仓库配置": "用于CLI工具的代码管理",
  "local_repo_path": "/Users/username/powerassistant/powerautomation",
  "repo_url": "https://github.com/username/powerautomation.git",
  "mcp_repo_url": "https://github.com/username/powerautomation_mcp.git",
  "ssh_key_path": "~/.ssh/id_rsa",
  "github_token": null,
  "github_repo": "username/powerautomation",
  
  "// 工作流配置": "用于CLI工具的工作流程控制",
  "test_script": "start_and_test.sh",
  "readme_path": "README.md",
  "auto_upload": true,
  "auto_test": true,
  "auto_solve": true,
  "check_interval": 3600.0,
  
  "// 监控配置": "用于视觉校准和自动监控",
  "screenshot_dir": "~/powerassistant/powerautomation/screenshots",
  "manus_url": "https://manus.im/",
  "ocr_engine": "tesseract",
  "capture_interval": 2.0,
  
  "// 监控区域配置": "用于自动监控的区域定义",
  "monitor_regions": {
    "work_list": {"x": 100, "y": 100, "width": 400, "height": 300},
    "action_list": {"x": 100, "y": 400, "width": 400, "height": 300}
  },
  
  "// 视觉校准配置": "用于视觉校准工具",
  "browser_window_title_pattern": ".*manus\\.im.*",
  "calibration_grid_size": 10,
  "detection_confidence_threshold": 0.7,
  "simple_mode": false,
  "manual_regions": false,
  "work_list_pattern": "work[-_\\s]*list|task[-_\\s]*list",
  "action_list_pattern": "action[-_\\s]*list|operation[-_\\s]*list",
  "work_list_css_selector": ".work-list-container",
  "action_list_css_selector": ".action-list-container",
  "default_work_list_region": [0.05, 0.2, 0.45, 0.8],
  "default_action_list_region": [0.55, 0.2, 0.95, 0.8],
  
  "// 版本管理配置": "用于ManusProblemSolver的版本回滚功能",
  "save_points_dir": "~/.powerautomation_mcp/save_points",
  "solutions_dir": "~/powerassistant/powerautomation/manus_solutions",
  "auto_create_save_point": true,
  "max_save_points": 10,
  "save_point_naming_pattern": "save_point_%Y%m%d_%H%M%S"
}
```

## 配置项说明

### 基础配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `platform` | 字符串 | 自动检测 | 平台类型，如"darwin"、"windows"、"linux"等 |
| `log_dir` | 字符串 | "~/mcp_logs" | 日志目录路径 |

### 仓库配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `local_repo_path` | 字符串 | "~/powerassistant/powerautomation" | 本地仓库路径 |
| `repo_url` | 字符串 | - | GitHub仓库URL |
| `mcp_repo_url` | 字符串 | - | MCP工具仓库URL |
| `ssh_key_path` | 字符串 | "~/.ssh/id_rsa" | SSH密钥路径 |
| `github_token` | 字符串 | null | GitHub令牌（可选） |
| `github_repo` | 字符串 | - | GitHub仓库名称（格式：username/repo） |

### 工作流配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `test_script` | 字符串 | "start_and_test.sh" | 测试脚本路径 |
| `readme_path` | 字符串 | "README.md" | README文件路径 |
| `auto_upload` | 布尔值 | true | 是否自动上传更改 |
| `auto_test` | 布尔值 | true | 是否自动运行测试 |
| `auto_solve` | 布尔值 | true | 是否自动解决问题 |
| `check_interval` | 数值 | 3600.0 | 检查间隔（秒） |

### 监控配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `screenshot_dir` | 字符串 | "~/powerassistant/powerautomation/screenshots" | 截图目录路径 |
| `manus_url` | 字符串 | "https://manus.im/" | Manus网站URL |
| `ocr_engine` | 字符串 | "tesseract" | OCR引擎 |
| `capture_interval` | 数值 | 2.0 | 截图间隔（秒） |

### 监控区域配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `monitor_regions` | 对象 | - | 监控区域配置，包含各区域的x、y、width、height |

### 视觉校准配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `browser_window_title_pattern` | 字符串 | ".*manus\\.im.*" | 浏览器窗口标题匹配模式 |
| `calibration_grid_size` | 数值 | 10 | 校准网格大小 |
| `detection_confidence_threshold` | 数值 | 0.7 | 检测置信度阈值 |
| `simple_mode` | 布尔值 | false | 是否使用简化模式 |
| `manual_regions` | 布尔值 | false | 是否使用手动区域标定模式 |
| `work_list_pattern` | 字符串 | "work[-_\\s]*list\|task[-_\\s]*list" | 工作列表匹配模式 |
| `action_list_pattern` | 字符串 | "action[-_\\s]*list\|operation[-_\\s]*list" | 操作列表匹配模式 |
| `work_list_css_selector` | 字符串 | ".work-list-container" | 工作列表CSS选择器 |
| `action_list_css_selector` | 字符串 | ".action-list-container" | 操作列表CSS选择器 |
| `default_work_list_region` | 数组 | [0.05, 0.2, 0.45, 0.8] | 默认工作列表区域 [左, 上, 右, 下] 相对比例 |
| `default_action_list_region` | 数组 | [0.55, 0.2, 0.95, 0.8] | 默认操作列表区域 [左, 上, 右, 下] 相对比例 |

### 版本管理配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `save_points_dir` | 字符串 | "~/.powerautomation_mcp/save_points" | 保存点目录路径 |
| `solutions_dir` | 字符串 | "~/powerassistant/powerautomation/manus_solutions" | 解决方案目录路径 |
| `auto_create_save_point` | 布尔值 | true | 是否自动创建保存点 |
| `max_save_points` | 数值 | 10 | 最大保存点数量 |
| `save_point_naming_pattern` | 字符串 | "save_point_%Y%m%d_%H%M%S" | 保存点命名模式 |

## 使用示例

### 创建统一配置文件

```bash
mkdir -p ~/.powerautomation_mcp
nano ~/.powerautomation_mcp/config.json
```

然后将以下内容复制到文件中（根据您的实际情况修改）：

```json
{
  "platform": "darwin",
  "log_dir": "/Users/alexchuang/Desktop/alex",
  "local_repo_path": "/Users/alexchuang/powerassistant/powerautomation",
  "repo_url": "https://github.com/alexchuang650730/powerautomation.git",
  "mcp_repo_url": "https://github.com/alexchuang650730/powerautomation_mcp.git",
  "ssh_key_path": "~/.ssh/id_rsa",
  "github_repo": "alexchuang650730/powerautomation",
  "auto_upload": true,
  "auto_test": true,
  "monitor_regions": {
    "work_list": {"x": 147, "y": 382, "width": 1176, "height": 1147},
    "action_list": {"x": 1617, "y": 382, "width": 1176, "height": 1147}
  },
  "capture_interval": 2.0
}
```

### 使用CLI功能

```bash
# 查看配置
python -m mcp_tool.cli config

# 下载release
python -m mcp_tool.cli download

# 上传更改
python -m mcp_tool.cli upload --message "更新配置"

# 运行工作流程
python -m mcp_tool.cli workflow
```

### 使用视觉校准工具

```bash
# 运行视觉校准工具
python -m mcp_tool.mac_visual_calibrator --manual_regions

# 使用简化模式
python -m mcp_tool.mac_visual_calibrator --simple_mode

# 使用图形化区域选择工具
python -m mcp_tool.gui_region_selector
```

### 使用ManusProblemSolver版本回滚功能

```bash
# 创建保存点
python -m mcp_tool.manus_problem_solver create_save_point --name "before_changes"

# 列出所有保存点
python -m mcp_tool.manus_problem_solver list_save_points

# 回滚到指定保存点
python -m mcp_tool.manus_problem_solver rollback --name "before_changes"
```

## 配置API使用

在Python代码中使用统一配置：

```python
from mcp_tool.unified_config import get_config

# 获取配置管理器实例
config = get_config()

# 读取配置项
log_dir = config.get("log_dir")
simple_mode = config.get("simple_mode", False)

# 设置配置项
config.set("test_key", "test_value")

# 批量更新配置
config.update({
    "simple_mode": True,
    "manual_regions": True
})

# 保存配置
config.save()

# 获取所有配置
all_config = config.get_all()
```

## 常见问题

### Q: 如何在不同平台之间共享配置文件？
A: 您可以创建一个基础配置文件，然后在不同平台上使用`--config`参数指定平台特定的配置文件。

### Q: 配置文件中的路径是否支持相对路径和环境变量？
A: 是的，统一配置管理模块会自动展开路径中的环境变量（如`~`、`$HOME`等）。

### Q: 如何合并两个配置文件？
A: 您可以使用统一配置管理模块的`merge_configs`函数：
```python
from mcp_tool.unified_config import merge_configs
merge_configs("/path/to/cli_config.json", "/path/to/visual_config.json", "/path/to/output.json")
```

## 更多信息

如需更多信息，请参阅以下文档：

- [CLI工具使用指南](./cli_usage.md)
- [视觉校准工具使用指南](./visual_calibrator_guide.md)
- [图形化区域选择工具使用指南](./gui_region_selector_guide.md)
- [架构设计图](./architecture_diagram.md)
