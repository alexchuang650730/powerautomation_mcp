"""
测试Manus问题解决驱动器模块

该脚本用于测试ManusProblemSolver模块的功能，包括：
1. 从README中提取问题
2. 分析问题
3. 生成修复策略
4. 生成测试方案
5. 更新README

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
from mcp_tool.manus_problem_solver import ManusProblemSolver

def test_problem_solver():
    """测试ManusProblemSolver的基本功能"""
    print("开始测试ManusProblemSolver...")
    
    # 创建测试目录
    test_repo_dir = os.path.join(os.getcwd(), "test_repo")
    os.makedirs(test_repo_dir, exist_ok=True)
    
    # 创建测试README文件，包含问题部分
    readme_path = os.path.join(test_repo_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write("""# PowerAutomation

This is a test README file for PowerAutomation.

## Features

- Feature 1
- Feature 2
- Feature 3

## 测试发现的问题

测试发现以下问题：

1. **ERROR**: test_file.log
   ```
   [ERR] ImportError: No module named 'missing_module'
   ```

2. **WARNING**: permission_test.log
   ```
   [WARN] Permission denied: /path/to/file.txt
   ```

3. **ERROR**: network_test.log
   ```
   [ERR] Connection timeout after 30 seconds
   ```

*测试时间: 2025-05-28 08:30:00*

## Installation

Instructions for installation...

## Usage

Instructions for usage...
""")
    
    # 初始化记录器
    recorder = ThoughtActionRecorder(log_dir=os.path.join(test_repo_dir, "logs"))
    
    # 初始化Manus问题解决驱动器
    solver = ManusProblemSolver(
        repo_path=test_repo_dir,
        readme_path="README.md",
        recorder=recorder
    )
    
    print(f"Manus问题解决驱动器初始化完成，仓库路径: {test_repo_dir}")
    
    # 测试从README中提取问题
    print("\n测试从README中提取问题...")
    issues = solver.extract_issues_from_readme()
    
    print(f"从README中提取到 {len(issues)} 个问题:")
    for i, issue in enumerate(issues, 1):
        print(f"- 问题 {i}: {issue['type']} in {issue['file']}")
    
    # 如果有问题，测试分析问题
    if issues:
        print("\n测试分析问题...")
        analysis = solver.analyze_issue(issues[0])
        
        print(f"问题分析结果:")
        print(f"- 问题类别: {analysis['problem_category']}")
        print(f"- 严重性: {analysis['severity']}")
        print(f"- 可能原因: {', '.join(analysis['possible_causes'])}")
        print(f"- 受影响组件: {', '.join(analysis['affected_components'])}")
        
        # 测试生成修复策略
        print("\n测试生成修复策略...")
        fix_strategy = solver.generate_fix_strategy(analysis)
        
        print(f"修复策略:")
        print(f"- 优先级: {fix_strategy['priority']}")
        print(f"- 预估工作量: {fix_strategy['estimated_effort']}")
        print(f"- 推荐操作: {', '.join(fix_strategy['recommended_actions'])}")
        
        # 测试生成测试方案
        print("\n测试生成测试方案...")
        test_plan = solver.generate_test_plan(fix_strategy)
        
        print(f"测试方案:")
        print(f"- 测试用例数量: {len(test_plan['test_cases'])}")
        print(f"- 验证步骤: {', '.join(test_plan['verification_steps'])}")
    
    # 测试处理所有问题
    print("\n测试处理所有问题...")
    process_result = solver.process_all_issues()
    
    if process_result["success"]:
        print(f"成功处理 {process_result['issues_count']} 个问题")
        if "results_file" in process_result:
            print(f"结果保存在: {process_result['results_file']}")
        if "summary_file" in process_result:
            print(f"摘要报告保存在: {process_result['summary_file']}")
    else:
        print(f"处理问题失败: {process_result.get('error')}")
    
    # 测试更新README
    print("\n测试更新README，添加解决方案...")
    update_result = solver.update_readme_with_solutions(process_result.get("results", []))
    
    if update_result["success"]:
        print(f"成功更新README，添加了 {update_result['solutions_count']} 个解决方案")
    else:
        print(f"更新README失败: {update_result.get('error')}")
    
    print("\n测试完成!")
    return solver

if __name__ == "__main__":
    solver = test_problem_solver()
