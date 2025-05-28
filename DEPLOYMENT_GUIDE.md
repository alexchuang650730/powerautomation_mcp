# PowerAutomation MCP 工具部署与使用文档

## 目录

1. [系统概述](#系统概述)
2. [安装与配置](#安装与配置)
   - [系统要求](#系统要求)
   - [安装步骤](#安装步骤)
   - [SSH密钥配置](#ssh密钥配置)
   - [配置文件](#配置文件)
3. [核心功能模块](#核心功能模块)
   - [视觉思考记录器](#视觉思考记录器)
   - [自动导航模块](#自动导航模块)
   - [Release管理器](#release管理器)
   - [测试与README更新器](#测试与readme更新器)
   - [问题解决器](#问题解决器)
   - [Release规则检查器](#release规则检查器)
4. [使用指南](#使用指南)
   - [命令行接口](#命令行接口)
   - [自动化工作流](#自动化工作流)
   - [手动操作](#手动操作)
5. [常见问题与故障排除](#常见问题与故障排除)
6. [最佳实践](#最佳实践)
7. [API参考](#api参考)
8. [更新与维护](#更新与维护)
9. [高级功能](#高级功能)
   - [自定义配置](#自定义配置)
   - [日志与报告](#日志与报告)
   - [集成到CI/CD](#集成到cicd)

## 系统概述

PowerAutomation MCP工具是一个专为 https://github.com/alexchuang650730/powerautomation 项目设计的自动化工具，它通过MCP（Multi-agent Communication Protocol）实现了以下核心功能：

1. **自动记录Manus所有步骤思考过程及动作**：通过OCR和视觉识别技术，实时监控Manus界面，记录思考过程和执行动作。

2. **在release时自动下载代码到端侧Mac并上传GitHub**：监控GitHub release事件，自动下载代码到指定目录，并在需要时上传更改。

3. **在端侧执行测试并更新README**：自动执行测试步骤，收集问题，并更新README文件。

4. **驱动Manus进行问题定位、修复和测试**：分析测试问题，生成问题定位报告、修复策略和测试方案。

系统采用模块化设计，各功能模块可独立使用，也可通过中央协调器实现端到端的自动化工作流。

## 安装与配置

### 系统要求

- **操作系统**：macOS Sonoma (14.x)
- **Python版本**：Python 3.9+
- **依赖库**：
  - pytesseract (OCR引擎)
  - playwright (浏览器自动化)
  - PyGithub (GitHub API)
  - opencv-python (图像处理)
  - pillow (图像处理)
  - pyyaml (配置文件处理)
- **Git**：Git 2.20或更高版本
- **GitHub CLI**（可选）：用于创建release和查看release信息
- **SSH密钥**：用于GitHub认证
- **磁盘空间**：至少500MB可用空间
- **网络**：稳定的互联网连接

### 安装步骤

1. **克隆仓库**：

```bash
git clone https://github.com/alexchuang650730/powerautomation_mcp.git
cd powerautomation_mcp
```

2. **创建并激活虚拟环境**（推荐）：

```bash
python -m venv myenv
source myenv/bin/activate  # 在macOS/Linux上
```

3. **安装依赖**：

```bash
pip install -r requirements.txt
```

4. **安装OCR引擎**：

```bash
# macOS
brew install tesseract

# 或者使用其他包管理器
```

5. **安装Playwright浏览器**：

```bash
playwright install
```

### SSH密钥配置

MCP工具使用SSH密钥与GitHub进行认证，确保您已经设置了SSH密钥并添加到GitHub账户：

1. 检查是否已有SSH密钥：

```bash
ls -la ~/.ssh
```

2. 如果没有，生成新的SSH密钥：

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

3. 将SSH密钥添加到ssh-agent：

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

4. 将公钥添加到GitHub账户：
   - 复制公钥内容：`cat ~/.ssh/id_ed25519.pub`
   - 在GitHub中，转到Settings > SSH and GPG keys > New SSH key
   - 粘贴公钥内容并保存

5. 测试SSH连接：

```bash
ssh -T git@github.com
```

### 配置文件

首次运行时，系统会在`~/.powerautomation_mcp/config.json`创建默认配置文件。您可以根据需要修改以下关键配置：

```json
{
  "repo_path": "/Users/alexchuang/powerassistant/powerautomation",
  "repo_url": "https://github.com/alexchuang650730/powerautomation.git",
  "mcp_repo_url": "https://github.com/alexchuang650730/powerautomation_mcp.git",
  "ssh_key_path": "~/.ssh/id_rsa",
  "github_token": null,
  "check_interval": 3600.0,
  "log_dir": "~/powerassistant/powerautomation/logs",
  "screenshot_dir": "~/powerassistant/powerautomation/screenshots",
  "manus_url": "https://manus.im/",
  "ocr_engine": "tesseract",
  "monitor_regions": {
    "thought_region": {"x": 100, "y": 100, "width": 400, "height": 300},
    "action_region": {"x": 100, "y": 400, "width": 400, "height": 300},
    "taskbar_region": {"x": 0, "y": 0, "width": 100, "height": 600}
  },
  "capture_interval": 2.0
}
```

**关键配置说明**：

- `repo_path`：本地仓库路径
- `ssh_key_path`：SSH密钥路径
- `manus_url`：Manus网站URL
- `monitor_regions`：屏幕监控区域设置
- `capture_interval`：屏幕捕获间隔（秒）

## 核心功能模块

### 视觉思考记录器

视觉思考记录器（VisualThoughtRecorder）是系统的核心模块，负责通过OCR技术实时监控Manus界面，记录思考过程和执行动作。

**主要功能**：

- 自动截取屏幕指定区域
- 使用OCR识别文本内容
- 智能区分思考过程和执行动作
- 结构化存储记录信息

**配置视觉监控区域**：

系统提供了图形化配置工具，可以直观地设置监控区域：

```bash
python -m mcp_tool.visual_recorder_config
```

这将打开一个图形界面，您可以通过拖拽来定义监控区域，并测试OCR识别效果。

**查看记录的思考和动作**：

```python
from mcp_tool.enhanced_thought_recorder import EnhancedThoughtRecorder

recorder = EnhancedThoughtRecorder()
thoughts = recorder.get_latest_thoughts(limit=10)
actions = recorder.get_latest_thoughts(limit=10, include_actions=True)

# 按类型过滤
reasoning_thoughts = recorder.get_latest_thoughts(filter_type="reasoning")
```

### 自动导航模块

自动导航模块（ManusNavigator）负责检测Manus界面是否存在，如果不存在则自动导航到Manus网站。

**主要功能**：

- 检测当前是否在Manus界面
- 自动启动浏览器并导航到Manus
- 处理登录和认证流程
- 维护浏览器会话状态

**手动触发导航**：

```python
from mcp_tool.manus_navigator import ManusNavigator

navigator = ManusNavigator()
navigator.navigate_to_manus()
```

### Release管理器

Release管理器（ReleaseManager）负责监控GitHub release事件，自动下载代码到指定目录，并在需要时上传更改。

**主要功能**：

- 监控GitHub release事件
- 下载release代码到本地目录
- 检测本地更改并上传到GitHub
- 支持SSH密钥认证

**检查并下载最新release**：

```python
from mcp_tool.release_manager import ReleaseManager

manager = ReleaseManager()
if manager.is_new_release_available():
    manager.download_release()
```

**上传本地更改**：

```python
manager.upload_to_github("更新README和测试结果")
```

### 测试与README更新器

测试与README更新器（TestAndReadmeUpdater）负责自动执行测试步骤，收集问题，并更新README文件。

**主要功能**：

- 执行自动化测试
- 截图记录测试步骤
- 收集测试问题
- 更新README文件

**运行测试并更新README**：

```python
from mcp_tool.test_readme_updater import TestAndReadmeUpdater

updater = TestAndReadmeUpdater()
test_results = updater.run_tests()
updater.update_readme_with_test_results()
```

### 问题解决器

问题解决器（ManusProblemSolver）负责分析测试问题，生成问题定位报告、修复策略和测试方案。

**主要功能**：

- 分析测试问题
- 生成问题定位报告
- 提出修复策略
- 制定测试方案
- **版本回滚管理**：支持每个版本的回滚，在持续出错时回滚至保存点

**分析问题并生成解决方案**：

```python
from mcp_tool.manus_problem_solver import ManusProblemSolver

solver = ManusProblemSolver()
solutions = solver.analyze_issues_and_generate_solutions()
report_path = solver.save_solutions_to_file(solutions)
```

### Release规则检查器

Release规则检查器（ReleaseRulesChecker）负责验证Release是否符合规则要求。

**主要功能**：

- 验证是否在真实环境中验证了修复效果
- 验证是否基于实际运行结果而非代码分析做出判断
- 验证是否完整测试了代码

**验证Release规则**：

```python
from mcp_tool.release_rules_checker import ReleaseRulesChecker

checker = ReleaseRulesChecker()
result = checker.verify_all_rules()
```

## 使用指南

### 命令行接口

系统提供了简单易用的命令行接口：

```bash
# 检查并下载release
python -m mcp_tool.cli download [--tag TAG]

# 运行测试并收集问题
python -m mcp_tool.cli test

# 分析并解决问题
python -m mcp_tool.cli solve

# 上传更改
python -m mcp_tool.cli upload [--message MESSAGE]

# 运行完整工作流程
python -m mcp_tool.cli workflow [--tag TAG] [--no-upload]

# 验证端到端工作流
python -m mcp_tool.cli validate [--tag TAG]

# 配置视觉监控区域
python -m mcp_tool.cli config
```

### 自动化工作流

系统支持完整的端到端自动化工作流，包括以下步骤：

1. 检查Manus界面并导航
2. 检查并下载release
3. 验证Release规则
4. 运行测试并更新README
5. 分析问题并生成解决方案
6. 上传更改（可选）

**启动自动化工作流**：

```python
from mcp_tool.mcp_central_coordinator import MCPCentralCoordinator

coordinator = MCPCentralCoordinator()
result = coordinator.run_full_workflow()
```

**在后台监控releases**：

```python
def callback(result):
    print(f"工作流完成，状态: {result['status']}")

coordinator.start_monitoring_in_background(callback)
```

### 手动操作

除了自动化工作流，您还可以手动使用各个模块：

**1. 配置视觉监控区域**：

```bash
python -m mcp_tool.visual_recorder_config
```

**2. 启动视觉记录**：

```python
from mcp_tool.visual_thought_recorder import VisualThoughtRecorder

recorder = VisualThoughtRecorder()
recorder.start_monitoring()
```

**3. 检查并下载release**：

```bash
python -m mcp_tool.cli download
```

**4. 运行测试**：

```bash
python -m mcp_tool.cli test
```

**5. 分析问题**：

```bash
python -m mcp_tool.cli solve
```

## 常见问题与故障排除

### OCR识别问题

**问题**：OCR无法正确识别Manus界面文本

**解决方案**：
- 调整监控区域，确保区域内只包含需要识别的文本
- 尝试使用不同的OCR引擎（在配置文件中修改`ocr_engine`）
- 增加屏幕分辨率或调整Manus界面字体大小

### 浏览器自动化问题

**问题**：无法自动导航到Manus界面

**解决方案**：
- 确保已安装Playwright浏览器：`playwright install`
- 检查网络连接是否正常
- 尝试手动打开Manus界面，然后再运行自动化工具

### GitHub访问问题

**问题**：无法访问GitHub或上传更改

**解决方案**：
- 确保SSH密钥已正确配置并添加到GitHub账户
- 检查SSH密钥路径是否正确（在配置文件中的`ssh_key_path`）
- 尝试手动使用SSH连接GitHub，确认连接正常

### 测试执行问题

**问题**：自动化测试失败或无法完成

**解决方案**：
- 检查测试脚本是否最新
- 确保Manus界面可访问
- 查看测试日志，了解具体失败原因
- 尝试手动执行测试步骤，确认问题

## 最佳实践

### 视觉监控配置

- **精确定义监控区域**：确保监控区域只包含需要识别的内容，避免干扰
- **定期校准**：如果Manus界面发生变化，重新配置监控区域
- **适当的捕获间隔**：根据实际需求调整捕获间隔，平衡实时性和系统负载

### Release管理

- **定期检查**：定期检查是否有新的release，而不是依赖自动检测
- **保留备份**：在下载新release前，备份当前代码
- **明确的提交信息**：上传更改时，提供清晰的提交信息，说明更改内容

### 问题解决

- **验证解决方案**：在应用修复前，验证问题解决器生成的解决方案
- **保留问题历史**：保留问题分析报告，用于追踪问题模式和改进
- **持续改进**：根据实际问题和解决效果，不断改进问题解决策略

## API参考

详细的API参考文档请参见项目源代码中的注释和文档字符串。以下是主要类和方法的概览：

### VisualThoughtRecorder

```python
class VisualThoughtRecorder:
    def __init__(self, log_dir=None, monitor_regions=None, ocr_engine="tesseract", capture_interval=2.0, navigator=None)
    def start_monitoring()
    def stop_monitoring()
    def capture_and_process_screen()
    def get_latest_records(limit=10)
```

### EnhancedThoughtRecorder

```python
class EnhancedThoughtRecorder:
    def __init__(self, log_dir=None, visual_recorder=None)
    def record_thought(content, thought_type="general", context=None)
    def record_action(action_name, params, result, context=None)
    def get_latest_thoughts(limit=10, include_actions=False, filter_type=None)
    def query_logs(start_time=None, end_time=None, filters=None)
```

### ManusNavigator

```python
class ManusNavigator:
    def __init__(self, manus_url=None, headless=False)
    def is_browser_open()
    def is_on_manus_page()
    def navigate_to_manus()
    def close_browser()
```

### ReleaseManager

```python
class ReleaseManager:
    def __init__(self, repo_url=None, local_repo_path=None, github_token=None, ssh_key_path=None, check_interval=3600.0)
    def is_new_release_available()
    def download_release(tag_name=None)
    def get_local_repo_status()
    def upload_to_github(commit_message)
    def monitor_releases(callback=None)
```

### TestAndReadmeUpdater

```python
class TestAndReadmeUpdater:
    def __init__(self, repo_path=None, screenshot_dir=None, visual_recorder=None, release_manager=None, rules_checker=None)
    def run_tests()
    def update_readme_with_test_results()
    def generate_test_report()
```

### ManusProblemSolver

```python
class ManusProblemSolver:
    def __init__(self, repo_path=None, enhanced_recorder=None, test_updater=None, rules_checker=None)
    def analyze_issues_and_generate_solutions(issues=None)
    def save_solutions_to_file(solutions, output_dir=None)
    def create_save_point(name=None)
    def list_save_points()
    def rollback_to_save_point(save_point_id)
```

### ReleaseRulesChecker

```python
class ReleaseRulesChecker:
    def __init__(self, repo_path=None, enhanced_recorder=None)
    def verify_rule(rule_name)
    def verify_all_rules()
```

### MCPCentralCoordinator

```python
class MCPCentralCoordinator:
    def __init__(self, config_path=None)
    def run_full_workflow(tag_name=None, skip_upload=False)
    def monitor_releases(callback=None)
    def start_monitoring_in_background(callback=None)
    def get_workflow_status()
    def validate_end_to_end_workflow(tag_name=None)
    def generate_validation_report(validation_result, output_path=None)
```

## 更新与维护

### 更新依赖

定期更新依赖包：

```bash
pip install --upgrade -r requirements.txt
```

### 更新配置

如果需要更新配置，可以直接编辑配置文件：

```bash
nano ~/.powerautomation_mcp/config.json
```

或者使用配置工具：

```bash
python -m mcp_tool.cli config
```

### 日志管理

系统日志存储在配置的`log_dir`目录中，定期检查和清理日志文件，避免占用过多磁盘空间。

### 备份

定期备份重要的配置和日志：

```bash
cp -r ~/.powerautomation_mcp ~/backups/powerautomation_mcp_$(date +%Y%m%d)
```

## 高级功能

### 自定义配置

您可以通过命令行参数指定配置文件路径：

```bash
python -m mcp_tool.cli workflow --config /path/to/custom_config.json
```

也可以通过环境变量设置配置文件路径：

```bash
export MCP_CONFIG_PATH=/path/to/custom_config.json
python -m mcp_tool.cli workflow
```

### 日志与报告

MCP工具会自动生成详细的日志和报告：

- **日志**：保存在`{local_repo_path}/logs`目录下
- **测试报告**：保存在`{local_repo_path}/output`目录下
- **工作流程报告**：保存在`{local_repo_path}/reports`目录下
- **解决方案**：保存在`{local_repo_path}/manus_solutions`目录下

查看最新的工作流程报告：

```bash
ls -lt $(python -m mcp_tool.cli config --get local_repo_path)/reports | head -n 2
```

### 集成到CI/CD

MCP工具可以集成到CI/CD流程中，例如使用GitHub Actions：

```yaml
name: PowerAutomation MCP Workflow

on:
  release:
    types: [published]

jobs:
  mcp-workflow:
    runs-on: macos-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Set up SSH key
        uses: webfactory/ssh-agent@v0.5.3
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}
      
      - name: Run MCP workflow
        run: |
          python -m mcp_tool.cli workflow --tag ${{ github.event.release.tag_name }}
```
