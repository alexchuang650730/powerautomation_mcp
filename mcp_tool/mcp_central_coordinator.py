"""
MCP中央协调器模块 - MCPCentralCoordinator

该模块用于协调各个功能模块，实现端到端的自动化流程。
主要功能：
1. 初始化和配置所有功能模块
2. 协调模块间的数据流转
3. 提供统一的API接口
4. 处理异常和错误
5. 管理整体工作流程

作者: Manus AI
日期: 2025-05-28
"""

import os
import json
import time
import datetime
import logging
import threading
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# 导入各功能模块
from .thought_action_recorder import ThoughtActionRecorder
from .release_manager import ReleaseManager
from .test_issue_collector import TestAndIssueCollector
from .manus_problem_solver import ManusProblemSolver

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCPCentralCoordinator")

class MCPCentralCoordinator:
    """
    MCP中央协调器，负责协调所有功能模块，实现端到端的自动化工作流。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化MCP中央协调器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.recorder = ThoughtActionRecorder()
        self.release_manager = ReleaseManager(
            repo_url=self.config.get("repo_url"),
            local_repo_path=self.config.get("repo_path"),
            ssh_key_path=self.config.get("ssh_key_path"),
            check_interval=self.config.get("check_interval", 3600.0)
        )
        self.test_collector = TestAndIssueCollector(
            repo_path=self.config.get("repo_path"),
            screenshot_dir=self.config.get("screenshot_dir")
        )
        self.problem_solver = ManusProblemSolver(
            repo_path=self.config.get("repo_path"),
            enhanced_recorder=self.recorder
        )
        
        # 工作流状态
        self.workflow_status = {
            "status": "idle",
            "current_step": None,
            "steps_completed": [],
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        # 监控线程
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()
        
        logger.info("MCP中央协调器初始化完成")
    
    def run_full_workflow(self, tag_name: Optional[str] = None, skip_upload: bool = False) -> Dict:
        """
        运行完整的工作流程
        
        Args:
            tag_name: 指定的release标签，如果为None则使用最新release
            skip_upload: 是否跳过上传步骤
            
        Returns:
            Dict: 工作流执行结果
        """
        self.recorder.record_thought("开始执行完整工作流")
        
        # 更新工作流状态
        self._update_workflow_status("running", "初始化工作流")
        
        try:
            # 步骤1: 检查并下载release
            self._update_workflow_status("running", "检查并下载release")
            download_result = self._download_release(tag_name)
            
            if download_result["status"] != "success":
                self._update_workflow_status("failed", "下载release失败")
                return {
                    "status": "failed",
                    "message": f"下载release失败: {download_result['message']}",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            # 步骤2: 运行测试并收集问题
            self._update_workflow_status("running", "运行测试并收集问题")
            test_result = self._run_tests()
            
            if test_result["status"] != "success":
                self._update_workflow_status("failed", "测试失败")
                return {
                    "status": "failed",
                    "message": f"测试失败: {test_result['message']}",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            # 步骤3: 分析问题并生成解决方案
            self._update_workflow_status("running", "分析问题并生成解决方案")
            solution_result = self._analyze_and_solve_issues()
            
            if solution_result["status"] != "success":
                self._update_workflow_status("failed", "问题分析失败")
                return {
                    "status": "failed",
                    "message": f"问题分析失败: {solution_result['message']}",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            # 步骤4: 上传更改（如果不跳过）
            if not skip_upload:
                self._update_workflow_status("running", "上传更改")
                upload_result = self._upload_changes()
                
                if upload_result["status"] != "success":
                    self._update_workflow_status("failed", "上传更改失败")
                    return {
                        "status": "failed",
                        "message": f"上传更改失败: {upload_result['message']}",
                        "timestamp": datetime.datetime.now().isoformat()
                    }
            
            # 工作流完成
            self._update_workflow_status("completed", "工作流完成")
            
            result = {
                "status": "success",
                "message": "工作流成功完成",
                "timestamp": datetime.datetime.now().isoformat(),
                "download_result": download_result,
                "test_result": test_result,
                "solution_result": solution_result
            }
            
            if not skip_upload:
                result["upload_result"] = upload_result
            
            self.recorder.record_action(
                "run_full_workflow", 
                {"tag_name": tag_name, "skip_upload": skip_upload},
                result
            )
            
            return result
        
        except Exception as e:
            error_message = f"工作流执行异常: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            self._update_workflow_status("failed", error_message)
            
            result = {
                "status": "failed",
                "message": error_message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "run_full_workflow", 
                {"tag_name": tag_name, "skip_upload": skip_upload},
                result
            )
            
            return result
    
    def monitor_releases(self, callback: Optional[Callable[[Dict], None]] = None) -> None:
        """
        监控releases并在有新release时执行工作流
        
        Args:
            callback: 工作流完成后的回调函数
        """
        self.recorder.record_thought("开始监控releases")
        
        while not self.stop_monitoring.is_set():
            try:
                # 检查是否有新release
                if self.release_manager.is_new_release_available():
                    logger.info("发现新release，开始执行工作流")
                    
                    # 执行工作流
                    result = self.run_full_workflow()
                    
                    # 调用回调函数
                    if callback is not None:
                        callback(result)
                
                # 等待一段时间
                time.sleep(self.config.get("check_interval", 3600.0))
            
            except Exception as e:
                error_message = f"监控releases异常: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_message)
                
                # 短暂等待后继续
                time.sleep(60)
    
    def start_monitoring_in_background(self, callback: Optional[Callable[[Dict], None]] = None) -> None:
        """
        在后台线程中开始监控releases
        
        Args:
            callback: 工作流完成后的回调函数
        """
        if self.monitor_thread is not None and self.monitor_thread.is_alive():
            logger.warning("监控线程已在运行")
            return
        
        # 重置停止标志
        self.stop_monitoring.clear()
        
        # 创建并启动线程
        self.monitor_thread = threading.Thread(
            target=self.monitor_releases,
            args=(callback,),
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("在后台开始监控releases")
    
    def stop_monitoring_in_background(self) -> None:
        """
        停止在后台监控releases
        """
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            logger.warning("监控线程未运行")
            return
        
        # 设置停止标志
        self.stop_monitoring.set()
        
        # 等待线程结束
        self.monitor_thread.join(timeout=10)
        
        logger.info("停止监控releases")
    
    def get_workflow_status(self) -> Dict:
        """
        获取工作流状态
        
        Returns:
            Dict: 工作流状态
        """
        return self.workflow_status
    
    def validate_end_to_end_workflow(self, tag_name: Optional[str] = None) -> Dict:
        """
        验证端到端工作流
        
        Args:
            tag_name: 指定的release标签，如果为None则使用最新release
            
        Returns:
            Dict: 验证结果
        """
        self.recorder.record_thought("开始验证端到端工作流")
        
        try:
            # 步骤1: 检查并下载release
            download_result = self._download_release(tag_name)
            
            if download_result["status"] != "success":
                return {
                    "status": "failed",
                    "message": f"下载release失败: {download_result['message']}",
                    "step": "download",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            # 步骤2: 运行测试并收集问题
            test_result = self._run_tests()
            
            if test_result["status"] != "success":
                return {
                    "status": "failed",
                    "message": f"测试失败: {test_result['message']}",
                    "step": "test",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            # 步骤3: 分析问题并生成解决方案
            solution_result = self._analyze_and_solve_issues()
            
            if solution_result["status"] != "success":
                return {
                    "status": "failed",
                    "message": f"问题分析失败: {solution_result['message']}",
                    "step": "solve",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            # 验证完成
            result = {
                "status": "success",
                "message": "端到端工作流验证成功",
                "timestamp": datetime.datetime.now().isoformat(),
                "download_result": download_result,
                "test_result": test_result,
                "solution_result": solution_result
            }
            
            self.recorder.record_action(
                "validate_end_to_end_workflow", 
                {"tag_name": tag_name},
                result
            )
            
            return result
        
        except Exception as e:
            error_message = f"端到端工作流验证异常: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            result = {
                "status": "failed",
                "message": error_message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "validate_end_to_end_workflow", 
                {"tag_name": tag_name},
                result
            )
            
            return result
    
    def generate_validation_report(self, validation_result: Dict, output_path: Optional[str] = None) -> str:
        """
        生成验证报告
        
        Args:
            validation_result: 验证结果
            output_path: 输出路径，如果为None则使用默认路径
            
        Returns:
            str: 报告文件路径
        """
        # 确定输出路径
        if output_path is None:
            reports_dir = os.path.join(self.config.get("repo_path", os.getcwd()), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(reports_dir, f"validation_report_{timestamp}.md")
        
        # 生成报告内容
        report_content = f"""# 端到端工作流验证报告

## 概述

- **状态**: {validation_result["status"]}
- **时间**: {validation_result["timestamp"]}
- **消息**: {validation_result["message"]}

## 详细结果

"""
        
        # 添加下载结果
        if "download_result" in validation_result:
            download_result = validation_result["download_result"]
            report_content += f"""### 下载Release

- **状态**: {download_result["status"]}
- **消息**: {download_result.get("message", "无")}
- **标签**: {download_result.get("tag", "最新")}
- **时间**: {download_result.get("timestamp", "未知")}

"""
        
        # 添加测试结果
        if "test_result" in validation_result:
            test_result = validation_result["test_result"]
            report_content += f"""### 测试结果

- **状态**: {test_result["status"]}
- **消息**: {test_result.get("message", "无")}
- **测试数**: {test_result.get("tests_count", 0)}
- **通过数**: {test_result.get("passed_count", 0)}
- **失败数**: {test_result.get("failed_count", 0)}
- **时间**: {test_result.get("timestamp", "未知")}

"""
            
            # 添加失败的测试
            if "failed_tests" in test_result and test_result["failed_tests"]:
                report_content += "#### 失败的测试\n\n"
                
                for i, test in enumerate(test_result["failed_tests"]):
                    report_content += f"{i+1}. **{test['name']}**: {test['message']}\n"
                
                report_content += "\n"
        
        # 添加解决方案结果
        if "solution_result" in validation_result:
            solution_result = validation_result["solution_result"]
            report_content += f"""### 问题分析与解决方案

- **状态**: {solution_result["status"]}
- **消息**: {solution_result.get("message", "无")}
- **问题数**: {solution_result.get("issues_count", 0)}
- **解决方案数**: {solution_result.get("solutions_count", 0)}
- **时间**: {solution_result.get("timestamp", "未知")}

"""
            
            # 添加解决方案
            if "solutions" in solution_result and solution_result["solutions"]:
                report_content += "#### 解决方案\n\n"
                
                for i, solution in enumerate(solution_result["solutions"]):
                    issue = solution["issue"]
                    report_content += f"{i+1}. **问题**: {issue['description']}\n"
                    report_content += f"   - **来源**: {issue['source']}\n"
                    report_content += f"   - **状态**: {issue['status']}\n"
                    report_content += f"   - **问题类型**: {solution['problem_location']['problem_type']}\n"
                    report_content += f"   - **优先级**: {solution['fix_strategy']['priority']}\n"
                    
                    # 添加修复建议
                    if "fix_suggestions" in solution["fix_strategy"] and solution["fix_strategy"]["fix_suggestions"]:
                        report_content += "   - **修复建议**:\n"
                        for suggestion in solution["fix_strategy"]["fix_suggestions"]:
                            report_content += f"     - {suggestion}\n"
                    
                    report_content += "\n"
        
        # 添加上传结果
        if "upload_result" in validation_result:
            upload_result = validation_result["upload_result"]
            report_content += f"""### 上传更改

- **状态**: {upload_result["status"]}
- **消息**: {upload_result.get("message", "无")}
- **提交ID**: {upload_result.get("commit_id", "未知")}
- **时间**: {upload_result.get("timestamp", "未知")}

"""
        
        # 添加结论
        report_content += f"""## 结论

端到端工作流验证**{validation_result["status"]}**。

"""
        
        if validation_result["status"] == "success":
            report_content += "所有步骤都成功完成，系统运行正常。\n"
        else:
            report_content += f"验证失败，原因: {validation_result['message']}\n"
        
        # 写入文件
        with open(output_path, "w") as f:
            f.write(report_content)
        
        logger.info(f"验证报告已生成: {output_path}")
        
        return output_path
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
            
        Returns:
            Dict: 配置字典
        """
        # 确定配置文件路径
        if config_path is None:
            config_path = os.environ.get(
                "MCP_CONFIG_PATH",
                os.path.expanduser("~/.powerautomation_mcp/config.json")
            )
        
        # 确保配置目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 如果配置文件不存在，创建默认配置
        if not os.path.exists(config_path):
            default_config = {
                "repo_path": os.path.expanduser("~/powerassistant/powerautomation"),
                "repo_url": "https://github.com/alexchuang650730/powerautomation.git",
                "mcp_repo_url": "https://github.com/alexchuang650730/powerautomation_mcp.git",
                "ssh_key_path": os.path.expanduser("~/.ssh/id_rsa"),
                "github_token": None,
                "check_interval": 3600.0,
                "log_dir": os.path.expanduser("~/powerassistant/powerautomation/logs"),
                "screenshot_dir": os.path.expanduser("~/powerassistant/powerautomation/screenshots"),
                "manus_url": "https://manus.im/",
                "ocr_engine": "tesseract",
                "monitor_regions": {
                    "thought_region": {"x": 100, "y": 100, "width": 400, "height": 300},
                    "action_region": {"x": 100, "y": 400, "width": 400, "height": 300},
                    "taskbar_region": {"x": 0, "y": 0, "width": 100, "height": 600}
                },
                "capture_interval": 2.0
            }
            
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"已创建默认配置文件: {config_path}")
        
        # 加载配置
        with open(config_path, "r") as f:
            config = json.load(f)
        
        logger.info(f"已加载配置文件: {config_path}")
        
        return config
    
    def _update_workflow_status(self, status: str, current_step: Optional[str] = None) -> None:
        """
        更新工作流状态
        
        Args:
            status: 状态（idle, running, completed, failed）
            current_step: 当前步骤
        """
        if current_step is not None and self.workflow_status["current_step"] != current_step:
            if self.workflow_status["current_step"] is not None:
                self.workflow_status["steps_completed"].append(self.workflow_status["current_step"])
            
            self.workflow_status["current_step"] = current_step
        
        self.workflow_status["status"] = status
        self.workflow_status["last_updated"] = datetime.datetime.now().isoformat()
        
        logger.info(f"工作流状态更新: {status}, 当前步骤: {current_step}")
    
    def _download_release(self, tag_name: Optional[str] = None) -> Dict:
        """
        检查并下载release
        
        Args:
            tag_name: 指定的release标签，如果为None则使用最新release
            
        Returns:
            Dict: 下载结果
        """
        self.recorder.record_thought(f"检查并下载release: {tag_name or '最新'}")
        
        try:
            # 检查是否有新release
            if tag_name is None and not self.release_manager.is_new_release_available():
                return {
                    "status": "skipped",
                    "message": "没有新的release",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            # 下载release
            result = self.release_manager.download_release(tag_name)
            
            self.recorder.record_action(
                "download_release", 
                {"tag_name": tag_name},
                result
            )
            
            return result
        
        except Exception as e:
            error_message = f"下载release异常: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            result = {
                "status": "failed",
                "message": error_message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "download_release", 
                {"tag_name": tag_name},
                result
            )
            
            return result
    
    def _run_tests(self) -> Dict:
        """
        运行测试并收集问题
        
        Returns:
            Dict: 测试结果
        """
        self.recorder.record_thought("运行测试并收集问题")
        
        try:
            # 运行测试
            result = self.test_collector.run_tests()
            
            # 更新README
            self.test_collector.update_readme_with_test_results()
            
            self.recorder.record_action(
                "run_tests", 
                {},
                result
            )
            
            return result
        
        except Exception as e:
            error_message = f"运行测试异常: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            result = {
                "status": "failed",
                "message": error_message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "run_tests", 
                {},
                result
            )
            
            return result
    
    def _analyze_and_solve_issues(self) -> Dict:
        """
        分析问题并生成解决方案
        
        Returns:
            Dict: 分析结果
        """
        self.recorder.record_thought("分析问题并生成解决方案")
        
        try:
            # 分析问题并生成解决方案
            solutions = self.problem_solver.analyze_issues_and_generate_solutions()
            
            # 保存解决方案
            if solutions["status"] != "no_issues":
                self.problem_solver.save_solutions_to_file(solutions)
            
            self.recorder.record_action(
                "analyze_and_solve_issues", 
                {},
                solutions
            )
            
            return solutions
        
        except Exception as e:
            error_message = f"分析问题异常: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            result = {
                "status": "failed",
                "message": error_message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "analyze_and_solve_issues", 
                {},
                result
            )
            
            return result
    
    def _upload_changes(self) -> Dict:
        """
        上传更改
        
        Returns:
            Dict: 上传结果
        """
        self.recorder.record_thought("上传更改")
        
        try:
            # 获取本地仓库状态
            repo_status = self.release_manager.get_local_repo_status()
            
            # 如果没有更改，跳过上传
            if not repo_status["has_changes"]:
                return {
                    "status": "skipped",
                    "message": "没有需要上传的更改",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            # 上传更改
            commit_message = "自动更新 - 测试结果和解决方案"
            result = self.release_manager.upload_to_github(commit_message)
            
            self.recorder.record_action(
                "upload_changes", 
                {"commit_message": commit_message},
                result
            )
            
            return result
        
        except Exception as e:
            error_message = f"上传更改异常: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            result = {
                "status": "failed",
                "message": error_message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "upload_changes", 
                {"commit_message": "自动更新 - 测试结果和解决方案"},
                result
            )
            
            return result
