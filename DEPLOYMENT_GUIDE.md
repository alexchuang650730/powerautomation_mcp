# PowerAutomation MCP 工具部署与使用文档

## 目录

1. [简介](#简介)
2. [系统要求](#系统要求)
3. [安装与配置](#安装与配置)
   - [依赖安装](#依赖安装)
   - [SSH密钥配置](#ssh密钥配置)
   - [初始配置](#初始配置)
4. [基本使用](#基本使用)
   - [检查并下载Release](#检查并下载release)
   - [运行测试](#运行测试)
   - [问题分析与解决](#问题分析与解决)
   - [上传更改](#上传更改)
   - [完整工作流程](#完整工作流程)
5. [高级功能](#高级功能)
   - [自定义配置](#自定义配置)
   - [日志与报告](#日志与报告)
   - [集成到CI/CD](#集成到cicd)
6. [常见问题](#常见问题)
7. [故障排除](#故障排除)
8. [API参考](#api参考)

## 简介

PowerAutomation MCP工具是一个多智能体通信协议工具包，专为PowerAutomation项目设计，提供以下核心功能：

1. **自动记录Manus所有步骤思考过程及动作**：捕获Manus的思考过程和执行的操作，提供结构化的日志存储和查询功能。
2. **在release时自动下载代码到端侧Mac对应目录并上传GitHub**：监控GitHub release事件，自动下载代码到指定Mac路径，处理GitHub上传流程。
3. **在端侧执行测试步骤要求的动作并把所有的问题放在更新版的README里**：执行自动化测试，收集问题并更新README文件。
4. **驱动Manus能够定位问题、提出修复策略、提出测试方案**：分析测试日志和README中的问题，调用Manus能力进行问题定位，生成修复策略建议，提出测试方案。

该工具采用模块化设计，各功能模块可独立使用，也可通过中央协调器实现端到端的自动化流程。

## 系统要求

- **操作系统**：macOS Sonoma (14.x)
- **Python版本**：Python 3.8或更高版本
- **Git**：Git 2.20或更高版本
- **GitHub CLI**（可选）：用于创建release和查看release信息
- **SSH密钥**：用于GitHub认证
- **磁盘空间**：至少500MB可用空间
- **网络**：稳定的互联网连接

## 安装与配置

### 依赖安装

1. 克隆PowerAutomation MCP工具仓库：

```bash
git clone https://github.com/alexchuang650730/powerautomation_mcp.git
cd powerautomation_mcp
```

2. 创建并激活虚拟环境（推荐）：

```bash
python -m venv myenv
source myenv/bin/activate  # 在macOS/Linux上
```

3. 安装依赖：

```bash
pip install -r requirements.txt
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

### 初始配置

首次使用MCP工具前，需要创建配置文件：

1. 创建配置目录：

```bash
mkdir -p ~/.powerautomation_mcp
```

2. 创建配置文件：

```bash
cat > ~/.powerautomation_mcp/config.json << EOF
{
  "local_repo_path": "/Users/alexchuang/powerassistant/powerautomation",
  "github_repo": "alexchuang650730/powerautomation",
  "ssh_key_path": "~/.ssh/id_ed25519",
  "test_script": "start_and_test.sh",
  "readme_path": "README.md",
  "auto_upload": true,
  "auto_test": true,
  "auto_solve": true
}
EOF
```

3. 根据您的实际情况修改配置文件：
   - `local_repo_path`：本地仓库路径
   - `github_repo`：GitHub仓库名称
   - `ssh_key_path`：SSH密钥路径
   - `test_script`：测试脚本名称
   - `readme_path`：README文件路径
   - `auto_upload`：是否自动上传更改
   - `auto_test`：是否自动运行测试
   - `auto_solve`：是否自动分析并解决问题

## 基本使用

### 检查并下载Release

检查GitHub上是否有新的release，并下载到本地：

```bash
python -m mcp_tool.cli download
```

指定特定的release标签：

```bash
python -m mcp_tool.cli download --tag v1.0.0
```

### 运行测试

运行测试并收集问题：

```bash
python -m mcp_tool.cli test
```

### 问题分析与解决

分析README中的问题，生成修复策略和测试方案：

```bash
python -m mcp_tool.cli solve
```

### 上传更改

将本地更改上传到GitHub：

```bash
python -m mcp_tool.cli upload --message "自动更新 - 测试结果和解决方案"
```

### 完整工作流程

运行完整的工作流程，包括下载release、运行测试、分析问题和上传更改：

```bash
python -m mcp_tool.cli workflow
```

指定release标签并禁用自动上传：

```bash
python -m mcp_tool.cli workflow --tag v1.0.0 --no-upload
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

## 常见问题

### 1. SSH密钥认证失败

**问题**：运行工具时出现SSH认证错误。

**解决方案**：
- 确认SSH密钥已添加到GitHub账户
- 检查配置文件中的`ssh_key_path`是否正确
- 尝试手动测试SSH连接：`ssh -T git@github.com`

### 2. 测试脚本执行失败

**问题**：测试脚本执行失败，无法收集问题。

**解决方案**：
- 确认测试脚本有执行权限：`chmod +x {test_script}`
- 检查测试脚本是否存在：`ls -la {local_repo_path}/{test_script}`
- 手动运行测试脚本检查错误：`cd {local_repo_path} && ./{test_script}`

### 3. 无法找到新的Release

**问题**：工具报告"No new releases found"。

**解决方案**：
- 确认GitHub仓库中确实有release
- 检查配置文件中的`github_repo`是否正确
- 尝试指定特定的release标签：`python -m mcp_tool.cli download --tag v1.0.0`

### 4. README更新失败

**问题**：工具无法更新README文件。

**解决方案**：
- 确认README文件存在：`ls -la {local_repo_path}/{readme_path}`
- 检查README文件权限：`ls -l {local_repo_path}/{readme_path}`
- 确认用户有写入权限：`chmod u+w {local_repo_path}/{readme_path}`

## 故障排除

### 日志检查

检查日志文件以获取详细的错误信息：

```bash
ls -la $(python -m mcp_tool.cli config --get local_repo_path)/logs
cat $(python -m mcp_tool.cli config --get local_repo_path)/logs/latest.log
```

### 调试模式

启用调试模式获取更详细的日志：

```bash
python -m mcp_tool.cli workflow --debug
```

### 重置工具状态

如果工具状态异常，可以重置：

```bash
python -m mcp_tool.cli reset
```

### 手动验证各组件

逐个验证各组件是否正常工作：

1. 验证GitHub连接：

```bash
ssh -T git@github.com
```

2. 验证本地仓库：

```bash
cd $(python -m mcp_tool.cli config --get local_repo_path)
git status
```

3. 验证测试脚本：

```bash
cd $(python -m mcp_tool.cli config --get local_repo_path)
./{test_script}
```

## API参考

MCP工具提供了Python API，可以在自定义脚本中使用：

```python
from mcp_tool.mcp_central_coordinator import MCPCentralCoordinator

# 初始化协调器
coordinator = MCPCentralCoordinator(config_path="~/.powerautomation_mcp/config.json")

# 检查并下载release
download_result = coordinator.check_and_download_release(tag_name="v1.0.0")

# 运行测试并收集问题
test_result = coordinator.run_tests_and_collect_issues()

# 分析并解决问题
solution_result = coordinator.analyze_and_solve_issues()

# 上传更改
upload_result = coordinator.upload_changes(commit_message="自动更新")

# 运行完整工作流程
workflow_result = coordinator.run_full_workflow(tag_name="v1.0.0", auto_upload=True)

# 生成工作流程报告
report_result = coordinator.generate_workflow_report(workflow_result)
```

更多API详情，请参考代码文档或使用`help()`函数：

```python
import mcp_tool
help(mcp_tool)
```

---

如有任何问题或建议，请联系项目维护者或提交GitHub issue。
