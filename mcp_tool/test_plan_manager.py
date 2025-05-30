"""
测试计划管理模块 - 集中管理visual_test目录下的测试计划

该模块负责管理visual_test目录下的测试计划，提供统一的接口供TestAndIssueCollector访问。
所有测试计划都集中存放在visual_test/plans目录下，测试结果存放在visual_test/results目录下，
测试报告存放在visual_test/reports目录下。

作者: Manus AI
日期: 2025-05-30
"""

import os
import sys
import json
import time
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# 配置日志
logger = logging.getLogger("TestPlanManager")

class TestPlanManager:
    """
    测试计划管理类，负责管理visual_test目录下的测试计划
    """
    
    def __init__(self, 
                 mcp_repo_path: Optional[str] = None,
                 visual_test_dir: Optional[str] = None):
        """
        初始化测试计划管理器
        
        Args:
            mcp_repo_path: MCP仓库路径，如果为None则使用当前目录
            visual_test_dir: visual_test目录路径，如果为None则使用默认路径
        """
        self.mcp_repo_path = mcp_repo_path or os.path.abspath(os.path.dirname(__file__))
        self.visual_test_dir = visual_test_dir or os.path.join(self.mcp_repo_path, "visual_test")
        
        # 确保目录存在
        self.plans_dir = os.path.join(self.visual_test_dir, "plans")
        self.results_dir = os.path.join(self.visual_test_dir, "results")
        self.reports_dir = os.path.join(self.visual_test_dir, "reports")
        
        os.makedirs(self.plans_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        logger.info(f"测试计划管理器初始化完成")
        logger.info(f"MCP仓库路径: {self.mcp_repo_path}")
        logger.info(f"visual_test目录: {self.visual_test_dir}")
        logger.info(f"测试计划目录: {self.plans_dir}")
        logger.info(f"测试结果目录: {self.results_dir}")
        logger.info(f"测试报告目录: {self.reports_dir}")
    
    def list_test_plans(self) -> List[str]:
        """
        列出所有测试计划
        
        Returns:
            List[str]: 测试计划文件名列表
        """
        logger.info("列出所有测试计划")
        
        plans = []
        
        for file in os.listdir(self.plans_dir):
            if file.endswith(".json") or file.endswith(".yaml") or file.endswith(".yml"):
                plans.append(file)
        
        logger.info(f"找到 {len(plans)} 个测试计划")
        return plans
    
    def get_test_plan(self, plan_name: str) -> Dict[str, Any]:
        """
        获取测试计划
        
        Args:
            plan_name: 测试计划名称
            
        Returns:
            Dict[str, Any]: 测试计划内容
        """
        logger.info(f"获取测试计划: {plan_name}")
        
        plan_path = os.path.join(self.plans_dir, plan_name)
        
        if not os.path.exists(plan_path):
            logger.error(f"测试计划不存在: {plan_path}")
            return {}
        
        try:
            with open(plan_path, "r") as f:
                if plan_name.endswith(".json"):
                    plan = json.load(f)
                elif plan_name.endswith(".yaml") or plan_name.endswith(".yml"):
                    import yaml
                    plan = yaml.safe_load(f)
                else:
                    logger.error(f"不支持的测试计划格式: {plan_path}")
                    return {}
            
            logger.info(f"成功加载测试计划: {plan_path}")
            return plan
        except Exception as e:
            logger.error(f"加载测试计划失败: {plan_path}, {e}")
            return {}
    
    def create_test_plan(self, plan_name: str, plan_content: Dict[str, Any]) -> bool:
        """
        创建测试计划
        
        Args:
            plan_name: 测试计划名称
            plan_content: 测试计划内容
            
        Returns:
            bool: 是否成功创建
        """
        logger.info(f"创建测试计划: {plan_name}")
        
        # 确保文件名有正确的扩展名
        if not (plan_name.endswith(".json") or plan_name.endswith(".yaml") or plan_name.endswith(".yml")):
            plan_name = f"{plan_name}.json"
        
        plan_path = os.path.join(self.plans_dir, plan_name)
        
        try:
            with open(plan_path, "w") as f:
                if plan_name.endswith(".json"):
                    json.dump(plan_content, f, indent=2)
                elif plan_name.endswith(".yaml") or plan_name.endswith(".yml"):
                    import yaml
                    yaml.dump(plan_content, f)
                else:
                    logger.error(f"不支持的测试计划格式: {plan_path}")
                    return False
            
            logger.info(f"成功创建测试计划: {plan_path}")
            return True
        except Exception as e:
            logger.error(f"创建测试计划失败: {plan_path}, {e}")
            return False
    
    def update_test_plan(self, plan_name: str, plan_content: Dict[str, Any]) -> bool:
        """
        更新测试计划
        
        Args:
            plan_name: 测试计划名称
            plan_content: 测试计划内容
            
        Returns:
            bool: 是否成功更新
        """
        logger.info(f"更新测试计划: {plan_name}")
        
        # 确保文件名有正确的扩展名
        if not (plan_name.endswith(".json") or plan_name.endswith(".yaml") or plan_name.endswith(".yml")):
            plan_name = f"{plan_name}.json"
        
        plan_path = os.path.join(self.plans_dir, plan_name)
        
        if not os.path.exists(plan_path):
            logger.warning(f"测试计划不存在，将创建新的测试计划: {plan_path}")
            return self.create_test_plan(plan_name, plan_content)
        
        try:
            with open(plan_path, "w") as f:
                if plan_name.endswith(".json"):
                    json.dump(plan_content, f, indent=2)
                elif plan_name.endswith(".yaml") or plan_name.endswith(".yml"):
                    import yaml
                    yaml.dump(plan_content, f)
                else:
                    logger.error(f"不支持的测试计划格式: {plan_path}")
                    return False
            
            logger.info(f"成功更新测试计划: {plan_path}")
            return True
        except Exception as e:
            logger.error(f"更新测试计划失败: {plan_path}, {e}")
            return False
    
    def delete_test_plan(self, plan_name: str) -> bool:
        """
        删除测试计划
        
        Args:
            plan_name: 测试计划名称
            
        Returns:
            bool: 是否成功删除
        """
        logger.info(f"删除测试计划: {plan_name}")
        
        plan_path = os.path.join(self.plans_dir, plan_name)
        
        if not os.path.exists(plan_path):
            logger.warning(f"测试计划不存在: {plan_path}")
            return False
        
        try:
            os.remove(plan_path)
            logger.info(f"成功删除测试计划: {plan_path}")
            return True
        except Exception as e:
            logger.error(f"删除测试计划失败: {plan_path}, {e}")
            return False
    
    def save_test_result(self, plan_name: str, result: Dict[str, Any]) -> str:
        """
        保存测试结果
        
        Args:
            plan_name: 测试计划名称
            result: 测试结果
            
        Returns:
            str: 测试结果文件路径
        """
        logger.info(f"保存测试结果: {plan_name}")
        
        # 去除扩展名
        base_name = os.path.splitext(plan_name)[0]
        
        # 生成结果文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        result_name = f"{base_name}_{timestamp}.json"
        result_path = os.path.join(self.results_dir, result_name)
        
        try:
            with open(result_path, "w") as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"成功保存测试结果: {result_path}")
            return result_path
        except Exception as e:
            logger.error(f"保存测试结果失败: {result_path}, {e}")
            return ""
    
    def save_test_report(self, plan_name: str, report_content: str) -> str:
        """
        保存测试报告
        
        Args:
            plan_name: 测试计划名称
            report_content: 测试报告内容
            
        Returns:
            str: 测试报告文件路径
        """
        logger.info(f"保存测试报告: {plan_name}")
        
        # 去除扩展名
        base_name = os.path.splitext(plan_name)[0]
        
        # 生成报告文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_name = f"{base_name}_{timestamp}.md"
        report_path = os.path.join(self.reports_dir, report_name)
        
        try:
            with open(report_path, "w") as f:
                f.write(report_content)
            
            logger.info(f"成功保存测试报告: {report_path}")
            return report_path
        except Exception as e:
            logger.error(f"保存测试报告失败: {report_path}, {e}")
            return ""
    
    def get_latest_test_result(self, plan_name: str) -> Dict[str, Any]:
        """
        获取最新的测试结果
        
        Args:
            plan_name: 测试计划名称
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        logger.info(f"获取最新的测试结果: {plan_name}")
        
        # 去除扩展名
        base_name = os.path.splitext(plan_name)[0]
        
        # 查找所有匹配的结果文件
        result_files = []
        for file in os.listdir(self.results_dir):
            if file.startswith(f"{base_name}_") and file.endswith(".json"):
                result_files.append(file)
        
        if not result_files:
            logger.warning(f"未找到测试结果: {plan_name}")
            return {}
        
        # 按时间戳排序
        result_files.sort(reverse=True)
        latest_result = result_files[0]
        
        try:
            with open(os.path.join(self.results_dir, latest_result), "r") as f:
                result = json.load(f)
            
            logger.info(f"成功加载最新的测试结果: {latest_result}")
            return result
        except Exception as e:
            logger.error(f"加载测试结果失败: {latest_result}, {e}")
            return {}
    
    def get_latest_test_report(self, plan_name: str) -> str:
        """
        获取最新的测试报告
        
        Args:
            plan_name: 测试计划名称
            
        Returns:
            str: 测试报告内容
        """
        logger.info(f"获取最新的测试报告: {plan_name}")
        
        # 去除扩展名
        base_name = os.path.splitext(plan_name)[0]
        
        # 查找所有匹配的报告文件
        report_files = []
        for file in os.listdir(self.reports_dir):
            if file.startswith(f"{base_name}_") and file.endswith(".md"):
                report_files.append(file)
        
        if not report_files:
            logger.warning(f"未找到测试报告: {plan_name}")
            return ""
        
        # 按时间戳排序
        report_files.sort(reverse=True)
        latest_report = report_files[0]
        
        try:
            with open(os.path.join(self.reports_dir, latest_report), "r") as f:
                report = f.read()
            
            logger.info(f"成功加载最新的测试报告: {latest_report}")
            return report
        except Exception as e:
            logger.error(f"加载测试报告失败: {latest_report}, {e}")
            return ""
    
    def create_default_test_plans(self) -> bool:
        """
        创建默认的测试计划
        
        Returns:
            bool: 是否成功创建
        """
        logger.info("创建默认的测试计划")
        
        # 基本功能测试计划
        basic_plan = {
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
        
        # 集成测试计划
        integration_plan = {
            "name": "集成测试",
            "description": "测试MCP工具的集成功能",
            "tests": [
                {
                    "name": "测试工具发现",
                    "description": "测试工具发现功能",
                    "tool": "mcp_tool_discovery",
                    "method": "discover_all_tools",
                    "args": {},
                    "expected": {
                        "status": "success"
                    }
                },
                {
                    "name": "测试工具生成",
                    "description": "测试工具生成功能",
                    "tool": "mcp_brainstorm",
                    "method": "generate_tool",
                    "args": {
                        "tool_name": "test_tool"
                    },
                    "expected": {
                        "status": "success"
                    }
                }
            ]
        }
        
        # 性能测试计划
        performance_plan = {
            "name": "性能测试",
            "description": "测试MCP工具的性能",
            "tests": [
                {
                    "name": "测试mcp_brainstorm性能",
                    "description": "测试mcp_brainstorm的性能",
                    "tool": "mcp_brainstorm",
                    "method": "analyze_capability_coverage",
                    "args": {},
                    "expected": {
                        "status": "success",
                        "time_limit": 5.0
                    }
                },
                {
                    "name": "测试mcp_planner性能",
                    "description": "测试mcp_planner的性能",
                    "tool": "mcp_planner",
                    "method": "find_matching_mcp",
                    "args": {
                        "sample": "测试样本"
                    },
                    "expected": {
                        "status": "success",
                        "time_limit": 2.0
                    }
                }
            ]
        }
        
        # 创建测试计划
        success = True
        success = success and self.create_test_plan("basic_test_plan.json", basic_plan)
        success = success and self.create_test_plan("integration_test_plan.json", integration_plan)
        success = success and self.create_test_plan("performance_test_plan.json", performance_plan)
        
        return success


def main():
    """主函数"""
    import argparse
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="测试计划管理")
    parser.add_argument("--mcp_repo_path", help="MCP仓库路径")
    parser.add_argument("--visual_test_dir", help="visual_test目录路径")
    parser.add_argument("--list", action="store_true", help="列出所有测试计划")
    parser.add_argument("--create_default", action="store_true", help="创建默认的测试计划")
    parser.add_argument("--get_plan", help="获取测试计划")
    
    args = parser.parse_args()
    
    # 创建测试计划管理器
    manager = TestPlanManager(
        mcp_repo_path=args.mcp_repo_path,
        visual_test_dir=args.visual_test_dir
    )
    
    # 列出所有测试计划
    if args.list:
        plans = manager.list_test_plans()
        print("测试计划列表:")
        for plan in plans:
            print(f"- {plan}")
    
    # 创建默认的测试计划
    if args.create_default:
        success = manager.create_default_test_plans()
        if success:
            print("成功创建默认的测试计划")
        else:
            print("创建默认的测试计划失败")
    
    # 获取测试计划
    if args.get_plan:
        plan = manager.get_test_plan(args.get_plan)
        print(f"测试计划: {args.get_plan}")
        print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
