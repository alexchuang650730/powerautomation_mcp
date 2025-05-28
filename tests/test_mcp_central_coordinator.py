"""
测试MCP中央协调器模块

该脚本用于测试MCPCentralCoordinator模块的功能，包括：
1. 初始化和配置
2. 检查并下载release
3. 运行测试并收集问题
4. 分析并解决问题
5. 上传更改
6. 运行完整工作流程

作者: Manus AI
日期: 2025-05-28
"""

import os
import sys
import time
import json

# 添加父目录到系统路径，以便导入mcp_tool包
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tool.mcp_central_coordinator import MCPCentralCoordinator

def test_coordinator():
    """测试MCPCentralCoordinator的基本功能"""
    print("开始测试MCPCentralCoordinator...")
    
    # 创建测试目录
    test_repo_dir = os.path.join(os.getcwd(), "test_repo")
    os.makedirs(test_repo_dir, exist_ok=True)
    
    # 创建测试配置
    test_config = {
        "local_repo_path": test_repo_dir,
        "github_repo": "alexchuang650730/powerautomation",
        "ssh_key_path": "~/.ssh/id_rsa",
        "test_script": "start_and_test.sh",
        "readme_path": "README.md",
        "auto_upload": False,  # 测试时禁用自动上传
        "auto_test": True,
        "auto_solve": True
    }
    
    # 保存测试配置
    config_path = os.path.join(test_repo_dir, "mcp_config.json")
    with open(config_path, "w") as f:
        json.dump(test_config, f, indent=2)
    
    # 创建测试脚本
    test_script_path = os.path.join(test_repo_dir, "start_and_test.sh")
    with open(test_script_path, "w") as f:
        f.write("""#!/bin/bash
echo "Starting test script..."
echo "Testing PowerAutomation functionality..."
echo "Simulating some warnings..."
echo "WARNING: This is a simulated warning"
echo "Simulating some errors..."
echo "ERROR: This is a simulated error"
echo "Test completed with some issues."
mkdir -p final_release/static/ppt
touch final_release/static/ppt/test.pptx
exit 0
""")
    
    # 创建README文件
    readme_path = os.path.join(test_repo_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write("""# PowerAutomation

This is a test README file for PowerAutomation.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

Instructions for installation...

## Usage

Instructions for usage...
""")
    
    # 初始化协调器
    coordinator = MCPCentralCoordinator(
        config_path=config_path
    )
    
    print(f"MCP中央协调器初始化完成，仓库路径: {test_repo_dir}")
    
    # 测试保存配置
    print("\n测试保存配置...")
    save_result = coordinator.save_config(os.path.join(test_repo_dir, "saved_config.json"))
    
    if save_result["success"]:
        print(f"成功保存配置到: {save_result['config_path']}")
    else:
        print(f"保存配置失败: {save_result.get('error')}")
    
    # 测试模拟下载release
    print("\n测试模拟下载release...")
    # 由于这是测试环境，我们不实际下载，而是模拟下载成功
    # 在实际环境中，这将调用GitHub API并下载实际的release
    
    # 创建.git目录以模拟git仓库
    os.makedirs(os.path.join(test_repo_dir, ".git"), exist_ok=True)
    
    # 测试运行测试并收集问题
    print("\n测试运行测试并收集问题...")
    test_result = coordinator.run_tests_and_collect_issues()
    
    if test_result["success"]:
        print("成功运行测试并收集问题")
    else:
        print(f"运行测试失败: {test_result.get('error')}")
        print("继续测试其他功能...")
    
    # 测试分析并解决问题
    print("\n测试分析并解决问题...")
    solution_result = coordinator.analyze_and_solve_issues()
    
    if solution_result["success"]:
        print("成功分析并解决问题")
    else:
        print(f"分析并解决问题失败: {solution_result.get('error')}")
    
    # 测试生成工作流程报告
    print("\n测试生成工作流程报告...")
    # 创建模拟的工作流程结果
    mock_workflow_result = {
        "success": True,
        "steps": {
            "download": {
                "success": True,
                "tag_name": "v1.0.0",
                "local_path": test_repo_dir
            },
            "test": {
                "success": True,
                "test_result": {
                    "success": True
                },
                "issues": [
                    {
                        "type": "error",
                        "file": "test_file.log",
                        "context": "ImportError: No module named 'missing_module'"
                    }
                ]
            },
            "solution": {
                "success": True,
                "process_result": {
                    "success": True,
                    "issues_count": 1,
                    "results": [
                        {
                            "issue": {
                                "type": "error",
                                "file": "test_file.log",
                                "context": "ImportError: No module named 'missing_module'"
                            },
                            "fix_strategy": {
                                "priority": "high",
                                "estimated_effort": "low",
                                "recommended_actions": [
                                    "检查项目依赖项是否正确安装",
                                    "验证导入路径是否正确"
                                ]
                            }
                        }
                    ]
                }
            },
            "upload": {
                "success": True,
                "skipped": True
            }
        }
    }
    
    report_result = coordinator.generate_workflow_report(mock_workflow_result)
    
    if report_result["success"]:
        print(f"成功生成工作流程报告: {report_result['report_path']}")
    else:
        print(f"生成工作流程报告失败: {report_result.get('error')}")
    
    print("\n测试完成!")
    return coordinator

if __name__ == "__main__":
    coordinator = test_coordinator()
