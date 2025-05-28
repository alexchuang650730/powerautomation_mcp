"""
测试自动化测试与问题收集器模块

该脚本用于测试TestAndIssueCollector模块的功能，包括：
1. 运行测试脚本
2. 收集问题
3. 更新README
4. 生成测试报告

作者: Manus AI
日期: 2025-05-28
"""

import os
import sys
import time
import json

# 添加父目录到系统路径，以便导入mcp_tool包
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tool.thought_action_recorder import ThoughtActionRecorder
from mcp_tool.test_issue_collector import TestAndIssueCollector

def test_collector():
    """测试TestAndIssueCollector的基本功能"""
    print("开始测试TestAndIssueCollector...")
    
    # 创建测试目录
    test_repo_dir = os.path.join(os.getcwd(), "test_repo")
    os.makedirs(test_repo_dir, exist_ok=True)
    
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
    
    # 初始化记录器
    recorder = ThoughtActionRecorder(log_dir=os.path.join(test_repo_dir, "logs"))
    
    # 初始化测试与问题收集器
    collector = TestAndIssueCollector(
        repo_path=test_repo_dir,
        test_script="start_and_test.sh",
        readme_path="README.md",
        recorder=recorder
    )
    
    print(f"测试与问题收集器初始化完成，仓库路径: {test_repo_dir}")
    
    # 测试运行测试脚本
    print("\n测试运行测试脚本...")
    test_result = collector.run_tests()
    
    if test_result["success"]:
        print("测试脚本运行成功")
    else:
        print(f"测试脚本运行失败: {test_result.get('error')}")
        print("继续测试其他功能...")
    
    # 测试收集问题
    print("\n测试收集问题...")
    issues = collector.collect_issues()
    
    print(f"收集到 {len(issues)} 个问题:")
    for i, issue in enumerate(issues, 1):
        print(f"- 问题 {i}: {issue['type']} in {issue['file']}")
    
    # 测试更新README
    print("\n测试更新README...")
    readme_result = collector.update_readme(issues)
    
    if readme_result["success"]:
        print(f"成功更新README，添加了 {readme_result['issues_count']} 个问题")
    else:
        print(f"更新README失败: {readme_result.get('error')}")
    
    # 测试生成测试报告
    print("\n测试生成测试报告...")
    report_result = collector.generate_test_report(test_result, issues)
    
    if report_result["success"]:
        print(f"成功生成测试报告: {report_result['report_path']}")
    else:
        print(f"生成测试报告失败: {report_result.get('error')}")
    
    # 测试归档测试结果
    print("\n测试归档测试结果...")
    archive_result = collector.archive_test_results()
    
    if archive_result["success"]:
        print(f"成功归档测试结果: {archive_result['archive_dir']}")
    else:
        print(f"归档测试结果失败: {archive_result.get('error')}")
    
    print("\n测试完成!")
    return collector

if __name__ == "__main__":
    collector = test_collector()
