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
7. 自动回滚：当测试方案持续出错超过5次时自动回滚到前一个保存点
8. Manus.im集成：使用大模型+自动化工具将问题提交给Manus.im平台

作者: Manus AI
日期: 2025-05-30
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
import threading
import webbrowser
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path

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
    集成Manus.im平台，通过大模型+自动化工具提交问题。
    """
    
    def __init__(self, 
                 repo_path: Optional[str] = None,
                 enhanced_recorder: Optional[Any] = None,
                 test_updater: Optional[Any] = None,
                 rules_checker: Optional[Any] = None,
                 manus_im_url: Optional[str] = "https://manus.im/app/dOwSylYaP4AL5S41JU3qO0"):
        """
        初始化Manus问题解决驱动器
        
        Args:
            repo_path: 代码仓库路径，如果为None则使用默认路径
            enhanced_recorder: 增强型记录器实例，如果为None则创建新实例
            test_updater: 测试更新器实例，如果为None则创建新实例
            rules_checker: 规则检查器实例，如果为None则创建新实例
            manus_im_url: Manus.im平台URL，默认为https://manus.im/app/dOwSylYaP4AL5S41JU3qO0
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
        
        # 错误计数器
        self.error_counter_file = os.path.join(self.repo_path, ".error_counter.json")
        if not os.path.exists(self.error_counter_file):
            with open(self.error_counter_file, "w") as f:
                json.dump({"error_count": 0, "last_error_time": None}, f)
        
        # Manus.im平台URL
        self.manus_im_url = manus_im_url
        
        # 自动化工具目录
        self.automation_tools_dir = os.path.join(self.repo_path, "automation_tools")
        os.makedirs(self.automation_tools_dir, exist_ok=True)
        
        # 问题提交历史
        self.submission_history_file = os.path.join(self.repo_path, ".submission_history.json")
        if not os.path.exists(self.submission_history_file):
            with open(self.submission_history_file, "w") as f:
                json.dump({"submissions": []}, f)
    
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
        
        # 重置错误计数器
        self._reset_error_counter()
        
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
    
    def rollback_to_previous_save_point(self) -> Dict:
        """
        回滚到前一个保存点
        
        Returns:
            Dict: 回滚结果
        """
        # 获取所有保存点
        save_points = self.list_save_points()
        
        if not save_points:
            error_msg = "没有可用的保存点"
            self.recorder.record_action(
                "rollback_to_previous_save_point", 
                {},
                {"status": "error", "message": error_msg}
            )
            return {"status": "error", "message": error_msg}
        
        # 按时间戳排序
        save_points.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 如果只有一个保存点，则回滚到该保存点
        if len(save_points) == 1:
            return self.rollback_to_save_point(save_points[0]["id"])
        
        # 否则回滚到前一个保存点
        return self.rollback_to_save_point(save_points[1]["id"])
    
    def record_test_error(self) -> Dict:
        """
        记录测试错误，并在错误次数超过阈值时自动回滚
        
        Returns:
            Dict: 记录结果，包括是否触发自动回滚
        """
        # 读取当前错误计数
        with open(self.error_counter_file, "r") as f:
            counter_data = json.load(f)
        
        # 更新错误计数
        counter_data["error_count"] += 1
        counter_data["last_error_time"] = datetime.now().isoformat()
        
        # 保存更新后的错误计数
        with open(self.error_counter_file, "w") as f:
            json.dump(counter_data, f, indent=2)
        
        result = {
            "status": "recorded",
            "error_count": counter_data["error_count"],
            "last_error_time": counter_data["last_error_time"],
            "auto_rollback": False
        }
        
        # 检查是否需要自动回滚
        if counter_data["error_count"] >= 5:
            self.recorder.record_thought(f"错误次数({counter_data['error_count']})已超过阈值(5)，准备自动回滚到前一个保存点")
            
            # 执行自动回滚
            rollback_result = self.rollback_to_previous_save_point()
            
            result["auto_rollback"] = True
            result["rollback_result"] = rollback_result
            
            # 重置错误计数器
            self._reset_error_counter()
            
            # 将问题提交给Manus.im平台
            issues = self._extract_issues_from_readme_and_logs()
            if issues:
                submission_result = self.submit_issues_to_manus_im(issues)
                result["submission_result"] = submission_result
        
        self.recorder.record_action(
            "record_test_error", 
            {},
            result
        )
        
        return result
    
    def _reset_error_counter(self) -> None:
        """
        重置错误计数器
        """
        with open(self.error_counter_file, "w") as f:
            json.dump({"error_count": 0, "last_error_time": None}, f)
    
    def submit_issues_to_manus_im(self, issues: List[Dict]) -> Dict:
        """
        使用大模型+自动化工具将问题提交给Manus.im平台
        
        Args:
            issues: 问题列表
            
        Returns:
            Dict: 提交结果
        """
        self.recorder.record_thought("准备使用大模型+自动化工具将问题提交给Manus.im平台")
        
        # 准备问题摘要
        issues_summary = self._prepare_issues_summary(issues)
        
        # 生成自动化脚本
        script_path = self._generate_automation_script(issues_summary)
        
        # 执行自动化脚本
        result = self._execute_automation_script(script_path)
        
        # 记录提交历史
        submission_record = {
            "timestamp": datetime.now().isoformat(),
            "issues_count": len(issues),
            "issues_summary": issues_summary,
            "result": result
        }
        
        with open(self.submission_history_file, "r") as f:
            history = json.load(f)
        
        history["submissions"].append(submission_record)
        
        with open(self.submission_history_file, "w") as f:
            json.dump(history, f, indent=2)
        
        self.recorder.record_action(
            "submit_issues_to_manus_im", 
            {"issues_count": len(issues)},
            result
        )
        
        return result
    
    def _prepare_issues_summary(self, issues: List[Dict]) -> str:
        """
        准备问题摘要
        
        Args:
            issues: 问题列表
            
        Returns:
            str: 问题摘要
        """
        summary = "PowerAutomation MCP测试中发现以下问题：\n\n"
        
        for i, issue in enumerate(issues, 1):
            summary += f"{i}. {issue['description']}\n"
            
            # 添加问题来源
            if "source" in issue:
                summary += f"   来源: {issue['source']}\n"
            
            # 添加问题状态
            if "status" in issue:
                summary += f"   状态: {issue['status']}\n"
            
            summary += "\n"
        
        # 添加环境信息
        summary += "环境信息：\n"
        summary += f"- 仓库路径: {self.repo_path}\n"
        summary += f"- 时间戳: {datetime.now().isoformat()}\n"
        summary += f"- 错误计数: {self._get_error_count()}\n"
        
        return summary
    
    def _get_error_count(self) -> int:
        """
        获取当前错误计数
        
        Returns:
            int: 错误计数
        """
        with open(self.error_counter_file, "r") as f:
            counter_data = json.load(f)
        
        return counter_data["error_count"]
    
    def _generate_automation_script(self, issues_summary: str) -> str:
        """
        生成自动化脚本
        
        Args:
            issues_summary: 问题摘要
            
        Returns:
            str: 脚本路径
        """
        # 生成脚本文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_filename = f"manus_im_submit_{timestamp}.py"
        script_path = os.path.join(self.automation_tools_dir, script_filename)
        
        # 生成脚本内容
        script_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Manus.im问题提交自动化脚本
生成时间: {datetime.now().isoformat()}
\"\"\"

import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='{os.path.join(self.automation_tools_dir, f"manus_im_submit_{timestamp}.log")}',
    filemode='w'
)
logger = logging.getLogger("ManusImSubmit")

# 问题摘要
ISSUES_SUMMARY = \"\"\"
{issues_summary}
\"\"\"

def main():
    \"\"\"主函数\"\"\"
    logger.info("开始执行Manus.im问题提交自动化脚本")
    
    try:
        # 初始化WebDriver
        logger.info("初始化WebDriver")
        driver = initialize_webdriver()
        
        # 打开Manus.im平台
        logger.info("打开Manus.im平台")
        driver.get("{self.manus_im_url}")
        
        # 等待页面加载
        logger.info("等待页面加载")
        time.sleep(5)
        
        # 定位消息输入框
        logger.info("定位消息输入框")
        message_input = locate_message_input(driver)
        
        # 输入问题摘要
        logger.info("输入问题摘要")
        input_issues_summary(message_input, ISSUES_SUMMARY)
        
        # 发送消息
        logger.info("发送消息")
        send_message(message_input)
        
        # 等待响应
        logger.info("等待响应")
        time.sleep(10)
        
        # 记录结果
        logger.info("记录结果")
        result = {{
            "status": "success",
            "message": "成功将问题提交给Manus.im平台",
            "timestamp": datetime.now().isoformat()
        }}
        
        # 保存结果
        save_result(result)
        
        # 关闭WebDriver
        logger.info("关闭WebDriver")
        driver.quit()
        
        return result
    
    except Exception as e:
        logger.error(f"执行过程中发生错误: {{e}}")
        
        result = {{
            "status": "error",
            "message": f"执行过程中发生错误: {{e}}",
            "timestamp": datetime.now().isoformat()
        }}
        
        # 保存结果
        save_result(result)
        
        return result

def initialize_webdriver():
    \"\"\"初始化WebDriver\"\"\"
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    
    return webdriver.Chrome(options=options)

def locate_message_input(driver):
    \"\"\"定位消息输入框\"\"\"
    try:
        # 等待消息输入框出现
        message_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[contenteditable='true']"))
        )
        return message_input
    except TimeoutException:
        logger.error("无法找到消息输入框")
        raise

def input_issues_summary(message_input, issues_summary):
    \"\"\"输入问题摘要\"\"\"
    # 清空输入框
    message_input.clear()
    
    # 输入问题摘要
    message_input.send_keys(issues_summary)
    
    # 等待输入完成
    time.sleep(2)

def send_message(message_input):
    \"\"\"发送消息\"\"\"
    # 按下Ctrl+Enter发送消息
    message_input.send_keys(Keys.CONTROL + Keys.RETURN)

def save_result(result):
    \"\"\"保存结果\"\"\"
    result_path = Path('{os.path.join(self.automation_tools_dir, f"manus_im_submit_{timestamp}_result.json")}')
    
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
"""
        
        # 保存脚本
        with open(script_path, "w") as f:
            f.write(script_content)
        
        # 设置执行权限
        os.chmod(script_path, 0o755)
        
        return script_path
    
    def _execute_automation_script(self, script_path: str) -> Dict:
        """
        执行自动化脚本
        
        Args:
            script_path: 脚本路径
            
        Returns:
            Dict: 执行结果
        """
        self.recorder.record_thought(f"执行自动化脚本: {script_path}")
        
        try:
            # 检查是否已安装所需依赖
            self._ensure_dependencies()
            
            # 执行脚本
            process = subprocess.Popen(
                ["python3", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待脚本执行完成
            stdout, stderr = process.communicate()
            
            # 检查执行结果
            if process.returncode != 0:
                error_msg = stderr.decode("utf-8")
                self.recorder.record_thought(f"脚本执行失败: {error_msg}")
                
                # 尝试使用备用方法
                return self._fallback_submit_to_manus_im(script_path)
            
            # 读取结果文件
            result_path = script_path.replace(".py", "_result.json")
            if os.path.exists(result_path):
                with open(result_path, "r") as f:
                    result = json.load(f)
            else:
                result = {
                    "status": "success",
                    "message": "脚本执行成功，但未找到结果文件",
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
        
        except Exception as e:
            self.recorder.record_thought(f"执行自动化脚本时发生错误: {e}")
            
            # 尝试使用备用方法
            return self._fallback_submit_to_manus_im(script_path)
    
    def _ensure_dependencies(self) -> None:
        """
        确保已安装所需依赖
        """
        try:
            # 检查是否已安装selenium
            import importlib.util
            if importlib.util.find_spec("selenium") is None:
                self.recorder.record_thought("安装selenium依赖")
                subprocess.check_call(["pip", "install", "selenium"])
            
            # 检查是否已安装webdriver_manager
            if importlib.util.find_spec("webdriver_manager") is None:
                self.recorder.record_thought("安装webdriver_manager依赖")
                subprocess.check_call(["pip", "install", "webdriver_manager"])
        
        except Exception as e:
            self.recorder.record_thought(f"安装依赖时发生错误: {e}")
    
    def _fallback_submit_to_manus_im(self, script_path: str) -> Dict:
        """
        备用方法：使用浏览器直接打开Manus.im平台
        
        Args:
            script_path: 脚本路径
            
        Returns:
            Dict: 执行结果
        """
        self.recorder.record_thought("使用备用方法提交问题到Manus.im平台")
        
        try:
            # 读取问题摘要
            with open(script_path, "r") as f:
                script_content = f.read()
            
            issues_summary_match = re.search(r'ISSUES_SUMMARY = """(.*?)"""', script_content, re.DOTALL)
            if issues_summary_match:
                issues_summary = issues_summary_match.group(1).strip()
            else:
                issues_summary = "PowerAutomation MCP测试中发现问题，请协助解决。"
            
            # 将问题摘要保存到临时文件
            temp_file = os.path.join(self.automation_tools_dir, "temp_issues_summary.txt")
            with open(temp_file, "w") as f:
                f.write(issues_summary)
            
            # 使用浏览器打开Manus.im平台
            webbrowser.open(self.manus_im_url)
            
            result = {
                "status": "partial_success",
                "message": f"已使用浏览器打开Manus.im平台，请手动复制问题摘要并提交。问题摘要已保存到: {temp_file}",
                "issues_summary_path": temp_file,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"备用方法执行失败: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
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
        
        return related_files
    
    def _analyze_problem_type(self, issue_description: str) -> str:
        """
        分析问题类型
        
        Args:
            issue_description: 问题描述
            
        Returns:
            str: 问题类型
        """
        # 定义问题类型关键词
        problem_types = {
            "syntax_error": ["SyntaxError", "语法错误", "syntax error"],
            "runtime_error": ["RuntimeError", "运行时错误", "runtime error"],
            "import_error": ["ImportError", "ModuleNotFoundError", "导入错误", "找不到模块"],
            "attribute_error": ["AttributeError", "属性错误", "没有属性"],
            "type_error": ["TypeError", "类型错误", "类型不匹配"],
            "value_error": ["ValueError", "值错误", "无效的值"],
            "index_error": ["IndexError", "索引错误", "索引超出范围"],
            "key_error": ["KeyError", "键错误", "找不到键"],
            "name_error": ["NameError", "名称错误", "未定义的名称"],
            "file_not_found": ["FileNotFoundError", "找不到文件", "file not found"],
            "permission_error": ["PermissionError", "权限错误", "permission denied"],
            "timeout_error": ["TimeoutError", "超时错误", "timeout"],
            "connection_error": ["ConnectionError", "连接错误", "connection failed"],
            "memory_error": ["MemoryError", "内存错误", "内存不足"],
            "assertion_error": ["AssertionError", "断言错误", "assertion failed"],
            "logic_error": ["逻辑错误", "logic error", "逻辑问题"],
            "configuration_error": ["配置错误", "configuration error", "配置问题"],
            "dependency_error": ["依赖错误", "dependency error", "依赖问题"],
            "performance_issue": ["性能问题", "performance issue", "性能下降"],
            "ui_issue": ["UI问题", "界面问题", "UI issue", "interface issue"],
            "compatibility_issue": ["兼容性问题", "compatibility issue", "不兼容"],
            "security_issue": ["安全问题", "security issue", "漏洞"],
            "data_issue": ["数据问题", "data issue", "数据错误"],
            "network_issue": ["网络问题", "network issue", "网络错误"],
            "unknown": []
        }
        
        # 检查问题描述中是否包含各类型的关键词
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
        
        # 从问题描述中提取可能的行号
        line_number_pattern = r"(?:line|行)\s*(\d+)"
        line_number_match = re.search(line_number_pattern, issue_description, re.IGNORECASE)
        target_line = int(line_number_match.group(1)) if line_number_match else None
        
        # 从问题描述中提取可能的错误信息
        error_message_pattern = r"(?:error|错误|exception|异常)[:：]\s*(.+?)(?=\n|$)"
        error_message_match = re.search(error_message_pattern, issue_description, re.IGNORECASE)
        error_message = error_message_match.group(1).strip() if error_message_match else None
        
        # 检查每个相关文件
        for file_path in related_files:
            full_path = os.path.join(self.repo_path, file_path)
            
            if not os.path.exists(full_path):
                continue
            
            with open(full_path, "r") as f:
                lines = f.readlines()
            
            # 如果有目标行号，则提取该行及其上下文
            if target_line is not None and 1 <= target_line <= len(lines):
                start_line = max(1, target_line - 5)
                end_line = min(len(lines), target_line + 5)
                
                snippet = {
                    "file": file_path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "target_line": target_line,
                    "code": "".join(lines[start_line-1:end_line])
                }
                
                code_snippets.append(snippet)
                continue
            
            # 如果有错误信息，则查找包含该错误信息的行
            if error_message is not None:
                for i, line in enumerate(lines, 1):
                    if error_message.lower() in line.lower():
                        start_line = max(1, i - 5)
                        end_line = min(len(lines), i + 5)
                        
                        snippet = {
                            "file": file_path,
                            "start_line": start_line,
                            "end_line": end_line,
                            "target_line": i,
                            "code": "".join(lines[start_line-1:end_line])
                        }
                        
                        code_snippets.append(snippet)
                        break
            
            # 如果没有找到特定行，则提取文件的前20行作为上下文
            if not code_snippets:
                snippet = {
                    "file": file_path,
                    "start_line": 1,
                    "end_line": min(20, len(lines)),
                    "target_line": None,
                    "code": "".join(lines[:min(20, len(lines))])
                }
                
                code_snippets.append(snippet)
        
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
        
        # 根据问题类型生成通用修复建议
        if problem_type == "syntax_error":
            suggestions.append("检查代码语法，确保括号、引号和缩进正确")
            suggestions.append("检查是否有拼写错误或遗漏的冒号")
        elif problem_type == "runtime_error":
            suggestions.append("检查代码逻辑，确保所有可能的执行路径都有正确的处理")
            suggestions.append("添加异常处理，捕获并处理可能的运行时错误")
        elif problem_type == "import_error":
            suggestions.append("检查依赖是否已安装，可能需要运行pip install命令")
            suggestions.append("检查导入路径是否正确，确保模块在Python路径中")
        elif problem_type == "attribute_error":
            suggestions.append("检查对象是否有该属性，可能需要先初始化或检查拼写")
            suggestions.append("确保在使用属性前对象已正确初始化")
        elif problem_type == "type_error":
            suggestions.append("检查变量类型，确保函数参数类型正确")
            suggestions.append("添加类型转换，确保操作的对象类型兼容")
        elif problem_type == "value_error":
            suggestions.append("检查输入值是否在有效范围内")
            suggestions.append("添加输入验证，确保值符合预期格式")
        elif problem_type == "index_error":
            suggestions.append("检查索引是否超出范围，确保在访问前检查列表长度")
            suggestions.append("使用try-except捕获索引错误，提供默认值或错误处理")
        elif problem_type == "key_error":
            suggestions.append("检查字典键是否存在，可以使用get方法提供默认值")
            suggestions.append("在访问键前使用in操作符检查键是否存在")
        elif problem_type == "name_error":
            suggestions.append("检查变量名是否拼写正确，确保在使用前已定义")
            suggestions.append("检查变量作用域，确保在正确的作用域中访问")
        elif problem_type == "file_not_found":
            suggestions.append("检查文件路径是否正确，确保文件存在")
            suggestions.append("使用绝对路径或相对于项目根目录的路径")
        elif problem_type == "permission_error":
            suggestions.append("检查文件或目录权限，确保有足够的访问权限")
            suggestions.append("以管理员权限运行或修改文件权限")
        elif problem_type == "timeout_error":
            suggestions.append("增加超时时间，或者优化操作减少执行时间")
            suggestions.append("添加重试机制，在超时后自动重试")
        elif problem_type == "connection_error":
            suggestions.append("检查网络连接，确保目标服务可访问")
            suggestions.append("添加重试机制，在连接失败后自动重试")
        elif problem_type == "memory_error":
            suggestions.append("优化内存使用，减少内存占用")
            suggestions.append("使用生成器或迭代器处理大数据集")
        elif problem_type == "assertion_error":
            suggestions.append("检查断言条件，确保符合预期")
            suggestions.append("修改代码逻辑，确保满足断言条件")
        elif problem_type == "logic_error":
            suggestions.append("检查业务逻辑，确保符合需求")
            suggestions.append("添加单元测试，验证逻辑正确性")
        elif problem_type == "configuration_error":
            suggestions.append("检查配置文件，确保格式正确且包含所有必要的配置项")
            suggestions.append("提供默认配置，在配置缺失时使用默认值")
        elif problem_type == "dependency_error":
            suggestions.append("检查依赖版本，确保兼容性")
            suggestions.append("更新requirements.txt，确保列出所有必要的依赖")
        elif problem_type == "performance_issue":
            suggestions.append("优化算法，减少时间复杂度")
            suggestions.append("使用缓存或并行处理提高性能")
        elif problem_type == "ui_issue":
            suggestions.append("检查UI元素，确保正确显示和响应")
            suggestions.append("添加响应式设计，适应不同屏幕尺寸")
        elif problem_type == "compatibility_issue":
            suggestions.append("检查兼容性要求，确保支持所有目标平台")
            suggestions.append("添加兼容性检查，在不兼容时提供替代方案")
        elif problem_type == "security_issue":
            suggestions.append("检查安全漏洞，确保数据安全")
            suggestions.append("添加安全措施，如输入验证、加密等")
        elif problem_type == "data_issue":
            suggestions.append("检查数据格式，确保符合预期")
            suggestions.append("添加数据验证，在处理前验证数据有效性")
        elif problem_type == "network_issue":
            suggestions.append("检查网络配置，确保连接正确")
            suggestions.append("添加网络诊断，在连接问题时提供诊断信息")
        else:
            suggestions.append("检查代码逻辑，确保符合预期")
            suggestions.append("添加日志记录，帮助定位问题")
        
        # 根据代码片段生成具体修复建议
        if code_snippets:
            for snippet in code_snippets:
                file_path = snippet["file"]
                code = snippet["code"]
                target_line = snippet["target_line"]
                
                if target_line is not None:
                    suggestions.append(f"检查{file_path}文件第{target_line}行的代码")
                else:
                    suggestions.append(f"检查{file_path}文件的代码")
        
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
        
        # 根据代码片段和修复建议生成代码修改建议
        for snippet in code_snippets:
            file_path = snippet["file"]
            code = snippet["code"]
            target_line = snippet["target_line"]
            
            # 如果有目标行，则生成针对该行的修改建议
            if target_line is not None:
                change = {
                    "file": file_path,
                    "line": target_line,
                    "original": code,
                    "suggestion": "根据修复建议修改此行代码"
                }
                
                code_changes.append(change)
        
        return code_changes
    
    def _generate_test_steps(self, issue_description: str, fix_strategy: Dict) -> List[str]:
        """
        生成测试步骤
        
        Args:
            issue_description: 问题描述
            fix_strategy: 修复策略
            
        Returns:
            List[str]: 测试步骤列表
        """
        test_steps = []
        
        # 生成通用测试步骤
        test_steps.append("准备测试环境，确保所有依赖已安装")
        test_steps.append("运行单元测试，验证修复是否解决问题")
        test_steps.append("运行集成测试，验证修复是否影响其他功能")
        
        # 根据问题描述和修复策略生成具体测试步骤
        if "fix_suggestions" in fix_strategy:
            for suggestion in fix_strategy["fix_suggestions"]:
                if "检查" in suggestion:
                    test_steps.append(f"验证{suggestion.replace('检查', '')}")
        
        return test_steps
    
    def _generate_verification_criteria(self, issue_description: str) -> List[str]:
        """
        生成验证标准
        
        Args:
            issue_description: 问题描述
            
        Returns:
            List[str]: 验证标准列表
        """
        criteria = []
        
        # 生成通用验证标准
        criteria.append("所有测试用例通过，无错误或警告")
        criteria.append("问题不再复现，功能正常工作")
        criteria.append("性能符合预期，无明显延迟或资源占用增加")
        
        return criteria
    
    def _estimate_test_time(self, test_steps: List[str]) -> str:
        """
        估计测试时间
        
        Args:
            test_steps: 测试步骤列表
            
        Returns:
            str: 估计时间
        """
        # 简单估计：每个测试步骤5分钟
        minutes = len(test_steps) * 5
        
        if minutes < 60:
            return f"{minutes}分钟"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            
            if remaining_minutes == 0:
                return f"{hours}小时"
            else:
                return f"{hours}小时{remaining_minutes}分钟"
    
    def _determine_priority(self, issue: Dict) -> str:
        """
        确定问题优先级
        
        Args:
            issue: 问题字典
            
        Returns:
            str: 优先级
        """
        description = issue["description"].lower()
        
        # 高优先级关键词
        high_priority_keywords = ["crash", "崩溃", "critical", "严重", "block", "阻塞", "urgent", "紧急", "security", "安全"]
        
        # 中优先级关键词
        medium_priority_keywords = ["error", "错误", "bug", "缺陷", "issue", "问题", "fail", "失败"]
        
        # 低优先级关键词
        low_priority_keywords = ["minor", "轻微", "cosmetic", "外观", "enhancement", "增强", "suggestion", "建议"]
        
        # 检查优先级
        for keyword in high_priority_keywords:
            if keyword in description:
                return "high"
        
        for keyword in medium_priority_keywords:
            if keyword in description:
                return "medium"
        
        for keyword in low_priority_keywords:
            if keyword in description:
                return "low"
        
        # 默认为中优先级
        return "medium"
    
    def _find_save_point(self, save_point_id: Union[int, str]) -> Optional[Dict]:
        """
        查找保存点
        
        Args:
            save_point_id: 保存点ID或名称
            
        Returns:
            Optional[Dict]: 保存点信息，如果未找到则返回None
        """
        save_points = self.list_save_points()
        
        # 按ID查找
        if isinstance(save_point_id, int) or save_point_id.isdigit():
            save_point_id = int(save_point_id)
            for save_point in save_points:
                if save_point["id"] == save_point_id:
                    return save_point
        
        # 按名称查找
        else:
            for save_point in save_points:
                if save_point["name"] == save_point_id:
                    return save_point
        
        return None
    
    def _copy_code_to_save_point(self, save_point_dir: str) -> None:
        """
        复制当前代码到保存点目录
        
        Args:
            save_point_dir: 保存点目录
        """
        # 复制所有Python文件
        for root, _, files in os.walk(self.repo_path):
            if ".git" in root or "__pycache__" in root or ".save_points" in root:
                continue
                
            for file in files:
                if file.endswith(".py"):
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, self.repo_path)
                    dst_path = os.path.join(save_point_dir, rel_path)
                    
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(src_path, dst_path)
    
    def _copy_code_from_save_point(self, save_point_dir: str) -> None:
        """
        从保存点目录复制代码到当前目录
        
        Args:
            save_point_dir: 保存点目录
        """
        # 复制所有Python文件
        for root, _, files in os.walk(save_point_dir):
            for file in files:
                if file.endswith(".py"):
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, save_point_dir)
                    dst_path = os.path.join(self.repo_path, rel_path)
                    
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(src_path, dst_path)
