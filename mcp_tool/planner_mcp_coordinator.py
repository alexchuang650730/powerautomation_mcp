"""
增强版MCP中央协调器 - 支持自然语言任务指令

该模块扩展了原有的MCPCentralCoordinator，添加了自然语言任务指令解析和执行能力，
使其能够作为一个真正的planner接受高级任务指令。

作者: Manus AI
日期: 2025-05-28
"""

import os
import time
import logging
import json
import threading
import re
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
import traceback

# 导入原有的MCPCentralCoordinator
from mcp_tool.mcp_central_coordinator import MCPCentralCoordinator as BaseMCPCentralCoordinator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PlannerMCPCentralCoordinator")

class PlannerMCPCentralCoordinator(BaseMCPCentralCoordinator):
    """
    增强版MCP中央协调器，支持自然语言任务指令，作为一个planner接受高级任务指令。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化增强版MCP中央协调器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 调用父类初始化方法
        super().__init__(config_path)
        
        # 任务类型映射
        self.task_type_patterns = {
            "record_thoughts_actions": [
                r"自动记录.*思考.*动作",
                r"记录.*思考.*过程",
                r"监控.*思考.*动作",
                r"捕获.*思考.*过程",
                r"ocr.*思考.*动作"
            ],
            "handle_release": [
                r"release.*下载.*代码",
                r"下载.*代码.*上传",
                r"release.*上传.*github",
                r"同步.*代码.*github"
            ],
            "test_and_fix": [
                r"执行测试.*更新.*readme",
                r"测试.*问题定位",
                r"测试.*修复.*测试",
                r"问题定位.*修复.*测试"
            ]
        }
        
        logger.info("增强版MCP中央协调器初始化完成，支持自然语言任务指令")
    
    def execute_task(self, task_description: str) -> Dict:
        """
        执行高级任务指令
        
        Args:
            task_description: 任务描述，如"自动记录Manus所有步骤思考过程及动作"
                
        Returns:
            Dict: 任务执行结果
        """
        logger.info(f"收到任务指令: {task_description}")
        
        # 解析任务描述
        task_type = self._parse_task_type(task_description)
        
        if not task_type:
            logger.warning(f"未识别的任务类型: {task_description}")
            return {
                "status": "error",
                "message": f"未识别的任务类型: {task_description}",
                "suggestion": "请尝试使用以下任务描述之一:\n"
                              "- 自动记录Manus所有步骤思考过程及动作\n"
                              "- 在release时自动下载代码到Mac端侧并上传GitHub\n"
                              "- 在端侧执行测试并更新README，驱动Manus进行问题定位、修复和测试"
            }
        
        logger.info(f"识别到任务类型: {task_type}")
        
        # 根据任务类型执行相应操作
        try:
            if task_type == "record_thoughts_actions":
                return self._execute_record_thoughts_actions()
            elif task_type == "handle_release":
                return self._execute_handle_release()
            elif task_type == "test_and_fix":
                return self._execute_test_and_fix()
            else:
                return {
                    "status": "error",
                    "message": f"未实现的任务类型: {task_type}"
                }
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "message": f"执行任务失败: {e}",
                "error_details": traceback.format_exc()
            }
    
    def _parse_task_type(self, task_description: str) -> Optional[str]:
        """
        解析任务描述，识别任务类型
        
        Args:
            task_description: 任务描述
            
        Returns:
            Optional[str]: 任务类型，如果无法识别则返回None
        """
        # 转换为小写以便匹配
        task_lower = task_description.lower()
        
        # 尝试匹配每种任务类型的模式
        for task_type, patterns in self.task_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, task_lower):
                    return task_type
        
        return None
    
    def _execute_record_thoughts_actions(self) -> Dict:
        """
        执行"自动记录Manus所有步骤思考过程及动作"任务
        
        Returns:
            Dict: 任务执行结果
        """
        logger.info("开始执行: 自动记录Manus所有步骤思考过程及动作")
        
        result = {
            "task_type": "record_thoughts_actions",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "steps": {},
            "error": None
        }
        
        try:
            # 步骤1: 检查Manus界面并导航
            self._run_step("check_and_navigate", self._check_and_navigate_to_manus)
            result["steps"]["check_and_navigate"] = "completed"
            
            # 步骤2: 启动视觉记录器
            if hasattr(self, "enhanced_recorder") and self.enhanced_recorder:
                # 如果视觉记录器已经在运行，则停止它
                if hasattr(self.enhanced_recorder, "visual_recorder") and self.enhanced_recorder.visual_recorder:
                    if self.enhanced_recorder.visual_recorder.is_monitoring():
                        self.enhanced_recorder.visual_recorder.stop_monitoring()
                        logger.info("已停止现有的视觉记录器")
                
                # 启动视觉记录器
                if hasattr(self.enhanced_recorder, "visual_recorder") and self.enhanced_recorder.visual_recorder:
                    self.enhanced_recorder.visual_recorder.start_monitoring()
                    logger.info("已启动视觉记录器")
                    result["steps"]["start_visual_recorder"] = "completed"
                else:
                    logger.warning("视觉记录器未初始化")
                    result["steps"]["start_visual_recorder"] = "skipped"
            else:
                logger.warning("增强型记录器未初始化")
                result["steps"]["start_visual_recorder"] = "skipped"
            
            # 步骤3: 分析任务栏
            # 这一步由视觉记录器自动处理
            result["steps"]["analyze_taskbar"] = "running"
            
            # 更新任务状态
            result["status"] = "completed"
            result["end_time"] = datetime.now().isoformat()
            result["message"] = "已成功启动Manus思考与动作记录"
            
            logger.info("成功执行: 自动记录Manus所有步骤思考过程及动作")
            return result
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            logger.error(traceback.format_exc())
            
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
            
            return result
    
    def _execute_handle_release(self) -> Dict:
        """
        执行"在release时自动下载代码到Mac端侧并上传GitHub"任务
        
        Returns:
            Dict: 任务执行结果
        """
        logger.info("开始执行: 在release时自动下载代码到Mac端侧并上传GitHub")
        
        result = {
            "task_type": "handle_release",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "steps": {},
            "error": None
        }
        
        try:
            # 步骤1: 检查是否有新release
            check_result = self._run_step("check_release", lambda: self._check_and_download_release(None))
            result["steps"]["check_release"] = check_result.get("status", "unknown")
            
            # 如果没有新release，则返回
            if check_result.get("status") == "skipped":
                result["status"] = "completed"
                result["end_time"] = datetime.now().isoformat()
                result["message"] = "没有新的release可用"
                
                logger.info("完成执行: 在release时自动下载代码到Mac端侧并上传GitHub (无新release)")
                return result
            
            # 步骤2: 验证Release规则
            verify_result = self._run_step("verify_release_rules", self._verify_release_rules)
            result["steps"]["verify_release_rules"] = verify_result.get("status", "unknown")
            
            # 步骤3: 上传更改（如果有）
            upload_result = self._run_step("upload_changes", self._upload_changes)
            result["steps"]["upload_changes"] = upload_result.get("status", "unknown")
            
            # 更新任务状态
            result["status"] = "completed"
            result["end_time"] = datetime.now().isoformat()
            result["message"] = f"已处理release: {check_result.get('tag_name', 'unknown')}"
            
            logger.info("成功执行: 在release时自动下载代码到Mac端侧并上传GitHub")
            return result
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            logger.error(traceback.format_exc())
            
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
            
            return result
    
    def _execute_test_and_fix(self) -> Dict:
        """
        执行"在端侧执行测试并更新README，驱动Manus进行问题定位、修复和测试"任务
        
        Returns:
            Dict: 任务执行结果
        """
        logger.info("开始执行: 在端侧执行测试并更新README，驱动Manus进行问题定位、修复和测试")
        
        result = {
            "task_type": "test_and_fix",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "steps": {},
            "issues_found": 0,
            "issues_analyzed": 0,
            "error": None
        }
        
        try:
            # 步骤1: 运行测试并更新README
            test_result = self._run_step("run_tests_and_update_readme", self._run_tests_and_update_readme)
            result["steps"]["run_tests_and_update_readme"] = test_result.get("status", "unknown")
            result["issues_found"] = test_result.get("issues_found", 0)
            
            # 步骤2: 分析问题并生成解决方案
            if result["issues_found"] > 0:
                analyze_result = self._run_step("analyze_issues_and_generate_solutions", self._analyze_issues_and_generate_solutions)
                result["steps"]["analyze_issues_and_generate_solutions"] = analyze_result.get("status", "unknown")
                result["issues_analyzed"] = analyze_result.get("issues_analyzed", 0)
                result["solutions_generated"] = analyze_result.get("solutions_generated", 0)
                result["report_path"] = analyze_result.get("report_path", "")
            else:
                result["steps"]["analyze_issues_and_generate_solutions"] = "skipped"
                result["message"] = "没有发现问题，跳过分析"
            
            # 更新任务状态
            result["status"] = "completed"
            result["end_time"] = datetime.now().isoformat()
            
            if result["issues_found"] > 0:
                result["message"] = f"发现 {result['issues_found']} 个问题，已生成 {result.get('solutions_generated', 0)} 个解决方案"
            else:
                result["message"] = "测试通过，没有发现问题"
            
            logger.info("成功执行: 在端侧执行测试并更新README，驱动Manus进行问题定位、修复和测试")
            return result
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            logger.error(traceback.format_exc())
            
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
            
            return result
    
    def start_task_monitoring(self, interval: float = 3600.0, callback: Optional[Callable] = None):
        """
        启动任务监控，定期执行所有任务
        
        Args:
            interval: 监控间隔（秒）
            callback: 回调函数，接收任务结果作为参数
        """
        logger.info(f"启动任务监控，间隔: {interval}秒")
        
        def monitor_loop():
            while True:
                try:
                    # 执行"自动记录Manus所有步骤思考过程及动作"任务
                    record_result = self.execute_task("自动记录Manus所有步骤思考过程及动作")
                    if callback:
                        callback(record_result)
                    
                    # 执行"在release时自动下载代码到Mac端侧并上传GitHub"任务
                    release_result = self.execute_task("在release时自动下载代码到Mac端侧并上传GitHub")
                    if callback:
                        callback(release_result)
                    
                    # 执行"在端侧执行测试并更新README，驱动Manus进行问题定位、修复和测试"任务
                    test_result = self.execute_task("在端侧执行测试并更新README，驱动Manus进行问题定位、修复和测试")
                    if callback:
                        callback(test_result)
                    
                    # 等待下一次监控
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"任务监控循环出错: {e}")
                    logger.error(traceback.format_exc())
                    time.sleep(60)  # 出错后等待一分钟再重试
        
        # 启动监控线程
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        
        return thread
    
    def start_task_monitoring_in_background(self, interval: float = 3600.0, callback: Optional[Callable] = None):
        """
        在后台线程中启动任务监控
        
        Args:
            interval: 监控间隔（秒）
            callback: 回调函数，接收任务结果作为参数
        """
        logger.info(f"在后台线程中启动任务监控，间隔: {interval}秒")
        
        thread = threading.Thread(
            target=self.start_task_monitoring,
            args=(interval, callback),
            daemon=True
        )
        thread.start()
        
        return thread
