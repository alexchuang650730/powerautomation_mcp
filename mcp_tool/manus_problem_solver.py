"""
Manus驱动的问题定位与修复建议模块 - ManusProblemSolver

该模块负责分析自动化测试和视觉日志中发现的问题，
自动生成结构化的问题定位报告、修复策略和测试方案。

作者: Manus AI
日期: 2025-05-28
"""

import os
import time
import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format=\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\'
)
logger = logging.getLogger("ManusProblemSolver")

class ManusProblemSolver:
    """
    Manus驱动的问题定位与修复建议器。
    分析测试问题和日志，生成定位报告、修复策略和测试方案。
    """
    
    def __init__(self, 
                 repo_path: str,
                 enhanced_recorder = None,
                 test_updater = None,
                 rules_checker = None):
        """
        初始化问题解决器
        
        Args:
            repo_path: 本地仓库路径
            enhanced_recorder: 增强型思考记录器实例
            test_updater: 测试与README更新器实例
            rules_checker: Release规则检查器实例
        """
        self.repo_path = os.path.expanduser(repo_path)
        self.enhanced_recorder = enhanced_recorder
        self.test_updater = test_updater
        self.rules_checker = rules_checker
        
        logger.info(f"初始化Manus问题解决器: {self.repo_path}")
    
    def analyze_issues_and_generate_solutions(self, issues: Optional[List[Dict]] = None) -> List[Dict]:
        """
        分析问题并生成解决方案（定位、修复策略、测试方案）
        
        Args:
            issues: 问题列表，如果为None则从测试更新器获取
            
        Returns:
            List[Dict]: 解决方案列表，每个解决方案对应一个问题
        """
        if issues is None:
            if self.test_updater:
                issues = self.test_updater.issues
            else:
                logger.warning("没有提供问题列表，也无法从测试更新器获取")
                return []
        
        if not issues:
            logger.info("没有发现问题，无需生成解决方案")
            return []
        
        logger.info(f"开始分析 {len(issues)} 个问题并生成解决方案")
        
        solutions = []
        for issue in issues:
            solution = self._analyze_single_issue(issue)
            solutions.append(solution)
        
        logger.info(f"成功为 {len(solutions)} 个问题生成了解决方案")
        
        # 可选：将解决方案保存到文件
        self.save_solutions_to_file(solutions)
        
        return solutions
    
    def _analyze_single_issue(self, issue: Dict) -> Dict:
        """
        分析单个问题并生成解决方案
        
        Args:
            issue: 问题字典
            
        Returns:
            Dict: 解决方案字典
        """
        issue_id = issue.get("id", "unknown")
        title = issue.get("title", "未命名问题")
        description = issue.get("description", "")
        
        logger.info(f"分析问题: {issue_id} - {title}")
        
        # 1. 定位问题
        location_report = self._locate_problem(issue)
        
        # 2. 提出修复策略
        repair_strategy = self._propose_repair_strategy(issue, location_report)
        
        # 3. 制定测试方案
        test_plan = self._generate_test_plan(issue, repair_strategy)
        
        # 组合解决方案
        solution = {
            "issue_id": issue_id,
            "issue_title": title,
            "issue_description": description,
            "location_report": location_report,
            "repair_strategy": repair_strategy,
            "test_plan": test_plan,
            "generated_at": datetime.now().isoformat()
        }
        
        return solution
    
    def _locate_problem(self, issue: Dict) -> Dict:
        """
        定位问题
        
        Args:
            issue: 问题字典
            
        Returns:
            Dict: 问题定位报告
        """
        logger.info(f"定位问题: {issue.get(\'id\')}")
        
        report = {
            "possible_causes": [],
            "relevant_logs": [],
            "relevant_code_files": [],
            "confidence_score": 0.0
        }
        
        # 示例：基于问题描述和日志进行简单分析
        description = issue.get("description", "").lower()
        message = issue.get("message", "").lower()
        
        # 分析可能原因
        if "timeout" in description or "timeout" in message:
            report["possible_causes"].append("网络超时或性能问题")
            report["confidence_score"] = 0.6
        elif "not found" in description or "not found" in message or "404" in message:
            report["possible_causes"].append("资源未找到或URL错误")
            report["confidence_score"] = 0.7
        elif "permission denied" in description or "permission denied" in message or "403" in message:
            report["possible_causes"].append("权限不足")
            report["confidence_score"] = 0.8
        elif "import error" in description or "import error" in message:
            report["possible_causes"].append("缺少依赖或环境配置错误")
            report["confidence_score"] = 0.9
        elif "element not clickable" in description or "element not clickable" in message:
            report["possible_causes"].append("UI元素被遮挡或状态错误")
            report["confidence_score"] = 0.7
        else:
            report["possible_causes"].append("未知错误，需要进一步分析")
            report["confidence_score"] = 0.3
        
        # 查找相关日志
        if self.enhanced_recorder:
            # 获取问题发生时间附近的日志
            issue_time_str = issue.get("created_at")
            if issue_time_str:
                try:
                    issue_time = datetime.fromisoformat(issue_time_str)
                    # 获取前后5分钟的日志
                    start_time = issue_time.timestamp() - 300
                    end_time = issue_time.timestamp() + 300
                    
                    # TODO: 实现按时间范围查询日志的功能
                    # relevant_logs = self.enhanced_recorder.query_logs(start_time=start_time, end_time=end_time)
                    # report["relevant_logs"] = relevant_logs[:10] # 限制数量
                    
                    # 临时方案：获取最近的日志
                    report["relevant_logs"] = self.enhanced_recorder.get_latest_thoughts(limit=20, include_actions=True)
                except Exception as e:
                    logger.warning(f"无法根据时间查询日志: {e}")
                    report["relevant_logs"] = self.enhanced_recorder.get_latest_thoughts(limit=10, include_actions=True)
            else:
                report["relevant_logs"] = self.enhanced_recorder.get_latest_thoughts(limit=10, include_actions=True)
        
        # 查找相关代码文件（基于问题描述中的文件名或路径）
        # TODO: 实现更智能的代码文件定位
        file_match = re.search(r"in\s+([\w/\\.]+?\.py)", description + message)
        if file_match:
            file_path = file_match.group(1)
            # 检查文件是否存在于仓库中
            full_path = os.path.join(self.repo_path, file_path)
            if os.path.exists(full_path):
                report["relevant_code_files"].append(file_path)
            else:
                # 尝试在子目录中查找
                found = False
                for root, _, files in os.walk(self.repo_path):
                    if file_path in files:
                        rel_path = os.path.relpath(os.path.join(root, file_path), self.repo_path)
                        report["relevant_code_files"].append(rel_path)
                        found = True
                        break
                if not found:
                     report["relevant_code_files"].append(f"{file_path} (路径可能不准确)")
        
        # 增加置信度（如果找到相关文件）
        if report["relevant_code_files"]:
            report["confidence_score"] = min(report["confidence_score"] + 0.1, 1.0)
            
        logger.info(f"问题定位完成: {issue.get(\'id\')}, 置信度: {report[\'confidence_score\']:.2f}")
        return report
    
    def _propose_repair_strategy(self, issue: Dict, location_report: Dict) -> Dict:
        """
        提出修复策略
        
        Args:
            issue: 问题字典
            location_report: 问题定位报告
            
        Returns:
            Dict: 修复策略
        """
        logger.info(f"为问题 {issue.get(\'id\')} 提出修复策略")
        
        strategy = {
            "suggested_actions": [],
            "required_changes": [],
            "estimated_effort": "中",
            "potential_risks": []
        }
        
        possible_causes = location_report.get("possible_causes", [])
        relevant_files = location_report.get("relevant_code_files", [])
        
        # 示例：根据可能原因生成修复建议
        for cause in possible_causes:
            if "网络超时" in cause:
                strategy["suggested_actions"].append("检查网络连接和目标服务状态")
                strategy["suggested_actions"].append("增加超时时间或添加重试机制")
                strategy["potential_risks"].append("重试可能导致重复操作")
                strategy["estimated_effort"] = "低"
            elif "资源未找到" in cause:
                strategy["suggested_actions"].append("验证URL或资源路径是否正确")
                strategy["suggested_actions"].append("检查资源是否存在或已被移动/删除")
                if relevant_files:
                    strategy["required_changes"].append(f"修改文件 {relevant_files[0]} 中的URL或路径")
                strategy["estimated_effort"] = "低"
            elif "权限不足" in cause:
                strategy["suggested_actions"].append("检查访问凭证（如API密钥、令牌）是否正确且有效")
                strategy["suggested_actions"].append("确认账户是否具有所需权限")
                strategy["potential_risks"].append("提升权限可能带来安全风险")
                strategy["estimated_effort"] = "中"
            elif "缺少依赖" in cause:
                strategy["suggested_actions"].append("检查项目依赖文件（如requirements.txt）")
                strategy["suggested_actions"].append("运行 `pip install -r requirements.txt` 或类似命令安装依赖")
                strategy["required_changes"].append("更新依赖文件并重新安装")
                strategy["estimated_effort"] = "低"
            elif "UI元素被遮挡" in cause:
                strategy["suggested_actions"].append("检查测试执行时的UI布局")
                strategy["suggested_actions"].append("尝试添加等待时间或滚动操作")
                strategy["suggested_actions"].append("使用更精确的元素定位器")
                if relevant_files:
                    strategy["required_changes"].append(f"修改文件 {relevant_files[0]} 中的UI交互逻辑")
                strategy["estimated_effort"] = "中"
            else: # 未知错误
                strategy["suggested_actions"].append("仔细检查相关日志和截图")
                strategy["suggested_actions"].append("尝试手动重现问题")
                strategy["suggested_actions"].append("增加更详细的日志记录")
                strategy["estimated_effort"] = "高"
        
        # 添加通用建议
        strategy["suggested_actions"].append("查看相关文档或搜索类似错误")
        strategy["potential_risks"].append("修复可能引入新的问题（回归风险）")
        
        logger.info(f"修复策略生成完成: {issue.get(\'id\')}")
        return strategy
    
    def _generate_test_plan(self, issue: Dict, repair_strategy: Dict) -> Dict:
        """
        制定测试方案
        
        Args:
            issue: 问题字典
            repair_strategy: 修复策略
            
        Returns:
            Dict: 测试方案
        """
        logger.info(f"为问题 {issue.get(\'id\')} 制定测试方案")
        
        plan = {
            "test_objective": f"验证问题 	{issue.get(\'id\')}	 是否已修复，并确保修复未引入新问题",
            "test_scope": [],
            "test_cases": [],
            "pass_criteria": "所有相关测试用例通过，且未发现新的回归问题",
            "environment": "与问题发生时相同的环境（或指定的测试环境）"
        }
        
        # 定义测试范围
        plan["test_scope"].append("直接相关的测试用例")
        plan["test_scope"].append("受影响的功能模块")
        if repair_strategy.get("required_changes"): 
            plan["test_scope"].append("修改的代码文件及其关联功能")
        
        # 生成测试用例
        # 1. 回归测试：重新运行失败的测试用例
        failed_case_id = issue.get("test_case_id")
        if failed_case_id:
            plan["test_cases"].append({
                "id": f"regression_{failed_case_id}",
                "description": f"重新运行失败的测试用例 {failed_case_id}",
                "steps": issue.get("steps_to_reproduce", ["按照原始测试用例步骤执行"]),
                "expected_result": "测试用例通过，问题不再出现"
            })
        
        # 2. 验证修复：根据修复策略设计新的测试用例
        for i, action in enumerate(repair_strategy.get("suggested_actions", [])):
            if "检查" in action or "验证" in action:
                plan["test_cases"].append({
                    "id": f"verify_fix_{i+1}",
                    "description": f"验证修复措施：{action}",
                    "steps": [f"执行操作 	{action}	"],
                    "expected_result": "操作成功，符合预期"
                })
        
        # 3. 探索性测试：围绕修改点进行探索
        if repair_strategy.get("required_changes"):
            plan["test_cases"].append({
                "id": "exploratory_test_1",
                "description": "围绕修改的代码进行探索性测试",
                "steps": [
                    f"检查文件 {f}	 的修改",
                    "测试与修改相关的边界条件",
                    "测试异常输入和场景"
                ],
                "expected_result": "系统功能稳定，未发现新的异常"
            })
        
        # 4. 负面测试：验证潜在风险
        for i, risk in enumerate(repair_strategy.get("potential_risks", [])):
            plan["test_cases"].append({
                "id": f"negative_test_{i+1}",
                "description": f"验证潜在风险：{risk}",
                "steps": [f"模拟可能导致风险 	{risk}	 的场景"],
                "expected_result": "系统能够正确处理该场景，未出现风险描述的问题"
            })
            
        logger.info(f"测试方案制定完成: {issue.get(\'id\')}")
        return plan
    
    def save_solutions_to_file(self, solutions: List[Dict], output_dir: Optional[str] = None) -> str:
        """
        将解决方案保存到Markdown文件
        
        Args:
            solutions: 解决方案列表
            output_dir: 输出目录，如果为None则保存在仓库根目录
            
        Returns:
            str: 生成的报告文件路径
        """
        if output_dir is None:
            output_dir = self.repo_path
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"issue_analysis_report_{timestamp}.md")
        
        logger.info(f"保存问题分析报告: {output_path}")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# 问题分析与解决方案报告\n\n")
                f.write(f"**生成时间**: {datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}\n\n")
                f.write(f"本文档分析了最近一次测试中发现的问题，并提供了定位、修复策略和测试方案。\n\n")
                
                if not solutions:
                    f.write("未发现需要分析的问题。\n")
                    return output_path
                
                f.write(f"共分析了 {len(solutions)} 个问题。\n\n")
                
                for i, solution in enumerate(solutions):
                    issue_id = solution.get("issue_id", f"未知问题{i+1}")
                    issue_title = solution.get("issue_title", "")
                    
                    f.write(f"## 问题 {i+1}: {issue_id} - {issue_title}\n\n")
                    f.write(f"**描述**: {solution.get(\'issue_description\', \'无\')}\n\n")
                    
                    # 定位报告
                    f.write("### 1. 问题定位\n\n")
                    location = solution.get("location_report", {})
                    f.write(f"- **可能原因**: {\', \'.join(location.get(\'possible_causes\', [\'未知\']))}\n")
                    f.write(f"- **相关代码文件**: {\', \'.join(location.get(\'relevant_code_files\', [\'未找到\']))}\n")
                    f.write(f"- **定位置信度**: {location.get(\'confidence_score\', 0.0):.2f}\n")
                    # TODO: 添加相关日志展示
                    f.write("\n")
                    
                    # 修复策略
                    f.write("### 2. 修复策略\n\n")
                    strategy = solution.get("repair_strategy", {})
                    f.write("**建议操作**:\n")
                    for action in strategy.get("suggested_actions", []):
                        f.write(f"- {action}\n")
                    f.write("\n**需要修改**: ")
                    f.write(f"{', '.join(strategy.get('required_changes', ['无']))}\n")
                    f.write(f"**预计工作量**: {strategy.get(\'estimated_effort\', \'未知\')}\n")
                    f.write("**潜在风险**:\n")
                    for risk in strategy.get("potential_risks", []):
                        f.write(f"- {risk}\n")
                    f.write("\n")
                    
                    # 测试方案
                    f.write("### 3. 测试方案\n\n")
                    plan = solution.get("test_plan", {})
                    f.write(f"**测试目标**: {plan.get(\'test_objective\', \'无\')}\n")
                    f.write(f"**测试范围**: {', '.join(plan.get('test_scope', ['无']))}\n")
                    f.write("**测试用例**:\n")
                    for case in plan.get("test_cases", []):
                        f.write(f"- **{case.get(\'id\')}:** {case.get(\'description\')}\n")
                        f.write(f"  - **步骤**: {'; '.join(case.get('steps', []))}\n")
                        f.write(f"  - **预期**: {case.get(\'expected_result\')}\n")
                    f.write(f"**通过标准**: {plan.get(\'pass_criteria\', \'无\')}\n")
                    f.write(f"**测试环境**: {plan.get(\'environment\', \'无\')}\n")
                    f.write("\n---\n\n")
            
            logger.info(f"问题分析报告保存成功: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"保存问题分析报告失败: {e}")
            return ""
