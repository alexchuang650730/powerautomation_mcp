"""
Release守则检查器模块 - ReleaseRulesChecker

该模块负责确保每次Release前都遵循规定的守则，
包括验证测试环境、执行流程、问题定位和测试方案等。

作者: Manus AI
日期: 2025-05-28
"""

import os
import time
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ReleaseRulesChecker")

class RuleStatus(Enum):
    """规则状态枚举"""
    PASSED = "通过"
    FAILED = "失败"
    WARNING = "警告"
    NOT_CHECKED = "未检查"

class ReleaseRulesChecker:
    """
    Release守则检查器，确保每次Release前都遵循规定的守则。
    """
    
    def __init__(self, 
                 log_dir: str,
                 visual_recorder = None,
                 navigator = None):
        """
        初始化Release守则检查器
        
        Args:
            log_dir: 日志存储目录
            visual_recorder: 视觉记录器实例
            navigator: Manus导航器实例
        """
        self.log_dir = log_dir
        self.visual_recorder = visual_recorder
        self.navigator = navigator
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 禁止事项
        self.forbidden_rules = [
            {
                "id": "no_real_env_verification",
                "description": "没有在真实环境中验证修复效果",
                "status": RuleStatus.NOT_CHECKED,
                "details": ""
            },
            {
                "id": "code_analysis_only",
                "description": "仅基于代码分析而非实际运行结果做出判断",
                "status": RuleStatus.NOT_CHECKED,
                "details": ""
            },
            {
                "id": "untested_code",
                "description": "让用户测试未经完整测试的代码",
                "status": RuleStatus.NOT_CHECKED,
                "details": ""
            }
        ]
        
        # 必须执行的步骤
        self.required_steps = [
            {
                "id": "sandbox_startup",
                "description": "在沙盒环境启动应用",
                "status": RuleStatus.NOT_CHECKED,
                "details": ""
            },
            {
                "id": "complete_workflow",
                "description": "完整执行用户流程并截图记录每个步骤",
                "status": RuleStatus.NOT_CHECKED,
                "details": ""
            },
            {
                "id": "mindmap_rendering",
                "description": "特别验证思维导图是否真实渲染",
                "status": RuleStatus.NOT_CHECKED,
                "details": ""
            },
            {
                "id": "console_logs",
                "description": "记录浏览器控制台日志和任何错误信息",
                "status": RuleStatus.NOT_CHECKED,
                "details": ""
            },
            {
                "id": "actual_results",
                "description": "基于实际测试结果而非假设来判断修复是否成功",
                "status": RuleStatus.NOT_CHECKED,
                "details": ""
            }
        ]
        
        # Release前的必要流程
        self.release_prerequisites = [
            {
                "id": "problem_identification",
                "description": "定位问题",
                "status": RuleStatus.NOT_CHECKED,
                "details": "",
                "document_path": ""
            },
            {
                "id": "fix_strategy",
                "description": "提出修复策略",
                "status": RuleStatus.NOT_CHECKED,
                "details": "",
                "document_path": ""
            },
            {
                "id": "test_plan",
                "description": "提出测试方案",
                "status": RuleStatus.NOT_CHECKED,
                "details": "",
                "document_path": ""
            }
        ]
        
        # 当前检查会话
        self.current_session = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "overall_status": RuleStatus.NOT_CHECKED,
            "screenshots": [],
            "console_logs": [],
            "test_results": []
        }
    
    def check_forbidden_rules(self):
        """
        检查禁止事项
        
        Returns:
            bool: 如果所有禁止事项都未违反，返回True；否则返回False
        """
        all_passed = True
        
        # 检查是否在真实环境中验证
        real_env_rule = self.forbidden_rules[0]
        if self._check_real_environment_verification():
            real_env_rule["status"] = RuleStatus.PASSED
            real_env_rule["details"] = "已在真实环境中验证修复效果"
        else:
            real_env_rule["status"] = RuleStatus.FAILED
            real_env_rule["details"] = "未在真实环境中验证修复效果"
            all_passed = False
        
        # 检查是否仅基于代码分析
        code_analysis_rule = self.forbidden_rules[1]
        if self._check_actual_run_results():
            code_analysis_rule["status"] = RuleStatus.PASSED
            code_analysis_rule["details"] = "基于实际运行结果做出判断"
        else:
            code_analysis_rule["status"] = RuleStatus.FAILED
            code_analysis_rule["details"] = "仅基于代码分析而非实际运行结果做出判断"
            all_passed = False
        
        # 检查是否测试未经完整测试的代码
        untested_code_rule = self.forbidden_rules[2]
        if self._check_complete_testing():
            untested_code_rule["status"] = RuleStatus.PASSED
            untested_code_rule["details"] = "代码已经过完整测试"
        else:
            untested_code_rule["status"] = RuleStatus.FAILED
            untested_code_rule["details"] = "代码未经完整测试"
            all_passed = False
        
        return all_passed
    
    def check_required_steps(self):
        """
        检查必须执行的步骤
        
        Returns:
            bool: 如果所有必须执行的步骤都已完成，返回True；否则返回False
        """
        all_passed = True
        
        # 检查是否在沙盒环境启动应用
        sandbox_rule = self.required_steps[0]
        if self._check_sandbox_startup():
            sandbox_rule["status"] = RuleStatus.PASSED
            sandbox_rule["details"] = "已在沙盒环境启动应用"
        else:
            sandbox_rule["status"] = RuleStatus.FAILED
            sandbox_rule["details"] = "未在沙盒环境启动应用"
            all_passed = False
        
        # 检查是否完整执行用户流程并截图
        workflow_rule = self.required_steps[1]
        if self._check_complete_workflow():
            workflow_rule["status"] = RuleStatus.PASSED
            workflow_rule["details"] = f"已完整执行用户流程并截图记录，共{len(self.current_session['screenshots'])}张截图"
        else:
            workflow_rule["status"] = RuleStatus.FAILED
            workflow_rule["details"] = "未完整执行用户流程或未截图记录"
            all_passed = False
        
        # 检查是否验证思维导图渲染
        mindmap_rule = self.required_steps[2]
        if self._check_mindmap_rendering():
            mindmap_rule["status"] = RuleStatus.PASSED
            mindmap_rule["details"] = "已验证思维导图真实渲染"
        else:
            mindmap_rule["status"] = RuleStatus.FAILED
            mindmap_rule["details"] = "未验证思维导图真实渲染"
            all_passed = False
        
        # 检查是否记录控制台日志
        console_rule = self.required_steps[3]
        if self._check_console_logs():
            console_rule["status"] = RuleStatus.PASSED
            console_rule["details"] = f"已记录浏览器控制台日志，共{len(self.current_session['console_logs'])}条日志"
        else:
            console_rule["status"] = RuleStatus.FAILED
            console_rule["details"] = "未记录浏览器控制台日志"
            all_passed = False
        
        # 检查是否基于实际测试结果判断
        results_rule = self.required_steps[4]
        if self._check_actual_test_results():
            results_rule["status"] = RuleStatus.PASSED
            results_rule["details"] = "基于实际测试结果判断修复是否成功"
        else:
            results_rule["status"] = RuleStatus.FAILED
            results_rule["details"] = "未基于实际测试结果判断修复是否成功"
            all_passed = False
        
        return all_passed
    
    def check_release_prerequisites(self):
        """
        检查Release前的必要流程
        
        Returns:
            bool: 如果所有Release前的必要流程都已完成，返回True；否则返回False
        """
        all_passed = True
        
        # 检查是否定位问题
        problem_rule = self.release_prerequisites[0]
        problem_doc = self._check_problem_identification()
        if problem_doc:
            problem_rule["status"] = RuleStatus.PASSED
            problem_rule["details"] = "已定位问题并生成文档"
            problem_rule["document_path"] = problem_doc
        else:
            problem_rule["status"] = RuleStatus.FAILED
            problem_rule["details"] = "未定位问题或未生成文档"
            all_passed = False
        
        # 检查是否提出修复策略
        strategy_rule = self.release_prerequisites[1]
        strategy_doc = self._check_fix_strategy()
        if strategy_doc:
            strategy_rule["status"] = RuleStatus.PASSED
            strategy_rule["details"] = "已提出修复策略并生成文档"
            strategy_rule["document_path"] = strategy_doc
        else:
            strategy_rule["status"] = RuleStatus.FAILED
            strategy_rule["details"] = "未提出修复策略或未生成文档"
            all_passed = False
        
        # 检查是否提出测试方案
        test_rule = self.release_prerequisites[2]
        test_doc = self._check_test_plan()
        if test_doc:
            test_rule["status"] = RuleStatus.PASSED
            test_rule["details"] = "已提出测试方案并生成文档"
            test_rule["document_path"] = test_doc
        else:
            test_rule["status"] = RuleStatus.FAILED
            test_rule["details"] = "未提出测试方案或未生成文档"
            all_passed = False
        
        return all_passed
    
    def run_full_check(self):
        """
        运行完整检查
        
        Returns:
            bool: 如果所有检查都通过，返回True；否则返回False
        """
        logger.info("开始运行Release守则完整检查")
        
        # 重置当前会话
        self.current_session = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "overall_status": RuleStatus.NOT_CHECKED,
            "screenshots": [],
            "console_logs": [],
            "test_results": []
        }
        
        # 检查禁止事项
        forbidden_passed = self.check_forbidden_rules()
        logger.info(f"禁止事项检查: {'通过' if forbidden_passed else '失败'}")
        
        # 检查必须执行的步骤
        steps_passed = self.check_required_steps()
        logger.info(f"必须执行的步骤检查: {'通过' if steps_passed else '失败'}")
        
        # 检查Release前的必要流程
        prerequisites_passed = self.check_release_prerequisites()
        logger.info(f"Release前的必要流程检查: {'通过' if prerequisites_passed else '失败'}")
        
        # 更新当前会话状态
        all_passed = forbidden_passed and steps_passed and prerequisites_passed
        self.current_session["end_time"] = datetime.now().isoformat()
        self.current_session["overall_status"] = RuleStatus.PASSED if all_passed else RuleStatus.FAILED
        
        # 保存检查结果
        self._save_check_results()
        
        logger.info(f"Release守则完整检查: {'通过' if all_passed else '失败'}")
        return all_passed
    
    def generate_report(self, output_path=None):
        """
        生成检查报告
        
        Args:
            output_path: 报告输出路径，如果为None则使用默认路径
            
        Returns:
            str: 报告文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.log_dir, f"release_check_report_{timestamp}.md")
        
        with open(output_path, "w", encoding="utf-8") as f:
            # 报告标题
            f.write("# Release守则检查报告\n\n")
            
            # 检查时间
            start_time = datetime.fromisoformat(self.current_session["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
            end_time = "进行中"
            if self.current_session["end_time"]:
                end_time = datetime.fromisoformat(self.current_session["end_time"]).strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"- **检查开始时间**: {start_time}\n")
            f.write(f"- **检查结束时间**: {end_time}\n")
            f.write(f"- **总体状态**: {self.current_session['overall_status'].value}\n\n")
            
            # 禁止事项
            f.write("## 禁止事项检查\n\n")
            for rule in self.forbidden_rules:
                status_icon = "✅" if rule["status"] == RuleStatus.PASSED else "❌"
                f.write(f"### {status_icon} {rule['description']}\n\n")
                f.write(f"- **状态**: {rule['status'].value}\n")
                f.write(f"- **详情**: {rule['details']}\n\n")
            
            # 必须执行的步骤
            f.write("## 必须执行的步骤检查\n\n")
            for step in self.required_steps:
                status_icon = "✅" if step["status"] == RuleStatus.PASSED else "❌"
                f.write(f"### {status_icon} {step['description']}\n\n")
                f.write(f"- **状态**: {step['status'].value}\n")
                f.write(f"- **详情**: {step['details']}\n\n")
                
                # 如果是截图步骤，列出截图
                if step["id"] == "complete_workflow" and step["status"] == RuleStatus.PASSED:
                    f.write("#### 截图记录\n\n")
                    for i, screenshot in enumerate(self.current_session["screenshots"]):
                        f.write(f"- 步骤 {i+1}: [{os.path.basename(screenshot)}]({screenshot})\n")
                    f.write("\n")
                
                # 如果是控制台日志步骤，列出日志摘要
                if step["id"] == "console_logs" and step["status"] == RuleStatus.PASSED:
                    f.write("#### 控制台日志摘要\n\n")
                    f.write("```\n")
                    for log in self.current_session["console_logs"][:10]:  # 只显示前10条
                        f.write(f"{log}\n")
                    if len(self.current_session["console_logs"]) > 10:
                        f.write(f"... 共{len(self.current_session['console_logs'])}条日志\n")
                    f.write("```\n\n")
            
            # Release前的必要流程
            f.write("## Release前的必要流程检查\n\n")
            for prereq in self.release_prerequisites:
                status_icon = "✅" if prereq["status"] == RuleStatus.PASSED else "❌"
                f.write(f"### {status_icon} {prereq['description']}\n\n")
                f.write(f"- **状态**: {prereq['status'].value}\n")
                f.write(f"- **详情**: {prereq['details']}\n")
                if prereq["document_path"]:
                    f.write(f"- **文档**: [{os.path.basename(prereq['document_path'])}]({prereq['document_path']})\n")
                f.write("\n")
            
            # 总结
            f.write("## 总结\n\n")
            if self.current_session["overall_status"] == RuleStatus.PASSED:
                f.write("✅ **所有检查项目均已通过，可以进行Release。**\n")
            else:
                f.write("❌ **存在未通过的检查项目，不建议进行Release。请先解决上述问题。**\n")
        
        logger.info(f"已生成检查报告: {output_path}")
        return output_path
    
    def add_screenshot(self, screenshot_path):
        """
        添加截图记录
        
        Args:
            screenshot_path: 截图文件路径
        """
        self.current_session["screenshots"].append(screenshot_path)
    
    def add_console_log(self, log_content):
        """
        添加控制台日志
        
        Args:
            log_content: 日志内容
        """
        self.current_session["console_logs"].append(log_content)
    
    def add_test_result(self, test_name, passed, details=None):
        """
        添加测试结果
        
        Args:
            test_name: 测试名称
            passed: 是否通过
            details: 详细信息
        """
        self.current_session["test_results"].append({
            "name": test_name,
            "passed": passed,
            "details": details or "",
            "timestamp": datetime.now().isoformat()
        })
    
    def _check_real_environment_verification(self):
        """
        检查是否在真实环境中验证修复效果
        
        Returns:
            bool: 如果在真实环境中验证，返回True；否则返回False
        """
        # 检查是否有真实环境的截图
        real_env_screenshots = [s for s in self.current_session["screenshots"] if "real_env" in s.lower()]
        
        # 检查测试结果中是否有真实环境的标记
        real_env_tests = [t for t in self.current_session["test_results"] if "real_env" in t["name"].lower()]
        
        return len(real_env_screenshots) > 0 or len(real_env_tests) > 0
    
    def _check_actual_run_results(self):
        """
        检查是否基于实际运行结果做出判断
        
        Returns:
            bool: 如果基于实际运行结果，返回True；否则返回False
        """
        # 检查是否有测试结果
        if len(self.current_session["test_results"]) == 0:
            return False
        
        # 检查是否有控制台日志
        if len(self.current_session["console_logs"]) == 0:
            return False
        
        # 检查是否有截图
        if len(self.current_session["screenshots"]) == 0:
            return False
        
        return True
    
    def _check_complete_testing(self):
        """
        检查是否完整测试代码
        
        Returns:
            bool: 如果完整测试，返回True；否则返回False
        """
        # 检查测试结果数量是否足够
        if len(self.current_session["test_results"]) < 3:  # 至少需要3个测试结果
            return False
        
        # 检查是否覆盖了所有主要功能
        test_names = [t["name"].lower() for t in self.current_session["test_results"]]
        
        # 检查是否包含核心功能测试
        core_features = ["navigation", "recording", "analysis", "taskbar", "mindmap"]
        covered_features = [f for f in core_features if any(f in name for name in test_names)]
        
        return len(covered_features) >= 3  # 至少覆盖3个核心功能
    
    def _check_sandbox_startup(self):
        """
        检查是否在沙盒环境启动应用
        
        Returns:
            bool: 如果在沙盒环境启动，返回True；否则返回False
        """
        # 检查是否有沙盒环境的标记
        sandbox_logs = [log for log in self.current_session["console_logs"] if "sandbox" in log.lower()]
        
        # 检查是否有应用启动的截图
        startup_screenshots = [s for s in self.current_session["screenshots"] if "startup" in s.lower()]
        
        return len(sandbox_logs) > 0 or len(startup_screenshots) > 0
    
    def _check_complete_workflow(self):
        """
        检查是否完整执行用户流程并截图
        
        Returns:
            bool: 如果完整执行并截图，返回True；否则返回False
        """
        # 检查截图数量是否足够
        if len(self.current_session["screenshots"]) < 5:  # 至少需要5张截图
            return False
        
        # 检查截图是否覆盖了完整流程
        # 这里可以根据实际需求定义完整流程的标准
        
        return True
    
    def _check_mindmap_rendering(self):
        """
        检查是否验证思维导图真实渲染
        
        Returns:
            bool: 如果验证思维导图渲染，返回True；否则返回False
        """
        # 检查是否有思维导图相关的截图
        mindmap_screenshots = [s for s in self.current_session["screenshots"] if "mindmap" in s.lower()]
        
        # 检查测试结果中是否有思维导图相关的测试
        mindmap_tests = [t for t in self.current_session["test_results"] if "mindmap" in t["name"].lower()]
        
        return len(mindmap_screenshots) > 0 or len(mindmap_tests) > 0
    
    def _check_console_logs(self):
        """
        检查是否记录浏览器控制台日志
        
        Returns:
            bool: 如果记录控制台日志，返回True；否则返回False
        """
        # 检查是否有控制台日志
        return len(self.current_session["console_logs"]) > 0
    
    def _check_actual_test_results(self):
        """
        检查是否基于实际测试结果判断修复是否成功
        
        Returns:
            bool: 如果基于实际测试结果，返回True；否则返回False
        """
        # 检查是否有测试结果
        if len(self.current_session["test_results"]) == 0:
            return False
        
        # 检查测试结果中是否包含成功和失败的案例
        has_passed = any(t["passed"] for t in self.current_session["test_results"])
        has_failed = any(not t["passed"] for t in self.current_session["test_results"])
        
        # 真实的测试应该包含成功和失败的案例
        # 如果全部成功或全部失败，可能是预设的结果
        return has_passed and has_failed
    
    def _check_problem_identification(self):
        """
        检查是否定位问题
        
        Returns:
            str: 问题定位文档路径，如果未定位问题则返回空字符串
        """
        # 检查是否存在问题定位文档
        problem_doc = os.path.join(self.log_dir, "problem_identification.md")
        if os.path.exists(problem_doc):
            return problem_doc
        
        return ""
    
    def _check_fix_strategy(self):
        """
        检查是否提出修复策略
        
        Returns:
            str: 修复策略文档路径，如果未提出修复策略则返回空字符串
        """
        # 检查是否存在修复策略文档
        strategy_doc = os.path.join(self.log_dir, "fix_strategy.md")
        if os.path.exists(strategy_doc):
            return strategy_doc
        
        return ""
    
    def _check_test_plan(self):
        """
        检查是否提出测试方案
        
        Returns:
            str: 测试方案文档路径，如果未提出测试方案则返回空字符串
        """
        # 检查是否存在测试方案文档
        test_doc = os.path.join(self.log_dir, "test_plan.md")
        if os.path.exists(test_doc):
            return test_doc
        
        return ""
    
    def _save_check_results(self):
        """保存检查结果"""
        # 创建结果对象
        results = {
            "timestamp": datetime.now().isoformat(),
            "session": self.current_session,
            "forbidden_rules": self.forbidden_rules,
            "required_steps": self.required_steps,
            "release_prerequisites": self.release_prerequisites
        }
        
        # 保存为JSON文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.log_dir, f"release_check_results_{timestamp}.json")
        
        with open(output_path, "w", encoding="utf-8") as f:
            # 将枚举值转换为字符串
            json_results = json.dumps(results, default=lambda o: o.value if isinstance(o, RuleStatus) else o.__dict__, indent=2)
            f.write(json_results)
        
        logger.info(f"已保存检查结果: {output_path}")
    
    def generate_problem_identification_doc(self, problems, output_path=None):
        """
        生成问题定位文档
        
        Args:
            problems: 问题列表，每个问题是一个字典，包含id、title、description、severity等字段
            output_path: 文档输出路径，如果为None则使用默认路径
            
        Returns:
            str: 文档文件路径
        """
        if output_path is None:
            output_path = os.path.join(self.log_dir, "problem_identification.md")
        
        with open(output_path, "w", encoding="utf-8") as f:
            # 文档标题
            f.write("# 问题定位报告\n\n")
            
            # 生成时间
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"**生成时间**: {timestamp}\n\n")
            
            # 问题摘要
            f.write("## 问题摘要\n\n")
            f.write(f"共发现 {len(problems)} 个问题：\n\n")
            
            severity_counts = {}
            for problem in problems:
                severity = problem.get("severity", "未知")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            for severity, count in severity_counts.items():
                f.write(f"- {severity}: {count}个\n")
            
            f.write("\n")
            
            # 详细问题列表
            f.write("## 详细问题列表\n\n")
            
            for i, problem in enumerate(problems):
                f.write(f"### 问题 {i+1}: {problem.get('title', '未命名问题')}\n\n")
                f.write(f"- **ID**: {problem.get('id', 'unknown')}\n")
                f.write(f"- **严重程度**: {problem.get('severity', '未知')}\n")
                f.write(f"- **描述**: {problem.get('description', '无描述')}\n")
                
                if "steps_to_reproduce" in problem:
                    f.write("\n**重现步骤**:\n\n")
                    for j, step in enumerate(problem["steps_to_reproduce"]):
                        f.write(f"{j+1}. {step}\n")
                
                if "affected_components" in problem:
                    f.write("\n**受影响组件**:\n\n")
                    for component in problem["affected_components"]:
                        f.write(f"- {component}\n")
                
                if "screenshots" in problem:
                    f.write("\n**相关截图**:\n\n")
                    for screenshot in problem["screenshots"]:
                        f.write(f"- [{os.path.basename(screenshot)}]({screenshot})\n")
                
                f.write("\n")
            
            # 问题分析
            f.write("## 问题分析\n\n")
            
            # 这里可以添加更多的问题分析内容
            f.write("根据以上问题的特征和分布，我们可以得出以下分析结论：\n\n")
            
            # 示例分析内容
            if len(problems) > 0:
                f.write("1. 主要问题集中在以下方面：\n")
                components = {}
                for problem in problems:
                    for component in problem.get("affected_components", []):
                        components[component] = components.get(component, 0) + 1
                
                for component, count in sorted(components.items(), key=lambda x: x[1], reverse=True)[:3]:
                    f.write(f"   - {component}: {count}个问题\n")
                
                f.write("\n2. 问题的可能原因：\n")
                f.write("   - 代码逻辑错误\n")
                f.write("   - 环境配置不当\n")
                f.write("   - 第三方依赖问题\n")
            else:
                f.write("未发现任何问题，系统运行正常。\n")
        
        logger.info(f"已生成问题定位文档: {output_path}")
        return output_path
    
    def generate_fix_strategy_doc(self, strategies, output_path=None):
        """
        生成修复策略文档
        
        Args:
            strategies: 修复策略列表，每个策略是一个字典，包含problem_id、title、description、steps等字段
            output_path: 文档输出路径，如果为None则使用默认路径
            
        Returns:
            str: 文档文件路径
        """
        if output_path is None:
            output_path = os.path.join(self.log_dir, "fix_strategy.md")
        
        with open(output_path, "w", encoding="utf-8") as f:
            # 文档标题
            f.write("# 修复策略报告\n\n")
            
            # 生成时间
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"**生成时间**: {timestamp}\n\n")
            
            # 策略摘要
            f.write("## 策略摘要\n\n")
            f.write(f"共提出 {len(strategies)} 个修复策略：\n\n")
            
            priority_counts = {}
            for strategy in strategies:
                priority = strategy.get("priority", "未知")
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            for priority, count in priority_counts.items():
                f.write(f"- {priority}优先级: {count}个\n")
            
            f.write("\n")
            
            # 详细策略列表
            f.write("## 详细策略列表\n\n")
            
            for i, strategy in enumerate(strategies):
                f.write(f"### 策略 {i+1}: {strategy.get('title', '未命名策略')}\n\n")
                f.write(f"- **问题ID**: {strategy.get('problem_id', 'unknown')}\n")
                f.write(f"- **优先级**: {strategy.get('priority', '未知')}\n")
                f.write(f"- **描述**: {strategy.get('description', '无描述')}\n")
                
                if "steps" in strategy:
                    f.write("\n**修复步骤**:\n\n")
                    for j, step in enumerate(strategy["steps"]):
                        f.write(f"{j+1}. {step}\n")
                
                if "affected_files" in strategy:
                    f.write("\n**受影响文件**:\n\n")
                    for file in strategy["affected_files"]:
                        f.write(f"- {file}\n")
                
                if "code_changes" in strategy:
                    f.write("\n**代码变更**:\n\n")
                    for change in strategy["code_changes"]:
                        f.write(f"**{change.get('file', '未知文件')}**:\n\n")
                        f.write("```diff\n")
                        f.write(change.get("diff", "无变更内容"))
                        f.write("\n```\n\n")
                
                f.write("\n")
            
            # 实施计划
            f.write("## 实施计划\n\n")
            
            # 按优先级排序
            priority_order = {"高": 0, "中": 1, "低": 2}
            sorted_strategies = sorted(strategies, key=lambda s: priority_order.get(s.get("priority", "低"), 3))
            
            f.write("根据问题的优先级和依赖关系，我们建议按以下顺序实施修复：\n\n")
            
            for i, strategy in enumerate(sorted_strategies):
                f.write(f"{i+1}. **{strategy.get('title', '未命名策略')}** ({strategy.get('priority', '未知')}优先级)\n")
                f.write(f"   - 预计工作量: {strategy.get('estimated_effort', '未知')}\n")
                f.write(f"   - 预计影响范围: {strategy.get('impact_scope', '未知')}\n")
            
            f.write("\n")
            
            # 风险评估
            f.write("## 风险评估\n\n")
            f.write("实施上述修复策略可能带来以下风险：\n\n")
            
            # 示例风险内容
            f.write("1. **回归风险**：修复可能影响现有功能的正常运行\n")
            f.write("   - 缓解措施：全面的回归测试\n")
            f.write("2. **性能风险**：某些修复可能影响系统性能\n")
            f.write("   - 缓解措施：性能测试和监控\n")
            f.write("3. **兼容性风险**：修复可能影响与其他系统的兼容性\n")
            f.write("   - 缓解措施：集成测试和兼容性验证\n")
        
        logger.info(f"已生成修复策略文档: {output_path}")
        return output_path
    
    def generate_test_plan_doc(self, test_cases, output_path=None):
        """
        生成测试方案文档
        
        Args:
            test_cases: 测试用例列表，每个用例是一个字典，包含id、title、description、steps、expected_results等字段
            output_path: 文档输出路径，如果为None则使用默认路径
            
        Returns:
            str: 文档文件路径
        """
        if output_path is None:
            output_path = os.path.join(self.log_dir, "test_plan.md")
        
        with open(output_path, "w", encoding="utf-8") as f:
            # 文档标题
            f.write("# 测试方案报告\n\n")
            
            # 生成时间
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"**生成时间**: {timestamp}\n\n")
            
            # 测试摘要
            f.write("## 测试摘要\n\n")
            f.write(f"共设计 {len(test_cases)} 个测试用例：\n\n")
            
            type_counts = {}
            for case in test_cases:
                case_type = case.get("type", "未知")
                type_counts[case_type] = type_counts.get(case_type, 0) + 1
            
            for case_type, count in type_counts.items():
                f.write(f"- {case_type}: {count}个\n")
            
            f.write("\n")
            
            # 测试环境
            f.write("## 测试环境\n\n")
            f.write("- **操作系统**: macOS Sonoma (14.x)\n")
            f.write("- **浏览器**: Chrome 最新版\n")
            f.write("- **测试工具**: Playwright\n")
            f.write("- **测试数据**: 使用模拟数据和真实数据结合\n\n")
            
            # 详细测试用例
            f.write("## 详细测试用例\n\n")
            
            for i, case in enumerate(test_cases):
                f.write(f"### 用例 {i+1}: {case.get('title', '未命名用例')}\n\n")
                f.write(f"- **ID**: {case.get('id', 'unknown')}\n")
                f.write(f"- **类型**: {case.get('type', '未知')}\n")
                f.write(f"- **优先级**: {case.get('priority', '未知')}\n")
                f.write(f"- **描述**: {case.get('description', '无描述')}\n")
                
                if "preconditions" in case:
                    f.write("\n**前置条件**:\n\n")
                    for precond in case["preconditions"]:
                        f.write(f"- {precond}\n")
                
                if "steps" in case:
                    f.write("\n**测试步骤**:\n\n")
                    for j, step in enumerate(case["steps"]):
                        f.write(f"{j+1}. {step}\n")
                
                if "expected_results" in case:
                    f.write("\n**预期结果**:\n\n")
                    for result in case["expected_results"]:
                        f.write(f"- {result}\n")
                
                if "verification_points" in case:
                    f.write("\n**验证点**:\n\n")
                    for point in case["verification_points"]:
                        f.write(f"- {point}\n")
                
                f.write("\n")
            
            # 测试执行计划
            f.write("## 测试执行计划\n\n")
            
            # 按优先级排序
            priority_order = {"高": 0, "中": 1, "低": 2}
            sorted_cases = sorted(test_cases, key=lambda c: priority_order.get(c.get("priority", "低"), 3))
            
            f.write("测试将按以下顺序执行：\n\n")
            
            # 冒烟测试
            smoke_tests = [case for case in sorted_cases if case.get("type") == "冒烟测试"]
            if smoke_tests:
                f.write("### 第1阶段：冒烟测试\n\n")
                for i, case in enumerate(smoke_tests):
                    f.write(f"{i+1}. {case.get('title')}\n")
                f.write("\n")
            
            # 功能测试
            func_tests = [case for case in sorted_cases if case.get("type") == "功能测试"]
            if func_tests:
                f.write("### 第2阶段：功能测试\n\n")
                for i, case in enumerate(func_tests):
                    f.write(f"{i+1}. {case.get('title')}\n")
                f.write("\n")
            
            # 回归测试
            regression_tests = [case for case in sorted_cases if case.get("type") == "回归测试"]
            if regression_tests:
                f.write("### 第3阶段：回归测试\n\n")
                for i, case in enumerate(regression_tests):
                    f.write(f"{i+1}. {case.get('title')}\n")
                f.write("\n")
            
            # 其他测试
            other_tests = [case for case in sorted_cases if case.get("type") not in ["冒烟测试", "功能测试", "回归测试"]]
            if other_tests:
                f.write("### 第4阶段：其他测试\n\n")
                for i, case in enumerate(other_tests):
                    f.write(f"{i+1}. {case.get('title')} ({case.get('type')})\n")
                f.write("\n")
            
            # 测试结果报告
            f.write("## 测试结果报告\n\n")
            f.write("测试完成后，将生成包含以下内容的测试结果报告：\n\n")
            f.write("1. **测试摘要**：测试用例总数、通过数、失败数、阻塞数\n")
            f.write("2. **详细测试结果**：每个测试用例的执行结果和发现的问题\n")
            f.write("3. **问题分析**：发现问题的分类和严重程度分析\n")
            f.write("4. **测试证据**：截图、日志和其他测试证据\n")
            f.write("5. **建议**：基于测试结果的建议和下一步行动\n")
        
        logger.info(f"已生成测试方案文档: {output_path}")
        return output_path
