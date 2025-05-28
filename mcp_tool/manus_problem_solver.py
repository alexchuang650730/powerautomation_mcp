"""
Manus问题解决驱动器模块 - ManusProblemSolver

该模块用于驱动Manus进行问题定位、提出修复策略和测试方案。
主要功能：
1. 分析测试日志和README中的问题
2. 调用Manus能力进行问题定位
3. 生成修复策略建议
4. 提出测试方案
5. 结构化输出结果

作者: Manus AI
日期: 2025-05-28
"""

import os
import re
import json
import time
import datetime
import logging
import requests
from typing import Dict, List, Any, Optional, Union

# 导入思考与操作记录器
from .thought_action_recorder import ThoughtActionRecorder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ManusProblemSolver")

class ManusProblemSolver:
    """
    Manus问题解决驱动器类，用于驱动Manus进行问题定位、提出修复策略和测试方案
    """
    
    def __init__(self, 
                 repo_path: str,
                 readme_path: str = "README.md",
                 recorder: ThoughtActionRecorder = None):
        """
        初始化Manus问题解决驱动器
        
        Args:
            repo_path: 仓库路径
            readme_path: README文件路径，默认为"README.md"
            recorder: 思考与操作记录器实例，如果为None则创建新实例
        """
        self.repo_path = repo_path
        self.readme_path = os.path.join(repo_path, readme_path)
        
        # 初始化记录器
        self.recorder = recorder or ThoughtActionRecorder(
            log_dir=os.path.join(repo_path, "logs")
        )
        
        # 创建输出目录
        self.output_dir = os.path.join(repo_path, "manus_solutions")
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"ManusProblemSolver initialized with repo path: {repo_path}")
        logger.info(f"README path: {self.readme_path}")
    
    def extract_issues_from_readme(self) -> List[Dict[str, Any]]:
        """
        从README中提取问题
        
        Returns:
            问题列表
        """
        self.recorder.record_thought("从README中提取问题")
        
        issues = []
        
        if not os.path.exists(self.readme_path):
            logger.error(f"README file {self.readme_path} does not exist")
            return issues
        
        try:
            with open(self.readme_path, "r", encoding="utf-8") as f:
                readme_content = f.read()
            
            # 查找问题部分
            issues_section_match = re.search(r"## 测试发现的问题(.*?)(?=\n## |$)", readme_content, re.DOTALL)
            
            if not issues_section_match:
                logger.info("No issues section found in README")
                return issues
            
            issues_section = issues_section_match.group(1).strip()
            
            # 如果问题部分包含"测试未发现任何问题"，则返回空列表
            if "测试未发现任何问题" in issues_section:
                logger.info("README indicates no issues were found")
                return issues
            
            # 提取问题
            issue_pattern = re.compile(r"(\d+)\. \*\*(.*?)\*\*: (.*?)\n\s+```\n\s+(.*?)\n\s+```", re.DOTALL)
            
            for match in issue_pattern.finditer(issues_section):
                issue_number = match.group(1)
                issue_type = match.group(2).lower()
                issue_file = match.group(3).strip()
                issue_context = match.group(4).strip()
                
                issues.append({
                    "number": issue_number,
                    "type": issue_type,
                    "file": issue_file,
                    "context": issue_context
                })
            
            logger.info(f"Extracted {len(issues)} issues from README")
            
            self.recorder.record_action(
                "extract_issues_from_readme", 
                {"readme_path": self.readme_path},
                {"issues_count": len(issues)}
            )
            
            return issues
            
        except Exception as e:
            error_msg = f"Error extracting issues from README: {str(e)}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "extract_issues_from_readme", 
                {"readme_path": self.readme_path},
                {"success": False, "error": error_msg}
            )
            
            return issues
    
    def analyze_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单个问题
        
        Args:
            issue: 问题信息
            
        Returns:
            问题分析结果
        """
        self.recorder.record_thought(f"分析问题: {issue.get('type')} in {issue.get('file')}")
        
        # 记录开始分析
        self.recorder.record_action(
            "start_analyze_issue", 
            {"issue": issue}
        )
        
        # 分析问题类型
        issue_type = issue.get("type", "").lower()
        issue_file = issue.get("file", "")
        issue_context = issue.get("context", "")
        
        # 初始化分析结果
        analysis = {
            "issue": issue,
            "problem_category": None,
            "severity": None,
            "possible_causes": [],
            "affected_components": [],
            "related_files": []
        }
        
        # 根据问题类型确定严重性
        if "error" in issue_type:
            analysis["severity"] = "high"
        elif "warning" in issue_type:
            analysis["severity"] = "medium"
        else:
            analysis["severity"] = "low"
        
        # 分析问题类别
        if "import" in issue_context.lower() or "module" in issue_context.lower():
            analysis["problem_category"] = "dependency"
            analysis["possible_causes"].append("Missing or incompatible dependency")
            analysis["possible_causes"].append("Incorrect import path")
        elif "permission" in issue_context.lower() or "access" in issue_context.lower():
            analysis["problem_category"] = "permission"
            analysis["possible_causes"].append("Insufficient file permissions")
            analysis["possible_causes"].append("Access denied to resource")
        elif "timeout" in issue_context.lower():
            analysis["problem_category"] = "performance"
            analysis["possible_causes"].append("Operation took too long to complete")
            analysis["possible_causes"].append("Resource unavailable or overloaded")
        elif "syntax" in issue_context.lower():
            analysis["problem_category"] = "syntax"
            analysis["possible_causes"].append("Syntax error in code")
            analysis["possible_causes"].append("Invalid configuration format")
        elif "null" in issue_context.lower() or "undefined" in issue_context.lower() or "none" in issue_context.lower():
            analysis["problem_category"] = "null_reference"
            analysis["possible_causes"].append("Attempting to use null or undefined value")
            analysis["possible_causes"].append("Missing required parameter or value")
        elif "memory" in issue_context.lower():
            analysis["problem_category"] = "memory"
            analysis["possible_causes"].append("Memory allocation failure")
            analysis["possible_causes"].append("Memory leak")
        elif "network" in issue_context.lower() or "connection" in issue_context.lower():
            analysis["problem_category"] = "network"
            analysis["possible_causes"].append("Network connection failure")
            analysis["possible_causes"].append("API endpoint unavailable")
        elif "file" in issue_context.lower() and ("not found" in issue_context.lower() or "missing" in issue_context.lower()):
            analysis["problem_category"] = "file_not_found"
            analysis["possible_causes"].append("File does not exist at expected location")
            analysis["possible_causes"].append("Incorrect file path")
        else:
            analysis["problem_category"] = "unknown"
            analysis["possible_causes"].append("Unclassified issue")
        
        # 分析受影响的组件
        if "ppt" in issue_file.lower() or "ppt" in issue_context.lower():
            analysis["affected_components"].append("PPT Generation")
        elif "pdf" in issue_file.lower() or "pdf" in issue_context.lower():
            analysis["affected_components"].append("PDF Processing")
        elif "api" in issue_file.lower() or "api" in issue_context.lower():
            analysis["affected_components"].append("API Integration")
        elif "ui" in issue_file.lower() or "interface" in issue_context.lower():
            analysis["affected_components"].append("User Interface")
        elif "data" in issue_file.lower() or "database" in issue_context.lower():
            analysis["affected_components"].append("Data Processing")
        else:
            analysis["affected_components"].append("Core System")
        
        # 查找相关文件
        file_pattern = re.compile(r'[\'"]([^\'"\s]+\.(py|js|html|css|json|md|sh))[\'"]')
        file_matches = file_pattern.findall(issue_context)
        
        for file_match in file_matches:
            file_path = file_match[0]
            if file_path not in analysis["related_files"]:
                analysis["related_files"].append(file_path)
        
        # 记录分析结果
        self.recorder.record_action(
            "analyze_issue_result", 
            {"issue": issue},
            {"analysis": analysis}
        )
        
        logger.info(f"Analyzed issue: {issue_type} in {issue_file}")
        logger.info(f"Category: {analysis['problem_category']}, Severity: {analysis['severity']}")
        
        return analysis
    
    def generate_fix_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成修复策略
        
        Args:
            analysis: 问题分析结果
            
        Returns:
            修复策略
        """
        issue = analysis.get("issue", {})
        issue_type = issue.get("type", "").lower()
        issue_file = issue.get("file", "")
        issue_context = issue.get("context", "")
        
        self.recorder.record_thought(f"为问题生成修复策略: {issue_type} in {issue_file}")
        
        # 初始化修复策略
        fix_strategy = {
            "issue": issue,
            "analysis": analysis,
            "recommended_actions": [],
            "code_changes": [],
            "configuration_changes": [],
            "dependency_changes": [],
            "priority": "medium",
            "estimated_effort": "medium"
        }
        
        # 根据问题类别生成修复策略
        problem_category = analysis.get("problem_category")
        severity = analysis.get("severity")
        
        # 设置优先级
        if severity == "high":
            fix_strategy["priority"] = "high"
        elif severity == "medium":
            fix_strategy["priority"] = "medium"
        else:
            fix_strategy["priority"] = "low"
        
        # 根据问题类别生成修复建议
        if problem_category == "dependency":
            fix_strategy["recommended_actions"].append("检查项目依赖项是否正确安装")
            fix_strategy["recommended_actions"].append("验证导入路径是否正确")
            fix_strategy["recommended_actions"].append("检查依赖版本兼容性")
            
            fix_strategy["dependency_changes"].append({
                "action": "verify",
                "description": "验证所有依赖项的安装状态和版本"
            })
            
            fix_strategy["code_changes"].append({
                "action": "check_imports",
                "description": "检查导入语句是否正确"
            })
            
            fix_strategy["estimated_effort"] = "low"
            
        elif problem_category == "permission":
            fix_strategy["recommended_actions"].append("检查文件和目录权限")
            fix_strategy["recommended_actions"].append("确保应用有足够的访问权限")
            
            fix_strategy["code_changes"].append({
                "action": "add_permission_check",
                "description": "添加权限检查和错误处理"
            })
            
            fix_strategy["estimated_effort"] = "low"
            
        elif problem_category == "performance":
            fix_strategy["recommended_actions"].append("优化耗时操作")
            fix_strategy["recommended_actions"].append("添加超时处理")
            fix_strategy["recommended_actions"].append("考虑异步处理")
            
            fix_strategy["code_changes"].append({
                "action": "optimize",
                "description": "优化性能关键代码"
            })
            
            fix_strategy["code_changes"].append({
                "action": "add_timeout",
                "description": "添加超时处理逻辑"
            })
            
            fix_strategy["estimated_effort"] = "high"
            
        elif problem_category == "syntax":
            fix_strategy["recommended_actions"].append("修复代码语法错误")
            fix_strategy["recommended_actions"].append("验证配置文件格式")
            
            fix_strategy["code_changes"].append({
                "action": "fix_syntax",
                "description": "修复语法错误"
            })
            
            fix_strategy["estimated_effort"] = "low"
            
        elif problem_category == "null_reference":
            fix_strategy["recommended_actions"].append("添加空值检查")
            fix_strategy["recommended_actions"].append("提供默认值")
            
            fix_strategy["code_changes"].append({
                "action": "add_null_check",
                "description": "添加空值检查和默认值处理"
            })
            
            fix_strategy["estimated_effort"] = "medium"
            
        elif problem_category == "memory":
            fix_strategy["recommended_actions"].append("优化内存使用")
            fix_strategy["recommended_actions"].append("检查内存泄漏")
            
            fix_strategy["code_changes"].append({
                "action": "optimize_memory",
                "description": "优化内存使用和资源释放"
            })
            
            fix_strategy["estimated_effort"] = "high"
            
        elif problem_category == "network":
            fix_strategy["recommended_actions"].append("添加网络错误处理")
            fix_strategy["recommended_actions"].append("实现重试机制")
            fix_strategy["recommended_actions"].append("添加连接超时设置")
            
            fix_strategy["code_changes"].append({
                "action": "add_error_handling",
                "description": "添加网络错误处理和重试逻辑"
            })
            
            fix_strategy["estimated_effort"] = "medium"
            
        elif problem_category == "file_not_found":
            fix_strategy["recommended_actions"].append("检查文件路径是否正确")
            fix_strategy["recommended_actions"].append("确保文件存在")
            fix_strategy["recommended_actions"].append("添加文件不存在时的错误处理")
            
            fix_strategy["code_changes"].append({
                "action": "add_file_check",
                "description": "添加文件存在检查和错误处理"
            })
            
            fix_strategy["estimated_effort"] = "low"
            
        else:  # unknown
            fix_strategy["recommended_actions"].append("进一步分析错误日志")
            fix_strategy["recommended_actions"].append("添加详细日志记录")
            
            fix_strategy["code_changes"].append({
                "action": "add_logging",
                "description": "添加详细日志记录以便进一步分析"
            })
            
            fix_strategy["estimated_effort"] = "medium"
        
        # 记录修复策略
        self.recorder.record_action(
            "generate_fix_strategy", 
            {"issue": issue},
            {"fix_strategy": fix_strategy}
        )
        
        logger.info(f"Generated fix strategy for issue: {issue_type} in {issue_file}")
        logger.info(f"Priority: {fix_strategy['priority']}, Effort: {fix_strategy['estimated_effort']}")
        
        return fix_strategy
    
    def generate_test_plan(self, fix_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成测试方案
        
        Args:
            fix_strategy: 修复策略
            
        Returns:
            测试方案
        """
        issue = fix_strategy.get("issue", {})
        issue_type = issue.get("type", "").lower()
        issue_file = issue.get("file", "")
        
        self.recorder.record_thought(f"为修复策略生成测试方案: {issue_type} in {issue_file}")
        
        # 初始化测试方案
        test_plan = {
            "issue": issue,
            "fix_strategy": fix_strategy,
            "test_cases": [],
            "verification_steps": [],
            "expected_results": [],
            "test_environment": {},
            "test_data": {}
        }
        
        # 根据问题类别和修复策略生成测试方案
        problem_category = fix_strategy.get("analysis", {}).get("problem_category")
        
        # 设置测试环境
        test_plan["test_environment"] = {
            "os": "macOS Sonoma (14.x)",
            "path": "/Users/alexchuang/powerassistant/powerautomation",
            "python_version": "3.x",
            "required_packages": []
        }
        
        # 根据问题类别生成测试用例
        if problem_category == "dependency":
            test_plan["test_cases"].append({
                "name": "依赖项安装验证",
                "description": "验证所有必要的依赖项是否正确安装",
                "steps": [
                    "激活虚拟环境",
                    "运行 `pip list` 检查已安装的依赖项",
                    "验证问题相关的依赖项是否存在且版本正确"
                ]
            })
            
            test_plan["test_cases"].append({
                "name": "导入验证",
                "description": "验证问题相关的模块是否可以正确导入",
                "steps": [
                    "激活虚拟环境",
                    "启动Python解释器",
                    "尝试导入问题相关的模块",
                    "验证导入是否成功"
                ]
            })
            
            test_plan["verification_steps"].append("确认所有依赖项已正确安装")
            test_plan["verification_steps"].append("确认所有模块可以正确导入")
            
            test_plan["expected_results"].append("所有依赖项安装成功且版本正确")
            test_plan["expected_results"].append("所有模块导入成功，无错误")
            
        elif problem_category == "permission":
            test_plan["test_cases"].append({
                "name": "权限验证",
                "description": "验证文件和目录权限是否正确",
                "steps": [
                    "检查问题相关文件和目录的权限",
                    "确保应用有足够的访问权限",
                    "尝试以应用运行时的用户身份访问相关资源"
                ]
            })
            
            test_plan["verification_steps"].append("确认所有文件和目录权限正确")
            test_plan["verification_steps"].append("确认应用可以访问所有必要的资源")
            
            test_plan["expected_results"].append("应用可以正常访问所有必要的文件和资源")
            test_plan["expected_results"].append("不再出现权限相关的错误")
            
        elif problem_category == "performance":
            test_plan["test_cases"].append({
                "name": "性能测试",
                "description": "测试优化后的性能",
                "steps": [
                    "在与生产环境相似的条件下运行应用",
                    "执行可能导致超时的操作",
                    "监控操作执行时间",
                    "验证是否在合理时间内完成"
                ]
            })
            
            test_plan["test_cases"].append({
                "name": "超时处理测试",
                "description": "测试超时处理逻辑",
                "steps": [
                    "模拟超时条件",
                    "验证应用是否正确处理超时",
                    "确认用户收到适当的错误消息"
                ]
            })
            
            test_plan["verification_steps"].append("确认操作在合理时间内完成")
            test_plan["verification_steps"].append("确认超时处理逻辑正常工作")
            
            test_plan["expected_results"].append("操作在预期时间内完成")
            test_plan["expected_results"].append("超时情况下，应用优雅地处理错误并提供有用的反馈")
            
        elif problem_category == "syntax":
            test_plan["test_cases"].append({
                "name": "语法验证",
                "description": "验证语法错误是否已修复",
                "steps": [
                    "检查修复后的代码",
                    "使用语法检查工具验证",
                    "尝试运行修复后的代码"
                ]
            })
            
            test_plan["verification_steps"].append("确认代码通过语法检查")
            test_plan["verification_steps"].append("确认代码可以正常运行")
            
            test_plan["expected_results"].append("代码通过语法检查，无错误")
            test_plan["expected_results"].append("代码正常运行，无语法相关错误")
            
        elif problem_category == "null_reference":
            test_plan["test_cases"].append({
                "name": "空值处理测试",
                "description": "测试空值处理逻辑",
                "steps": [
                    "模拟空值输入条件",
                    "验证应用是否正确处理空值",
                    "确认应用提供适当的默认值或错误消息"
                ]
            })
            
            test_plan["verification_steps"].append("确认应用正确处理空值")
            test_plan["verification_steps"].append("确认应用在空值情况下不会崩溃")
            
            test_plan["expected_results"].append("应用正确处理空值，提供默认值或适当的错误消息")
            test_plan["expected_results"].append("不再出现空引用相关的错误")
            
        elif problem_category == "memory":
            test_plan["test_cases"].append({
                "name": "内存使用测试",
                "description": "测试内存使用情况",
                "steps": [
                    "在与生产环境相似的条件下运行应用",
                    "监控内存使用情况",
                    "执行可能导致内存问题的操作",
                    "验证内存使用是否在合理范围内"
                ]
            })
            
            test_plan["test_cases"].append({
                "name": "内存泄漏测试",
                "description": "测试是否存在内存泄漏",
                "steps": [
                    "长时间运行应用",
                    "重复执行可能导致内存泄漏的操作",
                    "监控内存使用趋势",
                    "验证内存使用是否稳定"
                ]
            })
            
            test_plan["verification_steps"].append("确认内存使用在合理范围内")
            test_plan["verification_steps"].append("确认长时间运行后内存使用稳定")
            
            test_plan["expected_results"].append("应用内存使用在预期范围内")
            test_plan["expected_results"].append("长时间运行后内存使用稳定，无泄漏")
            
        elif problem_category == "network":
            test_plan["test_cases"].append({
                "name": "网络错误处理测试",
                "description": "测试网络错误处理逻辑",
                "steps": [
                    "模拟网络连接失败",
                    "验证应用是否正确处理网络错误",
                    "确认重试机制是否正常工作",
                    "验证用户是否收到适当的错误消息"
                ]
            })
            
            test_plan["test_cases"].append({
                "name": "网络超时测试",
                "description": "测试网络超时处理",
                "steps": [
                    "模拟网络延迟",
                    "验证应用是否正确处理超时",
                    "确认超时设置是否合理"
                ]
            })
            
            test_plan["verification_steps"].append("确认应用正确处理网络错误")
            test_plan["verification_steps"].append("确认重试机制正常工作")
            test_plan["verification_steps"].append("确认超时设置合理")
            
            test_plan["expected_results"].append("应用在网络错误情况下优雅地处理错误并提供有用的反馈")
            test_plan["expected_results"].append("重试机制正常工作，可以在网络恢复后继续操作")
            test_plan["expected_results"].append("超时设置合理，不会过早超时也不会无限等待")
            
        elif problem_category == "file_not_found":
            test_plan["test_cases"].append({
                "name": "文件路径验证",
                "description": "验证文件路径是否正确",
                "steps": [
                    "检查问题相关文件的路径",
                    "确保文件存在于预期位置",
                    "验证应用是否可以访问文件"
                ]
            })
            
            test_plan["test_cases"].append({
                "name": "文件不存在处理测试",
                "description": "测试文件不存在时的错误处理",
                "steps": [
                    "模拟文件不存在的情况",
                    "验证应用是否正确处理文件不存在的情况",
                    "确认用户收到适当的错误消息"
                ]
            })
            
            test_plan["verification_steps"].append("确认所有必要的文件存在且路径正确")
            test_plan["verification_steps"].append("确认应用正确处理文件不存在的情况")
            
            test_plan["expected_results"].append("应用可以正常访问所有必要的文件")
            test_plan["expected_results"].append("文件不存在时，应用提供有用的错误消息而不是崩溃")
            
        else:  # unknown
            test_plan["test_cases"].append({
                "name": "一般功能测试",
                "description": "测试问题相关功能",
                "steps": [
                    "执行可能触发问题的操作",
                    "验证问题是否仍然存在",
                    "检查日志是否包含更多信息"
                ]
            })
            
            test_plan["verification_steps"].append("确认问题不再出现")
            test_plan["verification_steps"].append("确认日志中包含足够的信息")
            
            test_plan["expected_results"].append("问题不再出现")
            test_plan["expected_results"].append("日志中包含足够的信息以便进一步分析")
        
        # 添加通用测试数据
        test_plan["test_data"] = {
            "sample_inputs": ["正常输入", "边界情况输入", "异常输入"],
            "expected_outputs": ["预期的正常输出", "预期的边界情况输出", "预期的错误处理"]
        }
        
        # 记录测试方案
        self.recorder.record_action(
            "generate_test_plan", 
            {"issue": issue},
            {"test_plan": test_plan}
        )
        
        logger.info(f"Generated test plan for issue: {issue_type} in {issue_file}")
        logger.info(f"Test cases: {len(test_plan['test_cases'])}")
        
        return test_plan
    
    def process_all_issues(self) -> Dict[str, Any]:
        """
        处理所有问题，生成修复策略和测试方案
        
        Returns:
            处理结果
        """
        self.recorder.record_thought("处理所有问题，生成修复策略和测试方案")
        
        # 从README中提取问题
        issues = self.extract_issues_from_readme()
        
        if not issues:
            logger.info("No issues found in README")
            
            self.recorder.record_action(
                "process_all_issues", 
                {},
                {"success": True, "issues_count": 0, "message": "No issues found"}
            )
            
            return {
                "success": True,
                "issues_count": 0,
                "message": "No issues found in README"
            }
        
        # 处理每个问题
        results = []
        
        for issue in issues:
            # 分析问题
            analysis = self.analyze_issue(issue)
            
            # 生成修复策略
            fix_strategy = self.generate_fix_strategy(analysis)
            
            # 生成测试方案
            test_plan = self.generate_test_plan(fix_strategy)
            
            # 添加到结果
            results.append({
                "issue": issue,
                "analysis": analysis,
                "fix_strategy": fix_strategy,
                "test_plan": test_plan
            })
        
        # 保存结果
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.output_dir, f"manus_solutions_{timestamp}.json")
        
        try:
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved results to {results_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
        
        # 生成摘要报告
        summary_file = os.path.join(self.output_dir, f"manus_solutions_summary_{timestamp}.md")
        
        try:
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write("# Manus问题解决方案摘要\n\n")
                f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"共发现 {len(issues)} 个问题\n\n")
                
                for i, result in enumerate(results, 1):
                    issue = result["issue"]
                    analysis = result["analysis"]
                    fix_strategy = result["fix_strategy"]
                    
                    f.write(f"## 问题 {i}: {issue.get('type', '').upper()} in {issue.get('file', '')}\n\n")
                    f.write(f"### 问题描述\n\n")
                    f.write(f"```\n{issue.get('context', '')}\n```\n\n")
                    
                    f.write(f"### 问题分析\n\n")
                    f.write(f"- 类别: {analysis.get('problem_category', '')}\n")
                    f.write(f"- 严重性: {analysis.get('severity', '')}\n")
                    f.write(f"- 可能原因:\n")
                    for cause in analysis.get("possible_causes", []):
                        f.write(f"  - {cause}\n")
                    f.write(f"- 受影响组件: {', '.join(analysis.get('affected_components', []))}\n\n")
                    
                    f.write(f"### 修复策略\n\n")
                    f.write(f"- 优先级: {fix_strategy.get('priority', '')}\n")
                    f.write(f"- 预估工作量: {fix_strategy.get('estimated_effort', '')}\n")
                    f.write(f"- 推荐操作:\n")
                    for action in fix_strategy.get("recommended_actions", []):
                        f.write(f"  - {action}\n")
                    
                    if fix_strategy.get("code_changes"):
                        f.write(f"- 代码修改:\n")
                        for change in fix_strategy.get("code_changes", []):
                            f.write(f"  - {change.get('description', '')}\n")
                    
                    f.write("\n")
            
            logger.info(f"Generated summary report: {summary_file}")
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
        
        # 记录处理结果
        self.recorder.record_action(
            "process_all_issues", 
            {},
            {
                "success": True,
                "issues_count": len(issues),
                "results_file": results_file,
                "summary_file": summary_file
            }
        )
        
        return {
            "success": True,
            "issues_count": len(issues),
            "results": results,
            "results_file": results_file,
            "summary_file": summary_file
        }
    
    def update_readme_with_solutions(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        更新README，添加解决方案
        
        Args:
            results: 处理结果
            
        Returns:
            更新结果
        """
        self.recorder.record_thought("更新README，添加解决方案")
        
        if not os.path.exists(self.readme_path):
            error_msg = f"README file {self.readme_path} does not exist"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "update_readme_with_solutions", 
                {},
                {"success": False, "error": error_msg}
            )
            
            return {"success": False, "error": error_msg}
        
        try:
            # 读取当前README内容
            with open(self.readme_path, "r", encoding="utf-8") as f:
                readme_content = f.read()
            
            # 生成解决方案部分
            solutions_section = "\n\n## Manus解决方案\n\n"
            
            if not results:
                solutions_section += "没有发现需要解决的问题。\n"
            else:
                solutions_section += f"Manus分析了 {len(results)} 个问题，并提供了以下解决方案：\n\n"
                
                for i, result in enumerate(results, 1):
                    issue = result["issue"]
                    fix_strategy = result["fix_strategy"]
                    
                    solutions_section += f"### 问题 {i}: {issue.get('type', '').upper()} in {issue.get('file', '')}\n\n"
                    
                    solutions_section += "#### 修复策略\n\n"
                    solutions_section += f"优先级: **{fix_strategy.get('priority', '')}** | 预估工作量: **{fix_strategy.get('estimated_effort', '')}**\n\n"
                    
                    solutions_section += "推荐操作:\n\n"
                    for action in fix_strategy.get("recommended_actions", []):
                        solutions_section += f"- {action}\n"
                    
                    solutions_section += "\n"
                    
                    if fix_strategy.get("code_changes"):
                        solutions_section += "代码修改:\n\n"
                        for change in fix_strategy.get("code_changes", []):
                            solutions_section += f"- {change.get('description', '')}\n"
                        
                        solutions_section += "\n"
            
            # 添加生成时间
            solutions_section += f"\n*解决方案生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
            
            # 检查README是否已包含解决方案部分
            if "## Manus解决方案" in readme_content:
                # 替换现有解决方案部分
                pattern = r"## Manus解决方案.*?(?=\n## |$)"
                readme_content = re.sub(pattern, solutions_section.strip(), readme_content, flags=re.DOTALL)
            else:
                # 添加解决方案部分到README末尾
                readme_content += solutions_section
            
            # 写回README文件
            with open(self.readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            
            logger.info(f"Updated README with {len(results)} solutions")
            
            self.recorder.record_action(
                "update_readme_with_solutions", 
                {},
                {"success": True, "solutions_count": len(results)}
            )
            
            return {"success": True, "solutions_count": len(results)}
            
        except Exception as e:
            error_msg = f"Error updating README with solutions: {str(e)}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "update_readme_with_solutions", 
                {},
                {"success": False, "error": error_msg}
            )
            
            return {"success": False, "error": error_msg}
    
    def run_full_solution_cycle(self) -> Dict[str, Any]:
        """
        运行完整的解决方案周期，包括处理问题、生成解决方案和更新README
        
        Returns:
            解决方案周期结果
        """
        self.recorder.record_thought("运行完整的解决方案周期")
        
        # 处理所有问题
        process_result = self.process_all_issues()
        
        if not process_result["success"]:
            logger.error(f"Failed to process issues: {process_result.get('error')}")
            return process_result
        
        # 如果没有问题，直接返回
        if process_result.get("issues_count", 0) == 0:
            logger.info("No issues found, nothing to solve")
            
            self.recorder.record_action(
                "run_full_solution_cycle", 
                {},
                {"success": True, "message": "No issues found"}
            )
            
            return {
                "success": True,
                "message": "No issues found, nothing to solve"
            }
        
        # 更新README，添加解决方案
        update_result = self.update_readme_with_solutions(process_result.get("results", []))
        
        if not update_result["success"]:
            logger.error(f"Failed to update README: {update_result.get('error')}")
        
        logger.info("Full solution cycle completed")
        
        self.recorder.record_action(
            "run_full_solution_cycle", 
            {},
            {
                "success": True,
                "issues_count": process_result.get("issues_count", 0),
                "readme_updated": update_result.get("success", False)
            }
        )
        
        return {
            "success": True,
            "process_result": process_result,
            "update_result": update_result
        }
