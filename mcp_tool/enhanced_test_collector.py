"""
TestAndIssueCollector集成模块 - 实现对visual_test/plans的自动访问与用例驱动

该模块扩展了TestAndIssueCollector，使其能够自动访问visual_test/plans目录下的测试计划，
并驱动Gemma 3 8B中文版模型与MCP工具进行自动化测试。

作者: Manus AI
日期: 2025-05-30
"""

import os
import sys
import json
import time
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# 配置日志
logger = logging.getLogger("TestAndIssueCollectorIntegration")

# 导入必要的模块
try:
    from mcp_tool.test_issue_collector import TestAndIssueCollector
    from mcp_tool.test_plan_manager import TestPlanManager
    from mcp_tool.mcp_tool_discovery import MCPToolDiscovery
except ImportError:
    logger.error("导入必要的模块失败，请确保相关模块已安装")
    sys.exit(1)

class EnhancedTestAndIssueCollector(TestAndIssueCollector):
    """
    增强版TestAndIssueCollector，支持自动访问visual_test/plans目录下的测试计划
    """
    
    def __init__(self, 
                 repo_path: Optional[str] = None,
                 test_script: Optional[str] = None,
                 readme_path: Optional[str] = None,
                 visual_test_dir: Optional[str] = None,
                 gemma_model_path: Optional[str] = None,
                 use_gpu: bool = True):
        """
        初始化增强版TestAndIssueCollector
        
        Args:
            repo_path: 仓库路径，如果为None则使用当前目录
            test_script: 测试脚本路径，如果为None则使用默认脚本
            readme_path: README文件路径，如果为None则使用默认路径
            visual_test_dir: visual_test目录路径，如果为None则使用默认路径
            gemma_model_path: Gemma模型路径，如果为None则使用默认路径
            use_gpu: 是否使用GPU，默认为True
        """
        # 初始化基类
        super().__init__(repo_path, test_script, readme_path)
        
        # 设置visual_test目录
        self.visual_test_dir = visual_test_dir or os.path.join(self.repo_path, "visual_test")
        
        # 创建测试计划管理器
        self.test_plan_manager = TestPlanManager(
            mcp_repo_path=self.repo_path,
            visual_test_dir=self.visual_test_dir
        )
        
        # 创建工具发现器
        self.tool_discovery = MCPToolDiscovery(
            mcp_repo_path=self.repo_path
        )
        
        # 发现工具
        self.discovered_tools = self.tool_discovery.discover_all_tools()
        
        # Gemma模型配置
        self.gemma_model_path = gemma_model_path
        self.use_gpu = use_gpu
        self.gemma_model = None
        
        logger.info(f"增强版TestAndIssueCollector初始化完成")
        logger.info(f"仓库路径: {self.repo_path}")
        logger.info(f"visual_test目录: {self.visual_test_dir}")
        logger.info(f"发现的工具数量: {len(self.discovered_tools)}")
    
    def initialize_gemma_model(self) -> bool:
        """
        初始化Gemma模型
        
        Returns:
            bool: 是否成功初始化
        """
        logger.info(f"初始化Gemma模型")
        
        try:
            # 导入必要的库
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # 设置设备
            device = "cuda" if torch.cuda.is_available() and self.use_gpu else "cpu"
            logger.info(f"使用设备: {device}")
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(self.gemma_model_path)
            
            # 加载模型
            self.gemma_model = AutoModelForCausalLM.from_pretrained(
                self.gemma_model_path,
                device_map="auto" if device == "cuda" else None,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )
            
            logger.info(f"Gemma模型加载成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化Gemma模型失败: {e}")
            return False
    
    def generate_with_gemma(self, prompt: str, **kwargs) -> str:
        """
        使用Gemma模型生成文本
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        try:
            # 检查模型是否已加载
            if self.gemma_model is None:
                logger.warning("模型未加载，先加载模型")
                if not self.initialize_gemma_model():
                    return "错误: 模型初始化失败"
            
            # 设置默认参数
            max_new_tokens = kwargs.get("max_new_tokens", 500)
            temperature = kwargs.get("temperature", 0.7)
            top_p = kwargs.get("top_p", 0.9)
            do_sample = kwargs.get("do_sample", True)
            
            # 生成文本
            import torch
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.use_gpu and torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            outputs = self.gemma_model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample
            )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 移除提示文本
            if response.startswith(prompt):
                response = response[len(prompt):]
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"生成文本失败: {e}")
            return f"生成失败: {str(e)}"
    
    def run_tests_from_plans(self, plan_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        从测试计划运行测试
        
        Args:
            plan_names: 测试计划名称列表，如果为None则运行所有测试计划
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        logger.info(f"从测试计划运行测试")
        
        # 获取测试计划列表
        if plan_names is None:
            plan_names = self.test_plan_manager.list_test_plans()
        
        # 测试结果
        results = {
            "total_plans": len(plan_names),
            "successful_plans": 0,
            "failed_plans": 0,
            "plan_results": {}
        }
        
        # 运行每个测试计划
        for plan_name in plan_names:
            logger.info(f"运行测试计划: {plan_name}")
            
            # 获取测试计划
            plan = self.test_plan_manager.get_test_plan(plan_name)
            
            if not plan:
                logger.error(f"测试计划加载失败: {plan_name}")
                results["failed_plans"] += 1
                results["plan_results"][plan_name] = {
                    "status": "failed",
                    "error": "测试计划加载失败"
                }
                continue
            
            # 运行测试计划
            plan_result = self._run_test_plan(plan_name, plan)
            
            # 保存测试结果
            result_path = self.test_plan_manager.save_test_result(plan_name, plan_result)
            
            # 生成测试报告
            report_content = self._generate_test_report(plan_name, plan, plan_result)
            report_path = self.test_plan_manager.save_test_report(plan_name, report_content)
            
            # 更新结果
            if plan_result.get("status") == "success":
                results["successful_plans"] += 1
            else:
                results["failed_plans"] += 1
            
            results["plan_results"][plan_name] = {
                "status": plan_result.get("status", "unknown"),
                "result_path": result_path,
                "report_path": report_path
            }
        
        return results
    
    def _run_test_plan(self, plan_name: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行测试计划
        
        Args:
            plan_name: 测试计划名称
            plan: 测试计划内容
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        logger.info(f"运行测试计划: {plan_name}")
        
        # 测试结果
        result = {
            "name": plan.get("name", plan_name),
            "description": plan.get("description", ""),
            "status": "success",
            "total_tests": len(plan.get("tests", [])),
            "successful_tests": 0,
            "failed_tests": 0,
            "test_results": []
        }
        
        # 运行每个测试
        for test in plan.get("tests", []):
            logger.info(f"运行测试: {test.get('name', 'unknown')}")
            
            # 运行测试
            test_result = self._run_test(test)
            
            # 更新结果
            if test_result.get("status") == "success":
                result["successful_tests"] += 1
            else:
                result["failed_tests"] += 1
                # 如果有任何测试失败，整个计划状态为失败
                result["status"] = "failed"
            
            result["test_results"].append(test_result)
        
        return result
    
    def _run_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行测试
        
        Args:
            test: 测试内容
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        logger.info(f"运行测试: {test.get('name', 'unknown')}")
        
        # 测试结果
        result = {
            "name": test.get("name", "unknown"),
            "description": test.get("description", ""),
            "status": "success",
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
            "output": None,
            "error": None
        }
        
        try:
            # 获取工具和方法
            tool_name = test.get("tool")
            method_name = test.get("method")
            args = test.get("args", {})
            expected = test.get("expected", {})
            
            # 检查是否需要使用Gemma模型
            if tool_name == "gemma":
                # 使用Gemma模型生成文本
                prompt = args.get("prompt", "")
                output = self.generate_with_gemma(prompt, **args)
                result["output"] = output
                
                # 检查是否符合预期
                if "expected_text" in expected:
                    expected_text = expected["expected_text"]
                    if expected_text not in output:
                        result["status"] = "failed"
                        result["error"] = f"输出不包含预期文本: {expected_text}"
            else:
                # 获取工具
                tool = self.tool_discovery.get_tool(tool_name)
                
                if not tool:
                    result["status"] = "failed"
                    result["error"] = f"工具不存在: {tool_name}"
                    return result
                
                # 如果指定了方法，则调用方法
                if method_name:
                    if hasattr(tool, method_name):
                        method = getattr(tool, method_name)
                        output = method(**args)
                    else:
                        result["status"] = "failed"
                        result["error"] = f"方法不存在: {method_name}"
                        return result
                else:
                    # 直接调用工具
                    output = tool(**args)
                
                result["output"] = output
                
                # 检查是否符合预期
                if "status" in expected:
                    expected_status = expected["status"]
                    if isinstance(output, dict) and "status" in output:
                        if output["status"] != expected_status:
                            result["status"] = "failed"
                            result["error"] = f"状态不匹配: 预期 {expected_status}，实际 {output['status']}"
                
                # 检查时间限制
                if "time_limit" in expected:
                    time_limit = expected["time_limit"]
                    if result["duration"] > time_limit:
                        result["status"] = "failed"
                        result["error"] = f"执行时间超过限制: 预期 {time_limit}s，实际 {result['duration']}s"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
        finally:
            # 记录结束时间和持续时间
            result["end_time"] = time.time()
            result["duration"] = result["end_time"] - result["start_time"]
        
        return result
    
    def _generate_test_report(self, plan_name: str, plan: Dict[str, Any], result: Dict[str, Any]) -> str:
        """
        生成测试报告
        
        Args:
            plan_name: 测试计划名称
            plan: 测试计划内容
            result: 测试结果
            
        Returns:
            str: 测试报告内容
        """
        logger.info(f"生成测试报告: {plan_name}")
        
        # 报告标题
        report = f"# 测试报告: {result.get('name', plan_name)}\n\n"
        
        # 报告时间
        report += f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 测试计划描述
        if result.get("description"):
            report += f"## 描述\n\n{result.get('description')}\n\n"
        
        # 测试摘要
        report += f"## 测试摘要\n\n"
        report += f"- 总测试数: {result.get('total_tests', 0)}\n"
        report += f"- 成功测试数: {result.get('successful_tests', 0)}\n"
        report += f"- 失败测试数: {result.get('failed_tests', 0)}\n"
        
        # 计算通过率
        pass_rate = 0
        if result.get("total_tests", 0) > 0:
            pass_rate = result.get("successful_tests", 0) / result.get("total_tests", 0) * 100
        report += f"- 通过率: {pass_rate:.2f}%\n\n"
        
        # 测试结果
        report += f"## 测试结果\n\n"
        
        for i, test_result in enumerate(result.get("test_results", []), 1):
            report += f"### {i}. {test_result.get('name', 'unknown')}\n\n"
            
            if test_result.get("description"):
                report += f"{test_result.get('description')}\n\n"
            
            report += f"状态: **{test_result.get('status', 'unknown')}**\n\n"
            
            if test_result.get("error"):
                report += f"错误: {test_result.get('error')}\n\n"
            
            report += f"执行时间: {test_result.get('duration', 0):.4f}s\n\n"
            
            # 输出结果
            if test_result.get("output"):
                report += f"输出:\n\n```\n{json.dumps(test_result.get('output'), indent=2, ensure_ascii=False)}\n```\n\n"
        
        # 使用Gemma模型生成测试总结
        if self.gemma_model:
            try:
                prompt = f"""
请根据以下测试结果生成一个简短的总结，包括主要发现和改进建议：

测试计划: {result.get('name', plan_name)}
总测试数: {result.get('total_tests', 0)}
成功测试数: {result.get('successful_tests', 0)}
失败测试数: {result.get('failed_tests', 0)}
通过率: {pass_rate:.2f}%

失败的测试:
"""
                
                # 添加失败的测试信息
                for test_result in result.get("test_results", []):
                    if test_result.get("status") != "success":
                        prompt += f"- {test_result.get('name', 'unknown')}: {test_result.get('error', '未知错误')}\n"
                
                # 生成总结
                summary = self.generate_with_gemma(prompt)
                
                report += f"## Gemma模型生成的测试总结\n\n{summary}\n\n"
            except Exception as e:
                logger.error(f"生成测试总结失败: {e}")
        
        return report
    
    def collect_issues_from_test_results(self) -> List[Dict[str, Any]]:
        """
        从测试结果中收集问题
        
        Returns:
            List[Dict[str, Any]]: 问题列表
        """
        logger.info("从测试结果中收集问题")
        
        issues = []
        
        # 获取所有测试计划
        plan_names = self.test_plan_manager.list_test_plans()
        
        for plan_name in plan_names:
            # 获取最新的测试结果
            result = self.test_plan_manager.get_latest_test_result(plan_name)
            
            if not result:
                continue
            
            # 检查是否有失败的测试
            if result.get("failed_tests", 0) > 0:
                for test_result in result.get("test_results", []):
                    if test_result.get("status") != "success":
                        # 创建问题
                        issue = {
                            "title": f"测试失败: {test_result.get('name', 'unknown')}",
                            "description": test_result.get("error", "未知错误"),
                            "plan_name": plan_name,
                            "test_name": test_result.get("name", "unknown"),
                            "severity": "high" if "critical" in test_result.get("name", "").lower() else "medium"
                        }
                        
                        issues.append(issue)
        
        return issues
    
    def update_readme_with_test_results(self) -> bool:
        """
        使用测试结果更新README
        
        Returns:
            bool: 是否成功更新
        """
        logger.info("使用测试结果更新README")
        
        try:
            # 读取README
            with open(self.readme_path, "r") as f:
                readme_content = f.read()
            
            # 获取所有测试计划
            plan_names = self.test_plan_manager.list_test_plans()
            
            # 测试结果摘要
            summary = "## 测试结果摘要\n\n"
            summary += "| 测试计划 | 状态 | 通过率 | 最后运行时间 |\n"
            summary += "| --- | --- | --- | --- |\n"
            
            for plan_name in plan_names:
                # 获取最新的测试结果
                result = self.test_plan_manager.get_latest_test_result(plan_name)
                
                if not result:
                    continue
                
                # 计算通过率
                pass_rate = 0
                if result.get("total_tests", 0) > 0:
                    pass_rate = result.get("successful_tests", 0) / result.get("total_tests", 0) * 100
                
                # 状态图标
                status_icon = "✅" if result.get("status") == "success" else "❌"
                
                # 添加到摘要
                summary += f"| {result.get('name', plan_name)} | {status_icon} | {pass_rate:.2f}% | {time.strftime('%Y-%m-%d %H:%M:%S')} |\n"
            
            # 检查README是否已有测试结果摘要
            if "## 测试结果摘要" in readme_content:
                # 替换现有的测试结果摘要
                import re
                readme_content = re.sub(
                    r"## 测试结果摘要\n\n.*?(?=\n##|\Z)",
                    summary,
                    readme_content,
                    flags=re.DOTALL
                )
            else:
                # 添加测试结果摘要
                readme_content += "\n\n" + summary
            
            # 写入README
            with open(self.readme_path, "w") as f:
                f.write(readme_content)
            
            logger.info("成功更新README")
            return True
        except Exception as e:
            logger.error(f"更新README失败: {e}")
            return False
    
    def run_full_workflow(self) -> Dict[str, Any]:
        """
        运行完整的工作流程
        
        Returns:
            Dict[str, Any]: 工作流程结果
        """
        logger.info("运行完整的工作流程")
        
        # 工作流程结果
        workflow_result = {
            "status": "success",
            "steps": {}
        }
        
        try:
            # 步骤1: 初始化Gemma模型
            logger.info("步骤1: 初始化Gemma模型")
            gemma_result = self.initialize_gemma_model()
            workflow_result["steps"]["initialize_gemma"] = {
                "status": "success" if gemma_result else "failed"
            }
            
            if not gemma_result:
                workflow_result["status"] = "failed"
                workflow_result["error"] = "初始化Gemma模型失败"
                return workflow_result
            
            # 步骤2: 创建默认测试计划
            logger.info("步骤2: 创建默认测试计划")
            plan_result = self.test_plan_manager.create_default_test_plans()
            workflow_result["steps"]["create_test_plans"] = {
                "status": "success" if plan_result else "failed"
            }
            
            if not plan_result:
                workflow_result["status"] = "failed"
                workflow_result["error"] = "创建默认测试计划失败"
                return workflow_result
            
            # 步骤3: 运行测试
            logger.info("步骤3: 运行测试")
            test_result = self.run_tests_from_plans()
            workflow_result["steps"]["run_tests"] = {
                "status": "success",
                "result": test_result
            }
            
            # 步骤4: 收集问题
            logger.info("步骤4: 收集问题")
            issues = self.collect_issues_from_test_results()
            workflow_result["steps"]["collect_issues"] = {
                "status": "success",
                "issues": issues
            }
            
            # 步骤5: 更新README
            logger.info("步骤5: 更新README")
            readme_result = self.update_readme_with_test_results()
            workflow_result["steps"]["update_readme"] = {
                "status": "success" if readme_result else "failed"
            }
            
            if not readme_result:
                workflow_result["status"] = "failed"
                workflow_result["error"] = "更新README失败"
                return workflow_result
            
            logger.info("工作流程完成")
            return workflow_result
        except Exception as e:
            logger.error(f"工作流程执行失败: {e}")
            workflow_result["status"] = "failed"
            workflow_result["error"] = str(e)
            return workflow_result


def main():
    """主函数"""
    import argparse
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="增强版TestAndIssueCollector")
    parser.add_argument("--repo_path", help="仓库路径")
    parser.add_argument("--test_script", help="测试脚本路径")
    parser.add_argument("--readme_path", help="README文件路径")
    parser.add_argument("--visual_test_dir", help="visual_test目录路径")
    parser.add_argument("--gemma_model_path", help="Gemma模型路径")
    parser.add_argument("--no_gpu", action="store_true", help="不使用GPU")
    parser.add_argument("--workflow", action="store_true", help="运行完整的工作流程")
    parser.add_argument("--run_tests", action="store_true", help="运行测试")
    parser.add_argument("--collect_issues", action="store_true", help="收集问题")
    parser.add_argument("--update_readme", action="store_true", help="更新README")
    
    args = parser.parse_args()
    
    # 创建增强版TestAndIssueCollector
    collector = EnhancedTestAndIssueCollector(
        repo_path=args.repo_path,
        test_script=args.test_script,
        readme_path=args.readme_path,
        visual_test_dir=args.visual_test_dir,
        gemma_model_path=args.gemma_model_path,
        use_gpu=not args.no_gpu
    )
    
    # 运行完整的工作流程
    if args.workflow:
        result = collector.run_full_workflow()
        print(f"工作流程结果: {result['status']}")
        if result["status"] == "failed":
            print(f"错误: {result.get('error', '未知错误')}")
    
    # 运行测试
    if args.run_tests:
        result = collector.run_tests_from_plans()
        print(f"测试结果: {result}")
    
    # 收集问题
    if args.collect_issues:
        issues = collector.collect_issues_from_test_results()
        print(f"收集到 {len(issues)} 个问题:")
        for issue in issues:
            print(f"- {issue['title']}: {issue['description']}")
    
    # 更新README
    if args.update_readme:
        result = collector.update_readme_with_test_results()
        if result:
            print("成功更新README")
        else:
            print("更新README失败")


if __name__ == "__main__":
    main()
