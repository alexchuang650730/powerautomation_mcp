"""
Manus问题解决驱动器模块 - ManusProblemSolver

该模块用于驱动Manus进行问题定位、提出修复策略和测试方案。
主要功能：
1. 分析测试日志和README中的问题
2. 调用Manus能力进行问题定位
3. 生成修复策略建议
4. 提出测试方案
5. 结构化输出结果
6. 版本回滚管理：支持每个版本的回滚，在持续出错时回滚至保存点

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
import shutil
import subprocess
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

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
    Manus问题解决驱动器，负责分析问题、提出修复策略和测试方案。
    支持版本回滚功能，在持续出错时可回滚至保存点。
    """
    
    def __init__(self, 
                 repo_path: Optional[str] = None,
                 enhanced_recorder: Optional[Any] = None,
                 test_updater: Optional[Any] = None,
                 rules_checker: Optional[Any] = None):
        """
        初始化Manus问题解决驱动器
        
        Args:
            repo_path: 代码仓库路径，如果为None则使用默认路径
            enhanced_recorder: 增强型记录器实例，如果为None则创建新实例
            test_updater: 测试更新器实例，如果为None则创建新实例
            rules_checker: 规则检查器实例，如果为None则创建新实例
        """
        self.repo_path = repo_path or os.path.expanduser("~/powerassistant/powerautomation")
        
        # 确保目录存在
        os.makedirs(self.repo_path, exist_ok=True)
        
        # 保存点目录
        self.save_points_dir = os.path.join(self.repo_path, ".save_points")
        os.makedirs(self.save_points_dir, exist_ok=True)
        
        # 解决方案输出目录
        self.solutions_dir = os.path.join(self.repo_path, "manus_solutions")
        os.makedirs(self.solutions_dir, exist_ok=True)
        
        # 组件实例
        self.recorder = enhanced_recorder or ThoughtActionRecorder()
        self.test_updater = test_updater
        self.rules_checker = rules_checker
        
        # 保存点索引文件
        self.save_points_index_file = os.path.join(self.save_points_dir, "index.json")
        if not os.path.exists(self.save_points_index_file):
            with open(self.save_points_index_file, "w") as f:
                json.dump({"save_points": []}, f)
    
    def analyze_issues_and_generate_solutions(self, issues: Optional[List[Dict]] = None) -> Dict:
        """
        分析问题并生成解决方案
        
        Args:
            issues: 问题列表，如果为None则从README和测试日志中提取
            
        Returns:
            Dict: 包含问题定位、修复策略和测试方案的解决方案
        """
        self.recorder.record_thought("开始分析问题并生成解决方案")
        
        # 如果未提供问题列表，则从README和测试日志中提取
        if issues is None:
            issues = self._extract_issues_from_readme_and_logs()
        
        if not issues:
            self.recorder.record_action(
                "analyze_issues", 
                {"issues_count": 0},
                {"status": "no_issues", "message": "未发现需要解决的问题"}
            )
            return {
                "status": "no_issues",
                "message": "未发现需要解决的问题",
                "timestamp": datetime.now().isoformat()
            }
        
        # 记录发现的问题
        self.recorder.record_action(
            "extract_issues", 
            {},
            {"issues_count": len(issues), "issues": issues}
        )
        
        # 分析每个问题并生成解决方案
        solutions = []
        for issue in issues:
            solution = self._analyze_single_issue(issue)
            solutions.append(solution)
        
        # 生成综合报告
        report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "issues_count": len(issues),
            "solutions_count": len(solutions),
            "solutions": solutions
        }
        
        self.recorder.record_action(
            "generate_solutions", 
            {"issues_count": len(issues)},
            {"solutions_count": len(solutions)}
        )
        
        return report
    
    def save_solutions_to_file(self, solutions: Dict, output_dir: Optional[str] = None) -> str:
        """
        将解决方案保存到文件
        
        Args:
            solutions: 解决方案字典
            output_dir: 输出目录，如果为None则使用默认目录
            
        Returns:
            str: 保存的文件路径
        """
        output_dir = output_dir or self.solutions_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"solutions_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # 保存到文件
        with open(filepath, "w") as f:
            json.dump(solutions, f, indent=2)
        
        self.recorder.record_action(
            "save_solutions", 
            {"output_dir": output_dir},
            {"filepath": filepath}
        )
        
        return filepath
    
    def create_save_point(self, name: Optional[str] = None) -> Dict:
        """
        创建版本保存点
        
        Args:
            name: 保存点名称，如果为None则使用时间戳
            
        Returns:
            Dict: 保存点信息
        """
        # 生成保存点ID和名称
        save_point_id = int(time.time())
        if name is None:
            name = f"save_point_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建保存点目录
        save_point_dir = os.path.join(self.save_points_dir, str(save_point_id))
        os.makedirs(save_point_dir, exist_ok=True)
        
        # 复制当前代码到保存点目录
        self._copy_code_to_save_point(save_point_dir)
        
        # 更新保存点索引
        save_point_info = {
            "id": save_point_id,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "directory": save_point_dir
        }
        
        with open(self.save_points_index_file, "r") as f:
            index = json.load(f)
        
        index["save_points"].append(save_point_info)
        
        with open(self.save_points_index_file, "w") as f:
            json.dump(index, f, indent=2)
        
        self.recorder.record_action(
            "create_save_point", 
            {"name": name},
            save_point_info
        )
        
        return save_point_info
    
    def list_save_points(self) -> List[Dict]:
        """
        列出所有保存点
        
        Returns:
            List[Dict]: 保存点列表
        """
        with open(self.save_points_index_file, "r") as f:
            index = json.load(f)
        
        return index["save_points"]
    
    def rollback_to_save_point(self, save_point_id: Union[int, str]) -> Dict:
        """
        回滚到指定保存点
        
        Args:
            save_point_id: 保存点ID或名称
            
        Returns:
            Dict: 回滚结果
        """
        # 查找保存点
        save_point = self._find_save_point(save_point_id)
        if save_point is None:
            error_msg = f"未找到保存点: {save_point_id}"
            self.recorder.record_action(
                "rollback_to_save_point", 
                {"save_point_id": save_point_id},
                {"status": "error", "message": error_msg}
            )
            return {"status": "error", "message": error_msg}
        
        # 在回滚前创建当前状态的备份
        backup_info = self.create_save_point(f"auto_backup_before_rollback_to_{save_point['name']}")
        
        # 从保存点复制代码到当前目录
        self._copy_code_from_save_point(save_point["directory"])
        
        result = {
            "status": "success",
            "message": f"成功回滚到保存点: {save_point['name']}",
            "save_point": save_point,
            "backup": backup_info,
            "timestamp": datetime.now().isoformat()
        }
        
        self.recorder.record_action(
            "rollback_to_save_point", 
            {"save_point_id": save_point_id},
            result
        )
        
        return result
    
    def _extract_issues_from_readme_and_logs(self) -> List[Dict]:
        """
        从README和测试日志中提取问题
        
        Returns:
            List[Dict]: 问题列表
        """
        issues = []
        
        # 从README中提取问题
        readme_path = os.path.join(self.repo_path, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r") as f:
                readme_content = f.read()
            
            # 查找问题部分
            issues_section_pattern = r"## 问题列表\s+(.+?)(?=##|\Z)"
            issues_match = re.search(issues_section_pattern, readme_content, re.DOTALL)
            
            if issues_match:
                issues_section = issues_match.group(1)
                
                # 提取每个问题
                issue_pattern = r"- \[([ x])\] (.+?)(?=\n- \[|$)"
                for issue_match in re.finditer(issue_pattern, issues_section, re.DOTALL):
                    status = issue_match.group(1)
                    description = issue_match.group(2).strip()
                    
                    # 只关注未解决的问题
                    if status != "x":
                        issues.append({
                            "source": "readme",
                            "description": description,
                            "status": "open"
                        })
        
        # 从测试日志中提取问题
        logs_dir = os.path.join(self.repo_path, "logs")
        if os.path.exists(logs_dir):
            log_files = [f for f in os.listdir(logs_dir) if f.endswith(".log")]
            
            for log_file in sorted(log_files, reverse=True)[:5]:  # 只检查最新的5个日志文件
                log_path = os.path.join(logs_dir, log_file)
                
                with open(log_path, "r") as f:
                    log_content = f.read()
                
                # 查找错误和警告
                error_pattern = r"(ERROR|CRITICAL|EXCEPTION|FAIL|FAILED).*?:(.+?)(?=\n\d{4}-\d{2}-\d{2}|\Z)"
                for error_match in re.finditer(error_pattern, log_content, re.IGNORECASE | re.DOTALL):
                    error_type = error_match.group(1)
                    error_message = error_match.group(2).strip()
                    
                    # 检查是否已存在相同问题
                    duplicate = False
                    for issue in issues:
                        if error_message in issue["description"]:
                            duplicate = True
                            break
                    
                    if not duplicate:
                        issues.append({
                            "source": f"log_{log_file}",
                            "description": f"{error_type}: {error_message}",
                            "status": "open"
                        })
        
        return issues
    
    def _analyze_single_issue(self, issue: Dict) -> Dict:
        """
        分析单个问题并生成解决方案
        
        Args:
            issue: 问题字典
            
        Returns:
            Dict: 解决方案
        """
        self.recorder.record_thought(f"分析问题: {issue['description']}")
        
        # 问题定位
        problem_location = self._locate_problem(issue)
        
        # 修复策略
        fix_strategy = self._generate_fix_strategy(issue, problem_location)
        
        # 测试方案
        test_plan = self._generate_test_plan(issue, fix_strategy)
        
        solution = {
            "issue": issue,
            "problem_location": problem_location,
            "fix_strategy": fix_strategy,
            "test_plan": test_plan,
            "timestamp": datetime.now().isoformat()
        }
        
        self.recorder.record_action(
            "analyze_issue", 
            {"issue": issue},
            {"solution": solution}
        )
        
        return solution
    
    def _locate_problem(self, issue: Dict) -> Dict:
        """
        定位问题
        
        Args:
            issue: 问题字典
            
        Returns:
            Dict: 问题位置信息
        """
        self.recorder.record_thought(f"定位问题: {issue['description']}")
        
        # 根据问题描述查找相关文件
        related_files = self._find_related_files(issue["description"])
        
        # 分析问题类型
        problem_type = self._analyze_problem_type(issue["description"])
        
        # 定位问题代码
        code_snippets = self._locate_problem_code(related_files, issue["description"])
        
        location = {
            "related_files": related_files,
            "problem_type": problem_type,
            "code_snippets": code_snippets
        }
        
        self.recorder.record_action(
            "locate_problem", 
            {"issue": issue},
            {"location": location}
        )
        
        return location
    
    def _generate_fix_strategy(self, issue: Dict, problem_location: Dict) -> Dict:
        """
        生成修复策略
        
        Args:
            issue: 问题字典
            problem_location: 问题位置信息
            
        Returns:
            Dict: 修复策略
        """
        self.recorder.record_thought(f"生成修复策略: {issue['description']}")
        
        # 根据问题类型生成修复建议
        fix_suggestions = self._generate_fix_suggestions(
            issue["description"],
            problem_location["problem_type"],
            problem_location["code_snippets"]
        )
        
        # 生成代码修改建议
        code_changes = self._generate_code_changes(
            problem_location["related_files"],
            problem_location["code_snippets"],
            fix_suggestions
        )
        
        strategy = {
            "fix_suggestions": fix_suggestions,
            "code_changes": code_changes,
            "priority": self._determine_priority(issue)
        }
        
        self.recorder.record_action(
            "generate_fix_strategy", 
            {"issue": issue, "problem_location": problem_location},
            {"strategy": strategy}
        )
        
        return strategy
    
    def _generate_test_plan(self, issue: Dict, fix_strategy: Dict) -> Dict:
        """
        生成测试方案
        
        Args:
            issue: 问题字典
            fix_strategy: 修复策略
            
        Returns:
            Dict: 测试方案
        """
        self.recorder.record_thought(f"生成测试方案: {issue['description']}")
        
        # 生成测试步骤
        test_steps = self._generate_test_steps(issue["description"], fix_strategy)
        
        # 生成验证标准
        verification_criteria = self._generate_verification_criteria(issue["description"])
        
        plan = {
            "test_steps": test_steps,
            "verification_criteria": verification_criteria,
            "estimated_time": self._estimate_test_time(test_steps)
        }
        
        self.recorder.record_action(
            "generate_test_plan", 
            {"issue": issue, "fix_strategy": fix_strategy},
            {"plan": plan}
        )
        
        return plan
    
    def _find_related_files(self, issue_description: str) -> List[str]:
        """
        根据问题描述查找相关文件
        
        Args:
            issue_description: 问题描述
            
        Returns:
            List[str]: 相关文件路径列表
        """
        related_files = []
        
        # 从问题描述中提取可能的文件名或模块名
        file_patterns = [
            r"(?:in|at|from|file)\s+['\"]?([a-zA-Z0-9_/\.]+\.py)['\"]?",
            r"(?:module|class|function)\s+['\"]?([a-zA-Z0-9_/\.]+)['\"]?",
            r"([a-zA-Z0-9_]+)\.py"
        ]
        
        potential_files = []
        for pattern in file_patterns:
            matches = re.finditer(pattern, issue_description, re.IGNORECASE)
            for match in matches:
                potential_files.append(match.group(1))
        
        # 搜索仓库中的文件
        for root, _, files in os.walk(self.repo_path):
            if ".git" in root or "__pycache__" in root:
                continue
                
            for file in files:
                if not file.endswith(".py"):
                    continue
                    
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.repo_path)
                
                # 检查文件名是否匹配
                for potential_file in potential_files:
                    if potential_file in rel_path:
                        related_files.append(rel_path)
                        break
                        
                # 如果没有找到足够的文件，搜索文件内容
                if len(related_files) < 3:
                    try:
                        with open(file_path, "r") as f:
                            content = f.read()
                            
                        # 提取错误关键词
                        error_keywords = re.findall(r"error|exception|fail|bug|issue|problem", issue_description, re.IGNORECASE)
                        
                        # 检查文件内容是否包含关键词
                        for keyword in error_keywords:
                            if keyword.lower() in content.lower() and rel_path not in related_files:
                                related_files.append(rel_path)
                                break
                    except Exception:
                        pass
        
        return related_files[:5]  # 最多返回5个相关文件
    
    def _analyze_problem_type(self, issue_description: str) -> str:
        """
        分析问题类型
        
        Args:
            issue_description: 问题描述
            
        Returns:
            str: 问题类型
        """
        # 定义问题类型及其关键词
        problem_types = {
            "syntax_error": ["syntax error", "invalid syntax", "unexpected indent"],
            "runtime_error": ["runtime error", "exception", "traceback"],
            "logic_error": ["incorrect result", "wrong output", "unexpected behavior"],
            "performance_issue": ["slow", "performance", "timeout", "memory"],
            "ui_issue": ["ui", "interface", "display", "render"],
            "network_issue": ["network", "connection", "timeout", "api"],
            "compatibility_issue": ["compatibility", "version", "platform"],
            "security_issue": ["security", "vulnerability", "exploit"]
        }
        
        # 检查问题描述是否包含各类型的关键词
        for problem_type, keywords in problem_types.items():
            for keyword in keywords:
                if keyword.lower() in issue_description.lower():
                    return problem_type
        
        return "unknown"
    
    def _locate_problem_code(self, related_files: List[str], issue_description: str) -> List[Dict]:
        """
        定位问题代码
        
        Args:
            related_files: 相关文件路径列表
            issue_description: 问题描述
            
        Returns:
            List[Dict]: 问题代码片段列表
        """
        code_snippets = []
        
        # 提取错误关键词
        error_keywords = re.findall(r"error|exception|fail|bug|issue|problem", issue_description, re.IGNORECASE)
        
        # 检查每个相关文件
        for file_path in related_files:
            full_path = os.path.join(self.repo_path, file_path)
            
            try:
                with open(full_path, "r") as f:
                    lines = f.readlines()
                
                # 搜索包含关键词的行
                for i, line in enumerate(lines):
                    for keyword in error_keywords:
                        if keyword.lower() in line.lower():
                            # 提取上下文（前后各5行）
                            start = max(0, i - 5)
                            end = min(len(lines), i + 6)
                            context = "".join(lines[start:end])
                            
                            code_snippets.append({
                                "file": file_path,
                                "line": i + 1,
                                "code": line.strip(),
                                "context": context
                            })
                            break
            except Exception:
                pass
        
        return code_snippets
    
    def _generate_fix_suggestions(self, issue_description: str, problem_type: str, code_snippets: List[Dict]) -> List[str]:
        """
        生成修复建议
        
        Args:
            issue_description: 问题描述
            problem_type: 问题类型
            code_snippets: 问题代码片段列表
            
        Returns:
            List[str]: 修复建议列表
        """
        suggestions = []
        
        # 根据问题类型生成通用建议
        if problem_type == "syntax_error":
            suggestions.append("检查代码语法，确保括号、缩进和引号正确")
            suggestions.append("使用代码格式化工具（如autopep8或black）格式化代码")
        elif problem_type == "runtime_error":
            suggestions.append("添加异常处理代码，捕获并处理可能的异常")
            suggestions.append("检查变量类型和值，确保符合函数或方法的要求")
        elif problem_type == "logic_error":
            suggestions.append("检查算法逻辑，确保符合预期")
            suggestions.append("添加单元测试，验证函数或方法的行为")
        elif problem_type == "performance_issue":
            suggestions.append("优化算法或数据结构，提高性能")
            suggestions.append("使用性能分析工具（如cProfile）定位性能瓶颈")
        elif problem_type == "ui_issue":
            suggestions.append("检查UI元素的样式和布局")
            suggestions.append("确保UI适配不同屏幕尺寸和分辨率")
        elif problem_type == "network_issue":
            suggestions.append("添加网络错误处理和重试机制")
            suggestions.append("检查API调用参数和响应处理")
        elif problem_type == "compatibility_issue":
            suggestions.append("检查代码是否兼容目标平台或版本")
            suggestions.append("添加条件代码处理不同平台或版本的差异")
        elif problem_type == "security_issue":
            suggestions.append("检查输入验证和过滤")
            suggestions.append("使用安全的API和库")
        
        # 根据代码片段生成具体建议
        for snippet in code_snippets:
            if "undefined" in snippet["code"] or "not defined" in snippet["code"]:
                suggestions.append(f"在{snippet['file']}第{snippet['line']}行，检查变量是否已定义")
            elif "import" in snippet["code"] and ("error" in snippet["code"] or "not found" in snippet["code"]):
                suggestions.append(f"在{snippet['file']}第{snippet['line']}行，检查导入的模块是否已安装")
            elif "index" in snippet["code"] and ("out of range" in snippet["code"] or "out of bounds" in snippet["code"]):
                suggestions.append(f"在{snippet['file']}第{snippet['line']}行，检查索引是否越界")
            elif "null" in snippet["code"] or "None" in snippet["code"]:
                suggestions.append(f"在{snippet['file']}第{snippet['line']}行，添加空值检查")
        
        return suggestions
    
    def _generate_code_changes(self, related_files: List[str], code_snippets: List[Dict], fix_suggestions: List[str]) -> List[Dict]:
        """
        生成代码修改建议
        
        Args:
            related_files: 相关文件路径列表
            code_snippets: 问题代码片段列表
            fix_suggestions: 修复建议列表
            
        Returns:
            List[Dict]: 代码修改建议列表
        """
        code_changes = []
        
        # 根据代码片段和修复建议生成代码修改
        for snippet in code_snippets:
            file_path = snippet["file"]
            line_number = snippet["line"]
            original_code = snippet["code"]
            
            # 根据问题类型生成修改建议
            if "undefined" in original_code or "not defined" in original_code:
                # 提取变量名
                var_match = re.search(r"'([a-zA-Z0-9_]+)'", original_code)
                if var_match:
                    var_name = var_match.group(1)
                    new_code = f"{var_name} = None  # TODO: 初始化变量\n{original_code}"
                    
                    code_changes.append({
                        "file": file_path,
                        "line": line_number,
                        "original_code": original_code,
                        "new_code": new_code,
                        "explanation": f"初始化变量 {var_name}"
                    })
            elif "import" in original_code and ("error" in original_code or "not found" in original_code):
                # 提取模块名
                module_match = re.search(r"import ([a-zA-Z0-9_]+)", original_code)
                if module_match:
                    module_name = module_match.group(1)
                    new_code = f"try:\n    {original_code}\nexcept ImportError:\n    print(f\"请安装 {module_name} 模块\")\n    # pip install {module_name}"
                    
                    code_changes.append({
                        "file": file_path,
                        "line": line_number,
                        "original_code": original_code,
                        "new_code": new_code,
                        "explanation": f"添加导入错误处理，提示安装 {module_name} 模块"
                    })
            elif "index" in original_code and ("out of range" in original_code or "out of bounds" in original_code):
                new_code = f"if index < len(array):\n    {original_code}\nelse:\n    print(\"索引越界\")"
                
                code_changes.append({
                    "file": file_path,
                    "line": line_number,
                    "original_code": original_code,
                    "new_code": new_code,
                    "explanation": "添加索引越界检查"
                })
            elif "null" in original_code or "None" in original_code:
                new_code = f"if variable is not None:\n    {original_code}\nelse:\n    print(\"变量为空\")"
                
                code_changes.append({
                    "file": file_path,
                    "line": line_number,
                    "original_code": original_code,
                    "new_code": new_code,
                    "explanation": "添加空值检查"
                })
        
        return code_changes
    
    def _determine_priority(self, issue: Dict) -> str:
        """
        确定问题优先级
        
        Args:
            issue: 问题字典
            
        Returns:
            str: 优先级（high, medium, low）
        """
        description = issue["description"].lower()
        
        # 高优先级关键词
        high_priority_keywords = ["crash", "critical", "urgent", "blocker", "security", "data loss"]
        for keyword in high_priority_keywords:
            if keyword in description:
                return "high"
        
        # 中优先级关键词
        medium_priority_keywords = ["error", "bug", "issue", "problem", "fail"]
        for keyword in medium_priority_keywords:
            if keyword in description:
                return "medium"
        
        return "low"
    
    def _generate_test_steps(self, issue_description: str, fix_strategy: Dict) -> List[str]:
        """
        生成测试步骤
        
        Args:
            issue_description: 问题描述
            fix_strategy: 修复策略
            
        Returns:
            List[str]: 测试步骤列表
        """
        test_steps = [
            "准备测试环境",
            "启动应用",
            "验证修复是否解决了问题",
            "检查是否引入了新问题",
            "记录测试结果"
        ]
        
        # 根据问题描述添加特定步骤
        if "ui" in issue_description.lower() or "interface" in issue_description.lower():
            test_steps.insert(2, "检查UI元素是否正确显示")
            test_steps.insert(3, "测试不同屏幕尺寸和分辨率")
        elif "performance" in issue_description.lower():
            test_steps.insert(2, "测量操作执行时间")
            test_steps.insert(3, "比较修复前后的性能差异")
        elif "network" in issue_description.lower():
            test_steps.insert(2, "测试在不同网络条件下的行为")
            test_steps.insert(3, "模拟网络错误和超时情况")
        
        return test_steps
    
    def _generate_verification_criteria(self, issue_description: str) -> List[str]:
        """
        生成验证标准
        
        Args:
            issue_description: 问题描述
            
        Returns:
            List[str]: 验证标准列表
        """
        criteria = [
            "问题不再复现",
            "应用正常运行",
            "没有引入新问题",
            "代码符合项目规范"
        ]
        
        # 根据问题描述添加特定标准
        if "performance" in issue_description.lower():
            criteria.append("操作执行时间符合预期")
        elif "ui" in issue_description.lower():
            criteria.append("UI元素正确显示")
            criteria.append("布局在不同屏幕尺寸下正确")
        elif "network" in issue_description.lower():
            criteria.append("网络错误处理正确")
            criteria.append("超时情况下行为符合预期")
        
        return criteria
    
    def _estimate_test_time(self, test_steps: List[str]) -> str:
        """
        估计测试时间
        
        Args:
            test_steps: 测试步骤列表
            
        Returns:
            str: 估计时间（如"30分钟"）
        """
        # 简单估计：每个步骤5-10分钟
        minutes = len(test_steps) * 7  # 平均7分钟
        
        if minutes < 60:
            return f"{minutes}分钟"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours}小时{remaining_minutes}分钟"
    
    def _copy_code_to_save_point(self, save_point_dir: str) -> None:
        """
        复制当前代码到保存点目录
        
        Args:
            save_point_dir: 保存点目录
        """
        # 复制代码文件
        for root, dirs, files in os.walk(self.repo_path):
            # 跳过.git、__pycache__和保存点目录
            if ".git" in root or "__pycache__" in root or self.save_points_dir in root:
                continue
            
            for file in files:
                # 跳过临时文件和大型二进制文件
                if file.endswith((".pyc", ".pyo", ".so", ".dll", ".exe", ".bin")):
                    continue
                
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, self.repo_path)
                dst_path = os.path.join(save_point_dir, rel_path)
                
                # 创建目标目录
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                
                # 复制文件
                shutil.copy2(src_path, dst_path)
    
    def _copy_code_from_save_point(self, save_point_dir: str) -> None:
        """
        从保存点复制代码到当前目录
        
        Args:
            save_point_dir: 保存点目录
        """
        # 复制代码文件
        for root, dirs, files in os.walk(save_point_dir):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, save_point_dir)
                dst_path = os.path.join(self.repo_path, rel_path)
                
                # 创建目标目录
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                
                # 复制文件
                shutil.copy2(src_path, dst_path)
    
    def _find_save_point(self, save_point_id: Union[int, str]) -> Optional[Dict]:
        """
        查找保存点
        
        Args:
            save_point_id: 保存点ID或名称
            
        Returns:
            Optional[Dict]: 保存点信息，如果未找到则返回None
        """
        with open(self.save_points_index_file, "r") as f:
            index = json.load(f)
        
        # 按ID查找
        if isinstance(save_point_id, int) or save_point_id.isdigit():
            save_point_id = int(save_point_id)
            for save_point in index["save_points"]:
                if save_point["id"] == save_point_id:
                    return save_point
        # 按名称查找
        else:
            for save_point in index["save_points"]:
                if save_point["name"] == save_point_id:
                    return save_point
        
        return None
