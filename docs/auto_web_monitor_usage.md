# AutoWebMonitor 使用文档

## 简介

AutoWebMonitor 是一个无GUI的自动网页监控与抓取模块，能够自动检测浏览器是否访问了特定网站（如https://manus.im/），并在访问时自动截取工作列表和操作列表。该模块不依赖tkinter或其他GUI库，适合在各种环境下运行。

## 主要功能

- 自动检测浏览器当前访问的URL
- 识别目标网站（默认为manus.im）
- 自动截取屏幕并保存
- 提取页面HTML内容
- 分析并提取工作列表和操作列表
- 支持多平台（Windows、macOS、Linux）

## 安装要求

```bash
pip install -r requirements.txt
```

主要依赖：
- requests
- pillow (PIL)
- beautifulsoup4 (可选，用于更高级的HTML解析)

## 基本用法

### 1. 简单启动监控

```python
from mcp_tool.auto_web_monitor import get_instance

# 获取监控器实例
monitor = get_instance()

# 开始监控
monitor.start_monitoring()

# 程序继续运行...
# 监控在后台线程中进行

# 停止监控
monitor.stop_monitoring()
```

### 2. 使用自定义配置

```python
from mcp_tool.auto_web_monitor import AutoWebMonitor

# 创建配置文件
config = {
    "target_url": "https://manus.im",
    "capture_interval": 2.0,  # 捕获间隔（秒）
    "log_dir": "/path/to/logs",
    "browser_check_interval": 1.0  # 浏览器检查间隔（秒）
}

# 保存配置到文件
import json
with open("config.json", "w") as f:
    json.dump(config, f)

# 使用配置文件初始化
monitor = AutoWebMonitor("config.json")
monitor.start_monitoring()
```

### 3. 命令行使用

```bash
# 使用默认配置启动监控
python -m mcp_tool.auto_web_monitor --start

# 使用自定义配置启动监控
python -m mcp_tool.auto_web_monitor --config /path/to/config.json --start

# 停止监控
python -m mcp_tool.auto_web_monitor --stop
```

## 配置选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| target_url | 目标网站URL | https://manus.im |
| capture_interval | 捕获间隔（秒） | 2.0 |
| log_dir | 日志和捕获文件保存目录 | ~/mcp_logs |
| browser_check_interval | 浏览器检查间隔（秒） | 1.0 |
| work_list_selector | 工作列表的CSS选择器 | .work-list-container |
| action_list_selector | 操作列表的CSS选择器 | .action-list-container |

## 输出文件

监控器会在配置的log_dir目录下生成以下文件：

- `screenshot_{timestamp}.png` - 完整屏幕截图
- `work_list_{timestamp}.png` - 工作列表区域截图
- `action_list_{timestamp}.png` - 操作列表区域截图
- `work_list_{timestamp}.txt` - 工作列表文本内容
- `action_list_{timestamp}.txt` - 操作列表文本内容
- `page_{timestamp}.html` - 原始HTML内容

## 集成到现有项目

### 与MCP中央协调器集成

```python
from mcp_tool.mcp_central_coordinator import MCPCentralCoordinator
from mcp_tool.auto_web_monitor import get_instance

class EnhancedMCPCoordinator(MCPCentralCoordinator):
    def __init__(self, config_file=None):
        super().__init__(config_file)
        self.web_monitor = get_instance()
        
    def start(self):
        super().start()
        # 启动网页监控
        self.web_monitor.start_monitoring()
        
    def stop(self):
        # 停止网页监控
        self.web_monitor.stop_monitoring()
        super().stop()
```

## 故障排除

1. **无法检测到浏览器URL**
   - 确保使用支持的浏览器（Chrome、Safari等）
   - 检查操作系统权限设置
   - 尝试使用浏览器扩展方法（需要额外配置）

2. **捕获的内容不准确**
   - 调整工作列表和操作列表的CSS选择器
   - 检查网站结构是否发生变化
   - 尝试使用更高级的HTML解析方法

3. **高CPU使用率**
   - 增加browser_check_interval值
   - 增加capture_interval值
   - 确保在不需要时停止监控

## 开发者扩展

### 添加新的URL检测方法

```python
def _get_url_from_custom_method(self):
    """自定义URL获取方法"""
    # 实现自定义逻辑
    return url

# 在AutoWebMonitor._get_current_browser_url方法中添加：
url = self._get_url_from_custom_method()
if url:
    return url
```

### 添加新的内容提取方法

```python
def _extract_content_with_custom_method(self, url, timestamp):
    """自定义内容提取方法"""
    # 实现自定义逻辑
    pass

# 在AutoWebMonitor._extract_page_content方法中添加：
self._extract_content_with_custom_method(url, timestamp)
```
