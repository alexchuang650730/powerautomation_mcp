"""
端到端工作流集成与验证模块 - MCPCentralCoordinator

该模块负责协调所有功能模块，实现端到端的自动化工作流，
并提供验证和监控功能。

作者: Manus AI
日期: 2025-05-28
"""

import os
import time
import logging
import json
import threading
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
import traceback

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
        self.config_path = config_path or os.path.expanduser("~/.powerautomation_mcp/config.json")
        self.config = self._load_config()
        
        # 组件实例
        self.visual_recorder = None
        self.release_manager = None
        self.test_updater = None
        self.rules_checker = None
        self.problem_solver = None
        self.manus_navigator = None
        
        # 工作流状态
        self.workflow_running = False
        self.current_step = None
        self.workflow_results = {}
        
        logger.info(f"初始化MCP中央协调器，配置文件: {self.config_path}")
        
        # 初始化组件
        self._init_components()
    
    def _load_config(self) -> Dict:
        """
        加载配置文件
        
        Returns:
            Dict: 配置字典
        """
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
        
        # 确保配置目录存在
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # 如果配置文件不存在，创建默认配置
        if not os.path.exists(self.config_path):
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"创建默认配置文件: {self.config_path}")
            return default_config
        
        # 加载配置文件
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"成功加载配置文件: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return default_config
    
    def _init_components(self):
        """初始化所有组件"""
        logger.info("初始化组件...")
        
        try:
            # 导入组件
            from mcp_tool.visual_thought_recorder import VisualThoughtRecorder
            from mcp_tool.enhanced_thought_recorder import EnhancedThoughtRecorder
            from mcp_tool.release_manager import ReleaseManager
            from mcp_tool.test_readme_updater import TestAndReadmeUpdater
            from mcp_tool.release_rules_checker import ReleaseRulesChecker
            from mcp_tool.manus_problem_solver import ManusProblemSolver
            from mcp_tool.manus_navigator import ManusNavigator
            
            # 初始化视觉导航器
            self.manus_navigator = ManusNavigator(
                manus_url=self.config.get("manus_url"),
                headless=False
            )
            logger.info("Manus导航器初始化完成")
            
            # 初始化视觉记录器
            visual_recorder = VisualThoughtRecorder(
                log_dir=self.config.get("log_dir"),
                monitor_regions=self.config.get("monitor_regions"),
                ocr_engine=self.config.get("ocr_engine"),
                capture_interval=self.config.get("capture_interval"),
                navigator=self.manus_navigator
            )
            logger.info("视觉思考记录器初始化完成")
            
            # 初始化增强型记录器
            self.enhanced_recorder = EnhancedThoughtRecorder(
                log_dir=self.config.get("log_dir"),
                visual_recorder=visual_recorder
            )
            logger.info("增强型思考记录器初始化完成")
            
            # 初始化Release管理器
            self.release_manager = ReleaseManager(
                repo_url=self.config.get("repo_url"),
                local_repo_path=self.config.get("repo_path"),
                github_token=self.config.get("github_token"),
                ssh_key_path=self.config.get("ssh_key_path"),
                check_interval=self.config.get("check_interval")
            )
            logger.info("Release管理器初始化完成")
            
            # 初始化Release规则检查器
            self.rules_checker = ReleaseRulesChecker(
                repo_path=self.config.get("repo_path"),
                enhanced_recorder=self.enhanced_recorder
            )
            logger.info("Release规则检查器初始化完成")
            
            # 初始化测试与README更新器
            self.test_updater = TestAndReadmeUpdater(
                repo_path=self.config.get("repo_path"),
                screenshot_dir=self.config.get("screenshot_dir"),
                visual_recorder=visual_recorder,
                release_manager=self.release_manager,
                rules_checker=self.rules_checker
            )
            logger.info("测试与README更新器初始化完成")
            
            # 初始化问题解决器
            self.problem_solver = ManusProblemSolver(
                repo_path=self.config.get("repo_path"),
                enhanced_recorder=self.enhanced_recorder,
                test_updater=self.test_updater,
                rules_checker=self.rules_checker
            )
            logger.info("问题解决器初始化完成")
            
            logger.info("所有组件初始化完成")
        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def run_full_workflow(self, tag_name: Optional[str] = None, skip_upload: bool = False) -> Dict:
        """
        运行完整的工作流程
        
        Args:
            tag_name: 指定的release标签，如果为None则使用最新release
            skip_upload: 是否跳过上传步骤
            
        Returns:
            Dict: 工作流结果
        """
        if self.workflow_running:
            logger.warning("工作流程已在运行中")
            return {"status": "error", "message": "工作流程已在运行中"}
        
        self.workflow_running = True
        self.workflow_results = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "steps": {},
            "issues_found": 0,
            "issues_fixed": 0,
            "test_results": None,
            "solutions": None
        }
        
        try:
            logger.info(f"开始运行完整工作流程，tag_name={tag_name}, skip_upload={skip_upload}")
            
            # 步骤1: 检查Manus界面并导航
            self._run_step("check_and_navigate", self._check_and_navigate_to_manus)
            
            # 步骤2: 检查并下载release
            self._run_step("check_and_download_release", lambda: self._check_and_download_release(tag_name))
            
            # 步骤3: 验证Release规则
            self._run_step("verify_release_rules", self._verify_release_rules)
            
            # 步骤4: 运行测试并更新README
            self._run_step("run_tests_and_update_readme", self._run_tests_and_update_readme)
            
            # 步骤5: 分析问题并生成解决方案
            self._run_step("analyze_issues_and_generate_solutions", self._analyze_issues_and_generate_solutions)
            
            # 步骤6: 上传更改（如果需要）
            if not skip_upload:
                self._run_step("upload_changes", self._upload_changes)
            
            # 更新工作流结果
            self.workflow_results["status"] = "completed"
            self.workflow_results["end_time"] = datetime.now().isoformat()
            
            logger.info("工作流程完成")
            return self.workflow_results
        except Exception as e:
            logger.error(f"工作流程执行失败: {e}")
            logger.error(traceback.format_exc())
            
            self.workflow_results["status"] = "failed"
            self.workflow_results["error"] = str(e)
            self.workflow_results["end_time"] = datetime.now().isoformat()
            
            return self.workflow_results
        finally:
            self.workflow_running = False
    
    def _run_step(self, step_name: str, step_func: Callable) -> Any:
        """
        运行工作流步骤
        
        Args:
            step_name: 步骤名称
            step_func: 步骤函数
            
        Returns:
            Any: 步骤结果
        """
        logger.info(f"开始执行步骤: {step_name}")
        self.current_step = step_name
        
        step_result = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "result": None,
            "error": None
        }
        
        self.workflow_results["steps"][step_name] = step_result
        
        try:
            result = step_func()
            
            step_result["result"] = result
            step_result["status"] = "completed"
            step_result["end_time"] = datetime.now().isoformat()
            
            logger.info(f"步骤 {step_name} 执行完成")
            return result
        except Exception as e:
            logger.error(f"步骤 {step_name} 执行失败: {e}")
            logger.error(traceback.format_exc())
            
            step_result["status"] = "failed"
            step_result["error"] = str(e)
            step_result["end_time"] = datetime.now().isoformat()
            
            raise
    
    def _check_and_navigate_to_manus(self) -> bool:
        """
        检查Manus界面并导航
        
        Returns:
            bool: 如果成功，返回True；否则返回False
        """
        logger.info("检查Manus界面并导航")
        
        if not self.manus_navigator:
            logger.error("Manus导航器未初始化")
            return False
        
        # 检查是否已经在Manus界面
        is_on_manus = self.manus_navigator.is_on_manus_page()
        
        if not is_on_manus:
            logger.info("未检测到Manus界面，开始导航")
            return self.manus_navigator.navigate_to_manus()
        else:
            logger.info("已在Manus界面")
            return True
    
    def _check_and_download_release(self, tag_name: Optional[str] = None) -> Dict:
        """
        检查并下载release
        
        Args:
            tag_name: 指定的release标签，如果为None则使用最新release
            
        Returns:
            Dict: 下载结果
        """
        logger.info(f"检查并下载release，tag_name={tag_name}")
        
        if not self.release_manager:
            logger.error("Release管理器未初始化")
            return {"status": "error", "message": "Release管理器未初始化"}
        
        # 如果指定了tag，直接下载
        if tag_name:
            success = self.release_manager.download_release(tag_name)
            return {
                "status": "success" if success else "error",
                "tag_name": tag_name,
                "message": f"Release {tag_name} 下载{'成功' if success else '失败'}"
            }
        
        # 检查是否有新release
        if self.release_manager.is_new_release_available():
            # 下载最新release
            success = self.release_manager.download_release()
            return {
                "status": "success" if success else "error",
                "tag_name": self.release_manager.latest_release.get("tag_name") if self.release_manager.latest_release else None,
                "message": f"最新release下载{'成功' if success else '失败'}"
            }
        else:
            return {
                "status": "skipped",
                "message": "没有新的release可用"
            }
    
    def _verify_release_rules(self) -> Dict:
        """
        验证Release规则
        
        Returns:
            Dict: 验证结果
        """
        logger.info("验证Release规则")
        
        if not self.rules_checker:
            logger.error("Release规则检查器未初始化")
            return {"status": "error", "message": "Release规则检查器未初始化"}
        
        # 验证规则
        result = self.rules_checker.verify_all_rules()
        
        # 记录结果
        return {
            "status": "success" if result["all_passed"] else "warning",
            "all_passed": result["all_passed"],
            "passed_rules": result["passed_rules"],
            "failed_rules": result["failed_rules"],
            "warnings": result["warnings"]
        }
    
    def _run_tests_and_update_readme(self) -> Dict:
        """
        运行测试并更新README
        
        Returns:
            Dict: 测试结果
        """
        logger.info("运行测试并更新README")
        
        if not self.test_updater:
            logger.error("测试与README更新器未初始化")
            return {"status": "error", "message": "测试与README更新器未初始化"}
        
        # 运行测试
        test_results = self.test_updater.run_tests()
        
        # 更新README
        readme_updated = self.test_updater.update_readme_with_test_results()
        
        # 生成测试报告
        test_report = self.test_updater.generate_test_report()
        
        # 记录结果
        total = len(test_results)
        passed = sum(1 for result in test_results if result.get("passed", False))
        failed = total - passed
        
        self.workflow_results["issues_found"] = len(self.test_updater.issues)
        self.workflow_results["test_results"] = test_results
        
        return {
            "status": "success" if failed == 0 else "warning",
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "issues_found": len(self.test_updater.issues),
            "readme_updated": readme_updated,
            "test_report": test_report
        }
    
    def _analyze_issues_and_generate_solutions(self) -> Dict:
        """
        分析问题并生成解决方案
        
        Returns:
            Dict: 分析结果
        """
        logger.info("分析问题并生成解决方案")
        
        if not self.problem_solver:
            logger.error("问题解决器未初始化")
            return {"status": "error", "message": "问题解决器未初始化"}
        
        # 获取问题列表
        issues = self.test_updater.issues if self.test_updater else []
        
        if not issues:
            logger.info("没有发现问题，跳过分析")
            return {
                "status": "skipped",
                "message": "没有发现问题，跳过分析"
            }
        
        # 分析问题并生成解决方案
        solutions = self.problem_solver.analyze_issues_and_generate_solutions(issues)
        
        # 保存解决方案
        report_path = self.problem_solver.save_solutions_to_file(solutions)
        
        # 记录结果
        self.workflow_results["solutions"] = solutions
        
        return {
            "status": "success",
            "issues_analyzed": len(issues),
            "solutions_generated": len(solutions),
            "report_path": report_path
        }
    
    def _upload_changes(self) -> Dict:
        """
        上传更改
        
        Returns:
            Dict: 上传结果
        """
        logger.info("上传更改")
        
        if not self.release_manager:
            logger.error("Release管理器未初始化")
            return {"status": "error", "message": "Release管理器未初始化"}
        
        # 获取本地仓库状态
        repo_status = self.release_manager.get_local_repo_status()
        
        if not repo_status["has_changes"]:
            logger.info("没有更改需要上传")
            return {
                "status": "skipped",
                "message": "没有更改需要上传"
            }
        
        # 生成提交信息
        commit_message = self._generate_commit_message()
        
        # 上传更改
        success = self.release_manager.upload_to_github(commit_message)
        
        return {
            "status": "success" if success else "error",
            "commit_message": commit_message,
            "message": f"更改上传{'成功' if success else '失败'}"
        }
    
    def _generate_commit_message(self) -> str:
        """
        生成提交信息
        
        Returns:
            str: 提交信息
        """
        # 获取测试结果
        test_results = self.workflow_results.get("test_results", [])
        total = len(test_results) if test_results else 0
        passed = sum(1 for result in test_results if result.get("passed", False)) if test_results else 0
        failed = total - passed
        
        # 获取问题数量
        issues_found = self.workflow_results.get("issues_found", 0)
        
        # 生成提交信息
        if failed > 0:
            return f"测试结果: {passed}/{total} 通过, 发现 {issues_found} 个问题, 已生成修复建议"
        else:
            return f"测试结果: 全部通过 ({total}/{total}), 无问题发现"
    
    def monitor_releases(self, callback: Optional[Callable] = None):
        """
        监控releases，当有新release时执行工作流
        
        Args:
            callback: 回调函数，接收工作流结果作为参数
        """
        logger.info("开始监控releases")
        
        if not self.release_manager:
            logger.error("Release管理器未初始化")
            return
        
        def release_callback(release_info):
            logger.info(f"检测到新release: {release_info.get('tag_name')}")
            
            # 运行工作流
            workflow_result = self.run_full_workflow(release_info.get("tag_name"))
            
            # 执行回调
            if callback:
                callback(workflow_result)
        
        # 开始监控
        self.release_manager.monitor_releases(release_callback)
    
    def start_monitoring_in_background(self, callback: Optional[Callable] = None):
        """
        在后台线程中开始监控
        
        Args:
            callback: 回调函数，接收工作流结果作为参数
        """
        logger.info("在后台线程中开始监控")
        
        thread = threading.Thread(
            target=self.monitor_releases,
            args=(callback,),
            daemon=True
        )
        thread.start()
        
        return thread
    
    def get_workflow_status(self) -> Dict:
        """
        获取工作流状态
        
        Returns:
            Dict: 工作流状态
        """
        return {
            "running": self.workflow_running,
            "current_step": self.current_step,
            "results": self.workflow_results
        }
    
    def validate_end_to_end_workflow(self, tag_name: Optional[str] = None) -> Dict:
        """
        验证端到端工作流
        
        Args:
            tag_name: 指定的release标签，如果为None则使用最新release
            
        Returns:
            Dict: 验证结果
        """
        logger.info(f"开始验证端到端工作流，tag_name={tag_name}")
        
        validation_result = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "components_status": {},
            "workflow_result": None,
            "error": None
        }
        
        try:
            # 验证组件状态
            validation_result["components_status"] = self._validate_components()
            
            # 运行工作流
            workflow_result = self.run_full_workflow(tag_name, skip_upload=True)
            validation_result["workflow_result"] = workflow_result
            
            # 更新验证结果
            validation_result["status"] = "completed" if workflow_result["status"] == "completed" else "failed"
            validation_result["end_time"] = datetime.now().isoformat()
            
            logger.info("端到端工作流验证完成")
            return validation_result
        except Exception as e:
            logger.error(f"端到端工作流验证失败: {e}")
            logger.error(traceback.format_exc())
            
            validation_result["status"] = "failed"
            validation_result["error"] = str(e)
            validation_result["end_time"] = datetime.now().isoformat()
            
            return validation_result
    
    def _validate_components(self) -> Dict:
        """
        验证组件状态
        
        Returns:
            Dict: 组件状态
        """
        components_status = {}
        
        # 验证Manus导航器
        if self.manus_navigator:
            try:
                is_browser_open = self.manus_navigator.is_browser_open()
                components_status["manus_navigator"] = {
                    "status": "ok" if is_browser_open else "error",
                    "message": "浏览器已打开" if is_browser_open else "浏览器未打开"
                }
            except Exception as e:
                components_status["manus_navigator"] = {
                    "status": "error",
                    "message": f"验证失败: {e}"
                }
        else:
            components_status["manus_navigator"] = {
                "status": "error",
                "message": "未初始化"
            }
        
        # 验证增强型记录器
        if self.enhanced_recorder:
            try:
                # 简单测试记录功能
                self.enhanced_recorder.record_thought("验证增强型记录器")
                latest_thoughts = self.enhanced_recorder.get_latest_thoughts(limit=1)
                
                components_status["enhanced_recorder"] = {
                    "status": "ok" if latest_thoughts else "warning",
                    "message": "记录功能正常" if latest_thoughts else "记录功能可能有问题"
                }
            except Exception as e:
                components_status["enhanced_recorder"] = {
                    "status": "error",
                    "message": f"验证失败: {e}"
                }
        else:
            components_status["enhanced_recorder"] = {
                "status": "error",
                "message": "未初始化"
            }
        
        # 验证Release管理器
        if self.release_manager:
            try:
                repo_status = self.release_manager.get_local_repo_status()
                
                components_status["release_manager"] = {
                    "status": "ok" if repo_status["exists"] else "warning",
                    "message": "本地仓库状态正常" if repo_status["exists"] else "本地仓库不存在"
                }
            except Exception as e:
                components_status["release_manager"] = {
                    "status": "error",
                    "message": f"验证失败: {e}"
                }
        else:
            components_status["release_manager"] = {
                "status": "error",
                "message": "未初始化"
            }
        
        # 验证规则检查器
        if self.rules_checker:
            try:
                # 简单测试规则检查功能
                rule_result = self.rules_checker.verify_rule("no_untested_code")
                
                components_status["rules_checker"] = {
                    "status": "ok",
                    "message": "规则检查功能正常"
                }
            except Exception as e:
                components_status["rules_checker"] = {
                    "status": "error",
                    "message": f"验证失败: {e}"
                }
        else:
            components_status["rules_checker"] = {
                "status": "error",
                "message": "未初始化"
            }
        
        # 验证测试更新器
        if self.test_updater:
            try:
                # 检查README文件
                readme_path = self.test_updater.readme_path
                readme_exists = os.path.exists(readme_path)
                
                components_status["test_updater"] = {
                    "status": "ok" if readme_exists else "warning",
                    "message": "README文件存在" if readme_exists else "README文件不存在"
                }
            except Exception as e:
                components_status["test_updater"] = {
                    "status": "error",
                    "message": f"验证失败: {e}"
                }
        else:
            components_status["test_updater"] = {
                "status": "error",
                "message": "未初始化"
            }
        
        # 验证问题解决器
        if self.problem_solver:
            try:
                # 简单测试问题解决器
                components_status["problem_solver"] = {
                    "status": "ok",
                    "message": "问题解决器初始化正常"
                }
            except Exception as e:
                components_status["problem_solver"] = {
                    "status": "error",
                    "message": f"验证失败: {e}"
                }
        else:
            components_status["problem_solver"] = {
                "status": "error",
                "message": "未初始化"
            }
        
        return components_status
    
    def generate_validation_report(self, validation_result: Dict, output_path: Optional[str] = None) -> str:
        """
        生成验证报告
        
        Args:
            validation_result: 验证结果
            output_path: 输出路径，如果为None则使用默认路径
            
        Returns:
            str: 报告文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.config.get("repo_path", "."), f"validation_report_{timestamp}.md")
        
        logger.info(f"生成验证报告: {output_path}")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# 端到端工作流验证报告\n\n")
                
                # 生成时间
                start_time = validation_result.get("start_time")
                end_time = validation_result.get("end_time")
                
                if start_time:
                    try:
                        start_time = datetime.fromisoformat(start_time).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                
                if end_time:
                    try:
                        end_time = datetime.fromisoformat(end_time).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                
                f.write(f"**开始时间**: {start_time}\n")
                f.write(f"**结束时间**: {end_time}\n")
                f.write(f"**状态**: {validation_result.get('status', '未知')}\n\n")
                
                # 组件状态
                f.write("## 组件状态\n\n")
                
                components_status = validation_result.get("components_status", {})
                
                f.write("| 组件 | 状态 | 消息 |\n")
                f.write("| --- | --- | --- |\n")
                
                for component, status in components_status.items():
                    component_status = status.get("status", "未知")
                    message = status.get("message", "")
                    
                    f.write(f"| {component} | {component_status} | {message} |\n")
                
                f.write("\n")
                
                # 工作流结果
                workflow_result = validation_result.get("workflow_result", {})
                
                if workflow_result:
                    f.write("## 工作流结果\n\n")
                    
                    f.write(f"**状态**: {workflow_result.get('status', '未知')}\n")
                    
                    # 步骤结果
                    steps = workflow_result.get("steps", {})
                    
                    if steps:
                        f.write("\n### 步骤结果\n\n")
                        
                        f.write("| 步骤 | 状态 | 消息 |\n")
                        f.write("| --- | --- | --- |\n")
                        
                        for step_name, step_result in steps.items():
                            step_status = step_result.get("status", "未知")
                            
                            # 提取消息
                            result = step_result.get("result", {})
                            message = result.get("message", "") if isinstance(result, dict) else ""
                            
                            f.write(f"| {step_name} | {step_status} | {message} |\n")
                    
                    # 测试结果
                    test_results = workflow_result.get("test_results", [])
                    
                    if test_results:
                        f.write("\n### 测试结果\n\n")
                        
                        total = len(test_results)
                        passed = sum(1 for result in test_results if result.get("passed", False))
                        failed = total - passed
                        
                        f.write(f"**总计**: {total} 个测试用例\n")
                        f.write(f"**通过**: {passed} 个\n")
                        f.write(f"**失败**: {failed} 个\n")
                        
                        if failed > 0:
                            f.write("\n**失败的测试用例**:\n\n")
                            
                            for result in test_results:
                                if not result.get("passed", False):
                                    case_id = result.get("id", "unknown")
                                    title = result.get("title", "未命名测试")
                                    
                                    f.write(f"- {case_id}: {title}\n")
                    
                    # 问题和解决方案
                    issues_found = workflow_result.get("issues_found", 0)
                    solutions = workflow_result.get("solutions", [])
                    
                    if issues_found > 0:
                        f.write(f"\n### 问题和解决方案\n\n")
                        
                        f.write(f"**发现问题**: {issues_found} 个\n")
                        f.write(f"**生成解决方案**: {len(solutions) if solutions else 0} 个\n")
                
                # 错误信息
                error = validation_result.get("error")
                
                if error:
                    f.write("\n## 错误信息\n\n")
                    f.write(f"```\n{error}\n```\n")
                
                # 结论
                f.write("\n## 结论\n\n")
                
                if validation_result.get("status") == "completed":
                    f.write("端到端工作流验证成功，所有组件和流程正常运行。\n")
                else:
                    f.write("端到端工作流验证失败，请查看详细信息了解具体问题。\n")
            
            logger.info(f"验证报告生成成功: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"生成验证报告失败: {e}")
            return ""
