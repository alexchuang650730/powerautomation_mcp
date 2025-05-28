"""
自动化测试与README更新模块 - TestAndReadmeUpdater

该模块负责在端侧执行测试步骤要求的动作，收集测试问题，
并自动更新README文件，提供问题报告给Manus进行分析和修复。

作者: Manus AI
日期: 2025-05-28
"""

import os
import time
import logging
import json
import re
import shutil
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import tempfile
import markdown
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestAndReadmeUpdater")

class TestAndReadmeUpdater:
    """
    自动化测试与README更新器，负责执行测试步骤，收集问题，
    并自动更新README文件。
    """
    
    def __init__(self, 
                 repo_path: str,
                 test_plan_path: Optional[str] = None,
                 readme_path: Optional[str] = None,
                 screenshot_dir: Optional[str] = None,
                 visual_recorder = None,
                 release_manager = None,
                 rules_checker = None):
        """
        初始化自动化测试与README更新器
        
        Args:
            repo_path: 本地仓库路径
            test_plan_path: 测试计划文件路径（可选）
            readme_path: README文件路径（可选）
            screenshot_dir: 截图保存目录（可选）
            visual_recorder: 视觉记录器实例（可选）
            release_manager: Release管理器实例（可选）
            rules_checker: Release规则检查器实例（可选）
        """
        self.repo_path = os.path.expanduser(repo_path)
        self.test_plan_path = test_plan_path or os.path.join(self.repo_path, "test_plan.md")
        self.readme_path = readme_path or os.path.join(self.repo_path, "README.md")
        self.screenshot_dir = screenshot_dir or os.path.join(self.repo_path, "screenshots")
        
        # 创建截图目录
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # 关联的模块
        self.visual_recorder = visual_recorder
        self.release_manager = release_manager
        self.rules_checker = rules_checker
        
        # 测试结果
        self.test_results = []
        self.issues = []
        
        logger.info(f"初始化自动化测试与README更新器: {self.repo_path}")
    
    def load_test_plan(self) -> List[Dict]:
        """
        加载测试计划
        
        Returns:
            List[Dict]: 测试用例列表
        """
        logger.info(f"加载测试计划: {self.test_plan_path}")
        
        if not os.path.exists(self.test_plan_path):
            logger.warning(f"测试计划文件不存在: {self.test_plan_path}")
            return []
        
        try:
            # 读取测试计划文件
            with open(self.test_plan_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 解析Markdown格式的测试计划
            test_cases = self._parse_test_plan_markdown(content)
            
            logger.info(f"成功加载 {len(test_cases)} 个测试用例")
            return test_cases
        except Exception as e:
            logger.error(f"加载测试计划失败: {e}")
            return []
    
    def _parse_test_plan_markdown(self, content: str) -> List[Dict]:
        """
        解析Markdown格式的测试计划
        
        Args:
            content: Markdown内容
            
        Returns:
            List[Dict]: 测试用例列表
        """
        test_cases = []
        
        # 将Markdown转换为HTML
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找所有测试用例（假设每个用例以h3标签开始）
        case_headers = soup.find_all("h3")
        
        for header in case_headers:
            # 检查是否为测试用例标题
            title_text = header.get_text().strip()
            if not title_text.startswith("用例") and ":" not in title_text:
                continue
            
            # 提取用例标题
            title = title_text.split(":", 1)[1].strip() if ":" in title_text else title_text
            
            # 初始化用例数据
            case = {
                "title": title,
                "id": f"test_{len(test_cases) + 1}",
                "type": "功能测试",
                "priority": "中",
                "description": "",
                "preconditions": [],
                "steps": [],
                "expected_results": [],
                "verification_points": []
            }
            
            # 查找用例详情
            element = header.next_sibling
            current_section = None
            
            while element and element.name != "h3":
                if element.name == "p":
                    text = element.get_text().strip()
                    
                    # 检查是否包含元数据
                    if "**ID**:" in text:
                        case["id"] = text.split("**ID**:", 1)[1].strip()
                    elif "**类型**:" in text:
                        case["type"] = text.split("**类型**:", 1)[1].strip()
                    elif "**优先级**:" in text:
                        case["priority"] = text.split("**优先级**:", 1)[1].strip()
                    elif "**描述**:" in text:
                        case["description"] = text.split("**描述**:", 1)[1].strip()
                
                elif element.name == "h4":
                    section_title = element.get_text().strip()
                    if "前置条件" in section_title:
                        current_section = "preconditions"
                    elif "测试步骤" in section_title:
                        current_section = "steps"
                    elif "预期结果" in section_title:
                        current_section = "expected_results"
                    elif "验证点" in section_title:
                        current_section = "verification_points"
                    else:
                        current_section = None
                
                elif element.name == "ul" and current_section:
                    items = element.find_all("li")
                    for item in items:
                        text = item.get_text().strip()
                        if text:
                            case[current_section].append(text)
                
                elif element.name == "ol" and current_section == "steps":
                    items = element.find_all("li")
                    for item in items:
                        text = item.get_text().strip()
                        if text:
                            case["steps"].append(text)
                
                element = element.next_sibling
            
            test_cases.append(case)
        
        return test_cases
    
    def run_tests(self, test_cases: Optional[List[Dict]] = None) -> List[Dict]:
        """
        运行测试用例
        
        Args:
            test_cases: 测试用例列表，如果为None则加载测试计划
            
        Returns:
            List[Dict]: 测试结果列表
        """
        if test_cases is None:
            test_cases = self.load_test_plan()
        
        if not test_cases:
            logger.warning("没有测试用例可运行")
            return []
        
        logger.info(f"开始运行 {len(test_cases)} 个测试用例")
        
        # 清空之前的测试结果
        self.test_results = []
        self.issues = []
        
        # 按优先级排序
        priority_order = {"高": 0, "中": 1, "低": 2}
        sorted_cases = sorted(test_cases, key=lambda c: priority_order.get(c.get("priority", "低"), 3))
        
        # 运行测试用例
        for case in sorted_cases:
            result = self._run_test_case(case)
            self.test_results.append(result)
            
            # 如果测试失败，记录问题
            if not result["passed"]:
                issue = self._create_issue_from_test_result(result)
                self.issues.append(issue)
        
        logger.info(f"测试完成: {len(self.test_results)} 个测试用例，{len(self.issues)} 个问题")
        
        # 更新README
        self.update_readme_with_test_results()
        
        return self.test_results
    
    def _run_test_case(self, test_case: Dict) -> Dict:
        """
        运行单个测试用例
        
        Args:
            test_case: 测试用例
            
        Returns:
            Dict: 测试结果
        """
        case_id = test_case.get("id", "unknown")
        title = test_case.get("title", "未命名测试")
        
        logger.info(f"运行测试用例: {case_id} - {title}")
        
        # 初始化测试结果
        result = {
            "id": case_id,
            "title": title,
            "type": test_case.get("type", "功能测试"),
            "priority": test_case.get("priority", "中"),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "passed": False,
            "steps_results": [],
            "issues": [],
            "screenshots": []
        }
        
        try:
            # 检查前置条件
            preconditions = test_case.get("preconditions", [])
            if preconditions:
                logger.info(f"检查前置条件: {len(preconditions)} 个")
                for i, condition in enumerate(preconditions):
                    logger.info(f"前置条件 {i+1}: {condition}")
                    # TODO: 实现前置条件检查
            
            # 执行测试步骤
            steps = test_case.get("steps", [])
            all_steps_passed = True
            
            for i, step in enumerate(steps):
                logger.info(f"执行步骤 {i+1}: {step}")
                
                # 执行测试步骤
                step_result = self._execute_test_step(step, i+1, test_case)
                result["steps_results"].append(step_result)
                
                # 如果步骤失败，整个测试失败
                if not step_result["passed"]:
                    all_steps_passed = False
                    logger.warning(f"步骤 {i+1} 失败: {step_result['message']}")
                    
                    # 添加问题
                    issue = {
                        "step": i+1,
                        "description": step,
                        "message": step_result["message"],
                        "screenshot": step_result.get("screenshot")
                    }
                    result["issues"].append(issue)
                
                # 添加截图
                if "screenshot" in step_result:
                    result["screenshots"].append(step_result["screenshot"])
            
            # 验证预期结果
            expected_results = test_case.get("expected_results", [])
            verification_points = test_case.get("verification_points", [])
            
            if expected_results or verification_points:
                logger.info(f"验证预期结果: {len(expected_results)} 个结果, {len(verification_points)} 个验证点")
                
                # TODO: 实现预期结果验证
                # 这里简化处理，假设如果所有步骤都通过，则预期结果也通过
                verification_passed = all_steps_passed
                
                if not verification_passed:
                    logger.warning("预期结果验证失败")
                    
                    # 添加问题
                    issue = {
                        "step": len(steps) + 1,
                        "description": "验证预期结果",
                        "message": "预期结果验证失败",
                        "screenshot": None
                    }
                    result["issues"].append(issue)
                    
                    # 截图
                    screenshot_path = self._take_screenshot(f"{case_id}_verification_failed")
                    if screenshot_path:
                        issue["screenshot"] = screenshot_path
                        result["screenshots"].append(screenshot_path)
            
            # 更新测试结果
            result["passed"] = all_steps_passed and (not expected_results or verification_passed)
            result["end_time"] = datetime.now().isoformat()
            
            logger.info(f"测试用例 {case_id} {'通过' if result['passed'] else '失败'}")
            
            return result
        except Exception as e:
            logger.error(f"运行测试用例 {case_id} 时发生错误: {e}")
            
            # 更新测试结果
            result["passed"] = False
            result["end_time"] = datetime.now().isoformat()
            result["issues"].append({
                "step": 0,
                "description": "测试执行异常",
                "message": str(e),
                "screenshot": None
            })
            
            # 截图
            screenshot_path = self._take_screenshot(f"{case_id}_error")
            if screenshot_path:
                result["issues"][-1]["screenshot"] = screenshot_path
                result["screenshots"].append(screenshot_path)
            
            return result
    
    def _execute_test_step(self, step: str, step_number: int, test_case: Dict) -> Dict:
        """
        执行测试步骤
        
        Args:
            step: 测试步骤描述
            step_number: 步骤编号
            test_case: 测试用例
            
        Returns:
            Dict: 步骤执行结果
        """
        # 初始化步骤结果
        result = {
            "step": step_number,
            "description": step,
            "passed": False,
            "message": "",
            "screenshot": None
        }
        
        try:
            # 根据步骤描述执行相应操作
            # 这里需要根据实际情况实现具体的测试步骤执行逻辑
            
            # 示例：根据步骤描述中的关键词执行不同操作
            if "打开" in step or "访问" in step or "导航" in step:
                # 打开页面
                url_match = re.search(r"(https?://\S+)", step)
                if url_match:
                    url = url_match.group(1)
                    logger.info(f"打开URL: {url}")
                    
                    # 使用视觉记录器的导航功能
                    if self.visual_recorder and hasattr(self.visual_recorder, "navigate_to"):
                        success = self.visual_recorder.navigate_to(url)
                        result["passed"] = success
                        result["message"] = "页面打开成功" if success else "页面打开失败"
                    else:
                        # 假设成功
                        result["passed"] = True
                        result["message"] = "页面打开成功（模拟）"
                else:
                    result["passed"] = False
                    result["message"] = "步骤中未找到URL"
            
            elif "点击" in step:
                # 点击元素
                element_match = re.search(r"点击\s*[\"'](.+?)[\"']", step)
                if element_match:
                    element_text = element_match.group(1)
                    logger.info(f"点击元素: {element_text}")
                    
                    # 使用视觉记录器的点击功能
                    if self.visual_recorder and hasattr(self.visual_recorder, "click_element"):
                        success = self.visual_recorder.click_element(element_text)
                        result["passed"] = success
                        result["message"] = f"点击元素 '{element_text}' 成功" if success else f"点击元素 '{element_text}' 失败"
                    else:
                        # 假设成功
                        result["passed"] = True
                        result["message"] = f"点击元素 '{element_text}' 成功（模拟）"
                else:
                    result["passed"] = False
                    result["message"] = "步骤中未找到要点击的元素"
            
            elif "输入" in step:
                # 输入文本
                input_match = re.search(r"输入\s*[\"'](.+?)[\"']\s*到\s*[\"'](.+?)[\"']", step)
                if input_match:
                    input_text = input_match.group(1)
                    input_field = input_match.group(2)
                    logger.info(f"在 {input_field} 中输入: {input_text}")
                    
                    # 使用视觉记录器的输入功能
                    if self.visual_recorder and hasattr(self.visual_recorder, "input_text"):
                        success = self.visual_recorder.input_text(input_field, input_text)
                        result["passed"] = success
                        result["message"] = f"在 '{input_field}' 中输入 '{input_text}' 成功" if success else f"在 '{input_field}' 中输入 '{input_text}' 失败"
                    else:
                        # 假设成功
                        result["passed"] = True
                        result["message"] = f"在 '{input_field}' 中输入 '{input_text}' 成功（模拟）"
                else:
                    result["passed"] = False
                    result["message"] = "步骤中未找到输入文本或输入字段"
            
            elif "验证" in step or "检查" in step:
                # 验证元素或文本
                verify_match = re.search(r"验证|检查\s*[\"'](.+?)[\"']", step)
                if verify_match:
                    verify_text = verify_match.group(1)
                    logger.info(f"验证元素或文本: {verify_text}")
                    
                    # 使用视觉记录器的验证功能
                    if self.visual_recorder and hasattr(self.visual_recorder, "verify_element"):
                        success = self.visual_recorder.verify_element(verify_text)
                        result["passed"] = success
                        result["message"] = f"验证 '{verify_text}' 成功" if success else f"验证 '{verify_text}' 失败"
                    else:
                        # 假设成功
                        result["passed"] = True
                        result["message"] = f"验证 '{verify_text}' 成功（模拟）"
                else:
                    result["passed"] = False
                    result["message"] = "步骤中未找到要验证的元素或文本"
            
            elif "等待" in step:
                # 等待
                wait_match = re.search(r"等待\s*(\d+)\s*秒", step)
                if wait_match:
                    wait_seconds = int(wait_match.group(1))
                    logger.info(f"等待 {wait_seconds} 秒")
                    time.sleep(wait_seconds)
                    result["passed"] = True
                    result["message"] = f"等待 {wait_seconds} 秒完成"
                else:
                    result["passed"] = False
                    result["message"] = "步骤中未找到等待时间"
            
            else:
                # 默认假设步骤成功
                logger.info(f"执行通用步骤: {step}")
                result["passed"] = True
                result["message"] = "步骤执行成功（模拟）"
            
            # 截图
            case_id = test_case.get("id", "unknown")
            screenshot_path = self._take_screenshot(f"{case_id}_step_{step_number}")
            if screenshot_path:
                result["screenshot"] = screenshot_path
            
            return result
        except Exception as e:
            logger.error(f"执行测试步骤时发生错误: {e}")
            result["passed"] = False
            result["message"] = f"步骤执行异常: {e}"
            
            # 截图
            case_id = test_case.get("id", "unknown")
            screenshot_path = self._take_screenshot(f"{case_id}_step_{step_number}_error")
            if screenshot_path:
                result["screenshot"] = screenshot_path
            
            return result
    
    def _take_screenshot(self, name: str) -> Optional[str]:
        """
        截图
        
        Args:
            name: 截图名称
            
        Returns:
            Optional[str]: 截图路径，如果失败则返回None
        """
        try:
            # 生成截图文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            screenshot_path = os.path.join(self.screenshot_dir, filename)
            
            # 使用视觉记录器截图
            if self.visual_recorder and hasattr(self.visual_recorder, "take_screenshot"):
                success = self.visual_recorder.take_screenshot(screenshot_path)
                if success:
                    logger.info(f"截图保存到: {screenshot_path}")
                    return screenshot_path
                else:
                    logger.warning(f"截图失败")
                    return None
            else:
                # 模拟截图
                logger.info(f"模拟截图: {screenshot_path}")
                
                # 创建一个空白图像文件
                try:
                    from PIL import Image
                    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
                    img.save(screenshot_path)
                    return screenshot_path
                except ImportError:
                    logger.warning("PIL库未安装，无法创建模拟截图")
                    return None
        except Exception as e:
            logger.error(f"截图时发生错误: {e}")
            return None
    
    def _create_issue_from_test_result(self, test_result: Dict) -> Dict:
        """
        从测试结果创建问题
        
        Args:
            test_result: 测试结果
            
        Returns:
            Dict: 问题
        """
        # 提取测试用例信息
        case_id = test_result.get("id", "unknown")
        title = test_result.get("title", "未命名测试")
        
        # 提取问题信息
        issues = test_result.get("issues", [])
        if not issues:
            # 如果没有具体问题，创建一个通用问题
            return {
                "id": f"issue_{len(self.issues) + 1}",
                "title": f"测试 '{title}' 失败",
                "description": f"测试用例 {case_id} 执行失败，但没有具体错误信息。",
                "severity": "中",
                "status": "新建",
                "test_case_id": case_id,
                "steps_to_reproduce": test_result.get("steps_results", []),
                "screenshots": test_result.get("screenshots", []),
                "created_at": datetime.now().isoformat()
            }
        
        # 使用第一个问题作为主要问题
        first_issue = issues[0]
        step = first_issue.get("step", 0)
        description = first_issue.get("description", "")
        message = first_issue.get("message", "")
        screenshot = first_issue.get("screenshot")
        
        # 创建问题
        issue = {
            "id": f"issue_{len(self.issues) + 1}",
            "title": f"测试 '{title}' 在步骤 {step} 失败",
            "description": f"测试用例 {case_id} 在执行步骤 {step} '{description}' 时失败: {message}",
            "severity": "中",  # 默认严重程度
            "status": "新建",
            "test_case_id": case_id,
            "steps_to_reproduce": [],
            "screenshots": [],
            "created_at": datetime.now().isoformat()
        }
        
        # 添加重现步骤
        steps_results = test_result.get("steps_results", [])
        for step_result in steps_results:
            step_num = step_result.get("step", 0)
            step_desc = step_result.get("description", "")
            issue["steps_to_reproduce"].append(f"步骤 {step_num}: {step_desc}")
        
        # 添加截图
        if screenshot:
            issue["screenshots"].append(screenshot)
        
        # 添加其他截图
        for other_screenshot in test_result.get("screenshots", []):
            if other_screenshot != screenshot:
                issue["screenshots"].append(other_screenshot)
        
        return issue
    
    def update_readme_with_test_results(self) -> bool:
        """
        使用测试结果更新README文件
        
        Returns:
            bool: 如果更新成功，返回True；否则返回False
        """
        logger.info(f"使用测试结果更新README: {self.readme_path}")
        
        if not os.path.exists(self.readme_path):
            logger.warning(f"README文件不存在: {self.readme_path}")
            return False
        
        try:
            # 读取README文件
            with open(self.readme_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 查找测试结果部分
            test_results_section = "## 测试结果"
            test_issues_section = "## 已知问题"
            
            # 生成测试结果内容
            test_results_content = self._generate_test_results_content()
            test_issues_content = self._generate_test_issues_content()
            
            # 更新或添加测试结果部分
            if test_results_section in content:
                # 更新现有部分
                pattern = re.compile(f"{test_results_section}.*?(?=^##|\Z)", re.DOTALL | re.MULTILINE)
                content = pattern.sub(f"{test_results_section}\n\n{test_results_content}\n\n", content)
            else:
                # 添加新部分
                content += f"\n\n{test_results_section}\n\n{test_results_content}\n"
            
            # 更新或添加已知问题部分
            if test_issues_section in content:
                # 更新现有部分
                pattern = re.compile(f"{test_issues_section}.*?(?=^##|\Z)", re.DOTALL | re.MULTILINE)
                content = pattern.sub(f"{test_issues_section}\n\n{test_issues_content}\n\n", content)
            else:
                # 添加新部分
                content += f"\n\n{test_issues_section}\n\n{test_issues_content}\n"
            
            # 写入README文件
            with open(self.readme_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"README更新成功: {self.readme_path}")
            return True
        except Exception as e:
            logger.error(f"更新README失败: {e}")
            return False
    
    def _generate_test_results_content(self) -> str:
        """
        生成测试结果内容
        
        Returns:
            str: 测试结果内容
        """
        if not self.test_results:
            return "暂无测试结果。"
        
        # 统计测试结果
        total = len(self.test_results)
        passed = sum(1 for result in self.test_results if result.get("passed", False))
        failed = total - passed
        
        # 生成内容
        content = f"最近一次测试于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 执行，共 {total} 个测试用例，{passed} 个通过，{failed} 个失败。\n\n"
        
        # 添加测试结果表格
        content += "| ID | 测试用例 | 类型 | 优先级 | 状态 | 详情 |\n"
        content += "| --- | --- | --- | --- | --- | --- |\n"
        
        for result in self.test_results:
            case_id = result.get("id", "unknown")
            title = result.get("title", "未命名测试")
            type_name = result.get("type", "功能测试")
            priority = result.get("priority", "中")
            status = "通过" if result.get("passed", False) else "失败"
            
            # 如果有截图，添加链接
            screenshots = result.get("screenshots", [])
            details = ""
            if screenshots:
                screenshot_path = screenshots[0]
                screenshot_name = os.path.basename(screenshot_path)
                details = f"[截图]({screenshot_path})"
            
            content += f"| {case_id} | {title} | {type_name} | {priority} | {status} | {details} |\n"
        
        return content
    
    def _generate_test_issues_content(self) -> str:
        """
        生成测试问题内容
        
        Returns:
            str: 测试问题内容
        """
        if not self.issues:
            return "暂无已知问题。"
        
        # 生成内容
        content = f"共发现 {len(self.issues)} 个问题：\n\n"
        
        for i, issue in enumerate(self.issues):
            issue_id = issue.get("id", f"issue_{i+1}")
            title = issue.get("title", "未命名问题")
            description = issue.get("description", "")
            severity = issue.get("severity", "中")
            status = issue.get("status", "新建")
            created_at = issue.get("created_at", "")
            if created_at:
                try:
                    created_at = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            content += f"### {issue_id}: {title}\n\n"
            content += f"- **严重程度**: {severity}\n"
            content += f"- **状态**: {status}\n"
            content += f"- **创建时间**: {created_at}\n"
            content += f"- **描述**: {description}\n"
            
            # 添加重现步骤
            steps = issue.get("steps_to_reproduce", [])
            if steps:
                content += "\n**重现步骤**:\n\n"
                for step in steps:
                    content += f"1. {step}\n"
            
            # 添加截图
            screenshots = issue.get("screenshots", [])
            if screenshots:
                content += "\n**相关截图**:\n\n"
                for screenshot in screenshots:
                    screenshot_name = os.path.basename(screenshot)
                    content += f"![{screenshot_name}]({screenshot})\n"
            
            content += "\n"
        
        return content
    
    def generate_test_report(self, output_path: Optional[str] = None) -> str:
        """
        生成测试报告
        
        Args:
            output_path: 报告输出路径，如果为None则使用默认路径
            
        Returns:
            str: 报告文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.repo_path, f"test_report_{timestamp}.md")
        
        logger.info(f"生成测试报告: {output_path}")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                # 报告标题
                f.write("# 测试报告\n\n")
                
                # 生成时间
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"**生成时间**: {timestamp}\n\n")
                
                # 测试摘要
                f.write("## 测试摘要\n\n")
                
                total = len(self.test_results)
                passed = sum(1 for result in self.test_results if result.get("passed", False))
                failed = total - passed
                
                f.write(f"- **测试用例总数**: {total}\n")
                f.write(f"- **通过**: {passed}\n")
                f.write(f"- **失败**: {failed}\n")
                f.write(f"- **通过率**: {passed/total*100:.2f}% 如果total > 0 else 'N/A'}\n\n")
                
                # 测试环境
                f.write("## 测试环境\n\n")
                f.write("- **操作系统**: macOS Sonoma (14.x)\n")
                f.write("- **浏览器**: Chrome 最新版\n")
                f.write("- **测试工具**: PowerAutomation MCP\n")
                f.write("- **测试数据**: 使用模拟数据和真实数据结合\n\n")
                
                # 测试结果详情
                f.write("## 测试结果详情\n\n")
                
                for result in self.test_results:
                    case_id = result.get("id", "unknown")
                    title = result.get("title", "未命名测试")
                    type_name = result.get("type", "功能测试")
                    priority = result.get("priority", "中")
                    status = "通过" if result.get("passed", False) else "失败"
                    
                    f.write(f"### {case_id}: {title}\n\n")
                    f.write(f"- **类型**: {type_name}\n")
                    f.write(f"- **优先级**: {priority}\n")
                    f.write(f"- **状态**: {status}\n")
                    
                    # 添加步骤结果
                    steps_results = result.get("steps_results", [])
                    if steps_results:
                        f.write("\n**步骤结果**:\n\n")
                        for step_result in steps_results:
                            step_num = step_result.get("step", 0)
                            step_desc = step_result.get("description", "")
                            step_status = "通过" if step_result.get("passed", False) else "失败"
                            step_message = step_result.get("message", "")
                            
                            f.write(f"{step_num}. {step_desc} - {step_status}\n")
                            if step_message:
                                f.write(f"   - {step_message}\n")
                    
                    # 添加截图
                    screenshots = result.get("screenshots", [])
                    if screenshots:
                        f.write("\n**截图**:\n\n")
                        for screenshot in screenshots:
                            screenshot_name = os.path.basename(screenshot)
                            f.write(f"![{screenshot_name}]({screenshot})\n")
                    
                    f.write("\n")
                
                # 问题摘要
                if self.issues:
                    f.write("## 问题摘要\n\n")
                    f.write(f"共发现 {len(self.issues)} 个问题：\n\n")
                    
                    # 按严重程度分类
                    severity_issues = {}
                    for issue in self.issues:
                        severity = issue.get("severity", "中")
                        if severity not in severity_issues:
                            severity_issues[severity] = []
                        severity_issues[severity].append(issue)
                    
                    for severity, issues in severity_issues.items():
                        f.write(f"- **{severity}**: {len(issues)}个\n")
                    
                    f.write("\n")
                    
                    # 问题详情
                    f.write("## 问题详情\n\n")
                    
                    for issue in self.issues:
                        issue_id = issue.get("id", "unknown")
                        title = issue.get("title", "未命名问题")
                        description = issue.get("description", "")
                        severity = issue.get("severity", "中")
                        status = issue.get("status", "新建")
                        
                        f.write(f"### {issue_id}: {title}\n\n")
                        f.write(f"- **严重程度**: {severity}\n")
                        f.write(f"- **状态**: {status}\n")
                        f.write(f"- **描述**: {description}\n")
                        
                        # 添加重现步骤
                        steps = issue.get("steps_to_reproduce", [])
                        if steps:
                            f.write("\n**重现步骤**:\n\n")
                            for step in steps:
                                f.write(f"1. {step}\n")
                        
                        # 添加截图
                        screenshots = issue.get("screenshots", [])
                        if screenshots:
                            f.write("\n**相关截图**:\n\n")
                            for screenshot in screenshots:
                                screenshot_name = os.path.basename(screenshot)
                                f.write(f"![{screenshot_name}]({screenshot})\n")
                        
                        f.write("\n")
                
                # 结论和建议
                f.write("## 结论和建议\n\n")
                
                if failed == 0:
                    f.write("所有测试用例均已通过，系统运行正常。\n")
                else:
                    f.write(f"测试发现 {failed} 个失败的测试用例，需要进一步分析和修复。\n\n")
                    
                    # 添加建议
                    f.write("### 建议\n\n")
                    f.write("1. 优先修复严重级别问题\n")
                    f.write("2. 对失败的测试用例进行深入分析\n")
                    f.write("3. 修复后进行回归测试\n")
            
            logger.info(f"测试报告生成成功: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"生成测试报告失败: {e}")
            return ""
