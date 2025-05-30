# MCP自动化测试指南

## 简介

本文档介绍了基于MCP（Model Context Protocol）的自动化测试框架，该框架集成了Gemma 3 8B中文版模型，实现了无脚本自动化测试。通过本指南，您将了解如何设置、配置和使用这个自动化测试系统。

## 架构概述

MCP自动化测试框架由以下核心组件组成：

1. **Gemma 3 8B中文版模型**：作为主要的大语言模型，负责生成测试用例、分析测试结果
2. **MCP工具发现与生成模块**：自动发现和加载mcp.so等工具，缺失时自动生成
3. **测试计划管理模块**：集中管理visual_test目录下的测试计划
4. **增强版TestAndIssueCollector**：自动访问测试计划并驱动测试执行
5. **统一配置管理**：为所有模块提供配置支持

## 目录结构

```
powerautomation_mcp/
├── mcp_tool/
│   ├── unified_config.py          # 统一配置管理
│   ├── mcp_tool_discovery.py      # MCP工具发现与生成
│   ├── test_plan_manager.py       # 测试计划管理
│   ├── enhanced_test_collector.py # 增强版测试与问题收集器
│   ├── test_issue_collector.py    # 基础测试与问题收集器
│   ├── mcp_brainstorm.py          # MCP头脑风暴工具
│   └── ...
├── visual_test/
│   ├── plans/                     # 测试计划目录
│   ├── results/                   # 测试结果目录
│   └── reports/                   # 测试报告目录
├── docs/
│   ├── architecture_diagram.md    # 架构设计图
│   ├── mcp_automation_testing_guide.md # 本指南
│   └── ...
└── mcp_integration_framework.py   # MCP集成框架
```

## 安装与设置

### 前提条件

- Python 3.8+
- PyTorch 2.0+
- Transformers 4.30+
- 足够的磁盘空间（至少10GB）用于存储模型
- 推荐：NVIDIA GPU（8GB+显存）用于加速模型推理

### 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/alexchuang650730/powerautomation_mcp.git
cd powerautomation_mcp
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **下载Gemma 3 8B中文版模型**

```bash
python -m mcp_integration_framework.py --setup
```

## 使用方法

### 基本用法

运行完整的自动化测试工作流：

```bash
python -m mcp_integration_framework.py --workflow
```

这将执行以下步骤：
1. 初始化Gemma 3 8B中文版模型
2. 创建默认测试计划（如果不存在）
3. 运行所有测试计划
4. 收集测试结果和问题
5. 更新README文件

### 分步执行

如果您希望分步执行工作流，可以使用以下命令：

```bash
# 设置环境
python -m mcp_integration_framework.py --setup

# 运行测试
python -m mcp_integration_framework.py --test

# 生成报告
python -m mcp_integration_framework.py --report
```

### 使用增强版TestAndIssueCollector

增强版TestAndIssueCollector提供了更多功能：

```bash
# 运行完整工作流程
python -m mcp_tool.enhanced_test_collector --workflow

# 只运行测试
python -m mcp_tool.enhanced_test_collector --run_tests

# 只收集问题
python -m mcp_tool.enhanced_test_collector --collect_issues

# 只更新README
python -m mcp_tool.enhanced_test_collector --update_readme
```

## 测试计划管理

### 测试计划格式

测试计划使用JSON或YAML格式，存放在`visual_test/plans`目录下。一个典型的测试计划如下：

```json
{
  "name": "基本功能测试",
  "description": "测试MCP工具的基本功能",
  "tests": [
    {
      "name": "测试mcp_brainstorm",
      "description": "测试mcp_brainstorm的基本功能",
      "tool": "mcp_brainstorm",
      "method": "analyze_capability_coverage",
      "args": {},
      "expected": {
        "status": "success"
      }
    },
    {
      "name": "测试mcp_planner",
      "description": "测试mcp_planner的基本功能",
      "tool": "mcp_planner",
      "method": "find_matching_mcp",
      "args": {
        "sample": "测试样本"
      },
      "expected": {
        "status": "success"
      }
    }
  ]
}
```

### 管理测试计划

使用测试计划管理器管理测试计划：

```bash
# 列出所有测试计划
python -m mcp_tool.test_plan_manager --list

# 创建默认测试计划
python -m mcp_tool.test_plan_manager --create_default

# 获取测试计划
python -m mcp_tool.test_plan_manager --get_plan basic_test_plan.json
```

## MCP工具发现与生成

MCP工具发现与生成模块负责自动发现和加载mcp.so等工具，当发现工具不足时，自动调用mcp_brainstorm生成所需工具。

### 工具发现机制

工具发现按以下顺序进行：

1. 查找二进制工具（如mcp.so）
2. 查找Python工具（如mcp_brainstorm.py）
3. 如果找不到所需工具，使用mcp_brainstorm生成

### 使用工具发现

```python
from mcp_tool.mcp_tool_discovery import MCPToolDiscovery

# 创建工具发现器
discovery = MCPToolDiscovery()

# 发现所有工具
tools = discovery.discover_all_tools()

# 获取特定工具
tool = discovery.get_tool("mcp_brainstorm")

# 使用工具
result = tool.analyze_capability_coverage()
```

## 集成Gemma 3 8B中文版模型

MCP集成框架专注于Gemma 3 8B中文版模型，提供了简单的接口用于生成文本和执行测试。

### 使用Gemma模型

```python
from mcp_integration_framework import GemmaMCPIntegration

# 创建集成实例
integration = GemmaMCPIntegration()

# 初始化模型
integration.initialize_model()

# 生成文本
response = integration.generate_text("请分析以下测试结果并提出改进建议：...")

# 执行测试
test_result = integration.run_test({
    "name": "测试mcp_brainstorm",
    "tool": "mcp_brainstorm",
    "method": "analyze_capability_coverage",
    "args": {}
})
```

## 测试结果与报告

测试结果保存在`visual_test/results`目录下，测试报告保存在`visual_test/reports`目录下。

### 测试结果格式

测试结果使用JSON格式，包含以下信息：

- 测试计划名称和描述
- 测试状态（成功/失败）
- 测试总数、成功数和失败数
- 每个测试的详细结果

### 测试报告格式

测试报告使用Markdown格式，包含以下内容：

- 测试计划名称和描述
- 测试摘要（总数、成功数、失败数、通过率）
- 每个测试的详细结果
- Gemma模型生成的测试总结

## 问题收集与处理

增强版TestAndIssueCollector会自动从测试结果中收集问题，并更新到README文件中。

### 问题格式

每个问题包含以下信息：

- 标题：测试失败的名称
- 描述：错误信息
- 测试计划名称
- 测试名称
- 严重程度（高/中/低）

### README更新

README文件会自动更新，添加测试结果摘要，包括：

- 测试计划名称
- 状态（成功/失败）
- 通过率
- 最后运行时间

## 最佳实践

### 编写有效的测试计划

1. **明确测试目标**：每个测试应该有明确的目标和预期结果
2. **合理组织测试**：将相关测试组织在同一个测试计划中
3. **详细描述**：提供足够的描述信息，帮助理解测试目的
4. **合理设置预期**：设置合理的预期结果，避免误报

### 优化模型性能

1. **使用GPU加速**：如果可能，使用GPU加速模型推理
2. **优化提示文本**：编写清晰、简洁的提示文本
3. **调整生成参数**：根据需要调整温度、top_p等参数

### 处理测试失败

1. **分析失败原因**：仔细分析测试失败的原因
2. **修复问题**：根据失败原因修复问题
3. **重新运行测试**：修复后重新运行测试
4. **更新测试计划**：如果需要，更新测试计划

## 常见问题

### Q: 如何添加新的测试计划？

A: 在`visual_test/plans`目录下创建新的JSON或YAML文件，按照测试计划格式编写测试计划。

### Q: 如何使用自己的模型？

A: 虽然框架专注于Gemma 3 8B中文版模型，但保留了对其他模型的扩展支持。您可以修改`mcp_integration_framework.py`中的`ModelAdapter`类，添加对新模型的支持。

### Q: 测试执行很慢，如何优化？

A: 确保使用GPU加速，减少测试数量，优化测试执行顺序，避免不必要的模型调用。

### Q: 如何处理工具不存在的情况？

A: 框架会自动使用mcp_brainstorm生成缺失的工具。如果生成的工具不满足需求，您可以手动实现并放置在正确的位置。

## 故障排除

### 模型加载失败

- 检查模型路径是否正确
- 确保有足够的磁盘空间和内存
- 检查是否安装了正确版本的PyTorch和Transformers

### 测试执行失败

- 检查测试计划格式是否正确
- 确保所需的工具已正确安装
- 查看日志文件获取详细错误信息

### 工具发现失败

- 检查工具路径是否正确
- 确保工具具有正确的权限
- 尝试手动加载工具进行测试

## 结论

MCP自动化测试框架提供了一种强大的方式，利用Gemma 3 8B中文版模型实现无脚本自动化测试。通过自动发现和生成工具、集中管理测试计划、自动执行测试和收集问题，该框架大大提高了测试效率和质量。

希望本指南能帮助您充分利用MCP自动化测试框架，如有任何问题或建议，请随时联系我们。
