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
from typing import Dict, List, Any, Optional, Union

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
    MCP中央协调器类，用于协调各个功能模块，实现端到端的自动化流程
    """
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 local_repo_path: Optional[str] = None,
                 github_repo: Optional[str] = None,
                 ssh_key_path: Optional[str] = None,
                 test_script: Optional[str] = None,
                 readme_path: Optional[str] = None):
        """
        初始化MCP中央协调器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
            local_repo_path: 本地仓库路径，如果为None则从配置文件读取
            github_repo: GitHub仓库名称，如果为None则从配置文件读取
            ssh_key_path: SSH密钥路径，如果为None则从配置文件读取
            test_script: 测试脚本名称，如果为None则从配置文件读取
            readme_path: README文件路径，如果为None则从配置文件读取
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 设置参数，优先使用传入的参数，如果为None则使用配置文件中的值
        self.local_repo_path = local_repo_path or self.config.get("local_repo_path")
        self.github_repo = github_repo or self.config.get("github_repo")
        self.ssh_key_path = ssh_key_path or self.config.get("ssh_key_path", "~/.ssh/id_rsa")
        self.test_script = test_script or self.config.get("test_script", "start_and_test.sh")
        self.readme_path = readme_path or self.config.get("readme_path", "README.md")
        
        # 创建日志目录
        self.logs_dir = os.path.join(self.local_repo_path, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # 初始化记录器
        self.recorder = ThoughtActionRecorder(log_dir=self.logs_dir)
        
        # 初始化各功能模块
        self.release_manager = ReleaseManager(
            local_repo_path=self.local_repo_path,
            github_repo=self.github_repo,
            ssh_key_path=self.ssh_key_path,
            recorder=self.recorder
        )
        
        self.test_collector = TestAndIssueCollector(
            repo_path=self.local_repo_path,
            test_script=self.test_script,
            readme_path=self.readme_path,
            recorder=self.recorder
        )
        
        self.problem_solver = ManusProblemSolver(
            repo_path=self.local_repo_path,
            readme_path=self.readme_path,
            recorder=self.recorder
        )
        
        logger.info(f"MCPCentralCoordinator initialized with local path: {self.local_repo_path}")
        logger.info(f"GitHub repository: {self.github_repo}")
        logger.info(f"Test script: {self.test_script}")
        logger.info(f"README path: {self.readme_path}")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
            
        Returns:
            配置字典
        """
        # 默认配置
        default_config = {
            "local_repo_path": "/Users/alexchuang/powerassistant/powerautomation",
            "github_repo": "alexchuang650730/powerautomation",
            "ssh_key_path": "~/.ssh/id_rsa",
            "test_script": "start_and_test.sh",
            "readme_path": "README.md",
            "auto_upload": True,
            "auto_test": True,
            "auto_solve": True
        }
        
        # 如果没有指定配置文件，返回默认配置
        if not config_path:
            logger.info("Using default configuration")
            return default_config
        
        # 加载配置文件
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            logger.info(f"Loaded configuration from {config_path}")
            
            # 合并默认配置和加载的配置
            merged_config = {**default_config, **config}
            return merged_config
            
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            logger.info("Using default configuration")
            return default_config
    
    def save_config(self, config_path: str) -> Dict[str, Any]:
        """
        保存当前配置到文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            保存结果
        """
        self.recorder.record_thought(f"保存配置到 {config_path}")
        
        # 构建当前配置
        current_config = {
            "local_repo_path": self.local_repo_path,
            "github_repo": self.github_repo,
            "ssh_key_path": self.ssh_key_path,
            "test_script": self.test_script,
            "readme_path": self.readme_path,
            "auto_upload": self.config.get("auto_upload", True),
            "auto_test": self.config.get("auto_test", True),
            "auto_solve": self.config.get("auto_solve", True)
        }
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(current_config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved configuration to {config_path}")
            
            self.recorder.record_action(
                "save_config", 
                {"config_path": config_path},
                {"success": True}
            )
            
            return {"success": True, "config_path": config_path}
            
        except Exception as e:
            error_msg = f"Error saving configuration to {config_path}: {e}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "save_config", 
                {"config_path": config_path},
                {"success": False, "error": error_msg}
            )
            
            return {"success": False, "error": error_msg}
    
    def check_and_download_release(self, tag_name: Optional[str] = None) -> Dict[str, Any]:
        """
        检查并下载release
        
        Args:
            tag_name: 指定的标签名称，如果为None则下载最新的release
            
        Returns:
            下载结果
        """
        self.recorder.record_thought(f"检查并下载release {tag_name or '最新'}")
        
        # 检查新的release
        new_releases = self.release_manager.check_for_new_releases()
        
        # 如果指定了标签名称，但该标签不在新release列表中，则尝试直接下载
        if tag_name and tag_name not in new_releases:
            logger.info(f"Specified tag {tag_name} not found in new releases, trying to download directly")
            download_result = self.release_manager.download_release(tag_name)
            
            self.recorder.record_action(
                "check_and_download_release", 
                {"tag_name": tag_name},
                download_result
            )
            
            return download_result
        
        # 如果没有指定标签名称，且没有新的release，则返回错误
        if not tag_name and not new_releases:
            error_msg = "No new releases found"
            logger.info(error_msg)
            
            self.recorder.record_action(
                "check_and_download_release", 
                {"tag_name": tag_name},
                {"success": False, "error": error_msg}
            )
            
            return {"success": False, "error": error_msg}
        
        # 下载release
        target_tag = tag_name or new_releases[0]
        download_result = self.release_manager.download_release(target_tag)
        
        self.recorder.record_action(
            "check_and_download_release", 
            {"tag_name": target_tag},
            download_result
        )
        
        return download_result
    
    def run_tests_and_collect_issues(self) -> Dict[str, Any]:
        """
        运行测试并收集问题
        
        Returns:
            测试结果
        """
        self.recorder.record_thought("运行测试并收集问题")
        
        # 运行完整的测试周期
        test_result = self.test_collector.run_full_test_cycle()
        
        self.recorder.record_action(
            "run_tests_and_collect_issues", 
            {},
            test_result
        )
        
        return test_result
    
    def analyze_and_solve_issues(self) -> Dict[str, Any]:
        """
        分析并解决问题
        
        Returns:
            解决结果
        """
        self.recorder.record_thought("分析并解决问题")
        
        # 运行完整的解决方案周期
        solution_result = self.problem_solver.run_full_solution_cycle()
        
        self.recorder.record_action(
            "analyze_and_solve_issues", 
            {},
            solution_result
        )
        
        return solution_result
    
    def upload_changes(self, commit_message: Optional[str] = None) -> Dict[str, Any]:
        """
        上传更改到GitHub
        
        Args:
            commit_message: 提交信息，如果为None则使用默认信息
            
        Returns:
            上传结果
        """
        # 生成默认提交信息
        if not commit_message:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"自动更新 - 测试结果和解决方案 ({timestamp})"
        
        self.recorder.record_thought(f"上传更改到GitHub，提交信息：{commit_message}")
        
        # 上传更改
        upload_result = self.release_manager.upload_to_github(commit_message)
        
        self.recorder.record_action(
            "upload_changes", 
            {"commit_message": commit_message},
            upload_result
        )
        
        return upload_result
    
    def run_full_workflow(self, tag_name: Optional[str] = None, auto_upload: Optional[bool] = None) -> Dict[str, Any]:
        """
        运行完整的工作流程
        
        Args:
            tag_name: 指定的标签名称，如果为None则使用最新的release
            auto_upload: 是否自动上传更改，如果为None则使用配置中的值
            
        Returns:
            工作流程结果
        """
        self.recorder.record_thought(f"运行完整的工作流程，tag_name={tag_name}, auto_upload={auto_upload}")
        
        workflow_result = {
            "success": True,
            "steps": {}
        }
        
        # 确定是否自动上传
        should_auto_upload = auto_upload if auto_upload is not None else self.config.get("auto_upload", True)
        
        # 步骤1：检查并下载release
        logger.info("Step 1: Checking and downloading release")
        download_result = self.check_and_download_release(tag_name)
        workflow_result["steps"]["download"] = download_result
        
        if not download_result["success"]:
            logger.error(f"Failed to download release: {download_result.get('error')}")
            workflow_result["success"] = False
            return workflow_result
        
        # 步骤2：运行测试并收集问题
        logger.info("Step 2: Running tests and collecting issues")
        test_result = self.run_tests_and_collect_issues()
        workflow_result["steps"]["test"] = test_result
        
        if not test_result["success"]:
            logger.error(f"Failed to run tests: {test_result.get('error')}")
            workflow_result["success"] = False
            
            # 如果配置了自动上传，即使测试失败也上传结果
            if should_auto_upload:
                logger.info("Uploading test results despite test failure")
                upload_result = self.upload_changes("自动更新 - 测试失败结果")
                workflow_result["steps"]["upload"] = upload_result
            
            return workflow_result
        
        # 步骤3：分析并解决问题
        logger.info("Step 3: Analyzing and solving issues")
        solution_result = self.analyze_and_solve_issues()
        workflow_result["steps"]["solution"] = solution_result
        
        if not solution_result["success"]:
            logger.error(f"Failed to solve issues: {solution_result.get('error')}")
            workflow_result["success"] = False
            
            # 如果配置了自动上传，即使解决问题失败也上传结果
            if should_auto_upload:
                logger.info("Uploading results despite solution failure")
                upload_result = self.upload_changes("自动更新 - 测试结果（解决方案生成失败）")
                workflow_result["steps"]["upload"] = upload_result
            
            return workflow_result
        
        # 步骤4：上传更改
        if should_auto_upload:
            logger.info("Step 4: Uploading changes")
            upload_result = self.upload_changes()
            workflow_result["steps"]["upload"] = upload_result
            
            if not upload_result["success"]:
                logger.error(f"Failed to upload changes: {upload_result.get('error')}")
                workflow_result["success"] = False
                return workflow_result
        else:
            logger.info("Auto upload is disabled, skipping upload step")
            workflow_result["steps"]["upload"] = {"success": True, "skipped": True}
        
        logger.info("Full workflow completed successfully")
        
        self.recorder.record_action(
            "run_full_workflow", 
            {"tag_name": tag_name, "auto_upload": should_auto_upload},
            workflow_result
        )
        
        return workflow_result
    
    def generate_workflow_report(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成工作流程报告
        
        Args:
            workflow_result: 工作流程结果
            
        Returns:
            报告生成结果
        """
        self.recorder.record_thought("生成工作流程报告")
        
        # 创建报告文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.local_repo_path, "reports", f"workflow_report_{timestamp}.md")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write("# PowerAutomation MCP工作流程报告\n\n")
                f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 总体结果
                f.write("## 总体结果\n\n")
                f.write(f"工作流程 {'成功' if workflow_result.get('success') else '失败'}\n\n")
                
                # 下载步骤
                f.write("## 步骤1: 检查并下载Release\n\n")
                download_result = workflow_result.get("steps", {}).get("download", {})
                
                if download_result.get("success"):
                    f.write(f"✅ 成功下载Release: {download_result.get('tag_name')}\n")
                    f.write(f"本地路径: {download_result.get('local_path')}\n\n")
                else:
                    f.write(f"❌ 下载Release失败: {download_result.get('error')}\n\n")
                
                # 测试步骤
                f.write("## 步骤2: 运行测试并收集问题\n\n")
                test_result = workflow_result.get("steps", {}).get("test", {})
                
                if test_result.get("success"):
                    test_details = test_result.get("test_result", {})
                    issues = test_result.get("issues", [])
                    
                    f.write(f"✅ 测试{'成功' if test_details.get('success') else '失败但流程继续'}\n")
                    f.write(f"发现 {len(issues)} 个问题\n\n")
                    
                    if issues:
                        f.write("### 发现的问题\n\n")
                        for i, issue in enumerate(issues, 1):
                            f.write(f"{i}. **{issue.get('type', '').upper()}**: {issue.get('file', '')}\n")
                            f.write(f"   ```\n   {issue.get('context', '')}\n   ```\n\n")
                else:
                    f.write(f"❌ 运行测试失败: {test_result.get('error')}\n\n")
                
                # 解决方案步骤
                f.write("## 步骤3: 分析并解决问题\n\n")
                solution_result = workflow_result.get("steps", {}).get("solution", {})
                
                if solution_result.get("success"):
                    process_result = solution_result.get("process_result", {})
                    issues_count = process_result.get("issues_count", 0)
                    
                    if issues_count > 0:
                        f.write(f"✅ 成功分析并解决 {issues_count} 个问题\n\n")
                        
                        f.write("### 解决方案摘要\n\n")
                        for i, result in enumerate(process_result.get("results", []), 1):
                            issue = result.get("issue", {})
                            fix_strategy = result.get("fix_strategy", {})
                            
                            f.write(f"{i}. **{issue.get('type', '').upper()}**: {issue.get('file', '')}\n")
                            f.write(f"   - 优先级: {fix_strategy.get('priority', '')}\n")
                            f.write(f"   - 预估工作量: {fix_strategy.get('estimated_effort', '')}\n")
                            f.write(f"   - 推荐操作: {', '.join(fix_strategy.get('recommended_actions', []))}\n\n")
                    else:
                        f.write("✅ 没有发现需要解决的问题\n\n")
                else:
                    f.write(f"❌ 分析并解决问题失败: {solution_result.get('error')}\n\n")
                
                # 上传步骤
                f.write("## 步骤4: 上传更改\n\n")
                upload_result = workflow_result.get("steps", {}).get("upload", {})
                
                if upload_result.get("skipped"):
                    f.write("⏩ 自动上传已禁用，跳过上传步骤\n\n")
                elif upload_result.get("success"):
                    f.write(f"✅ 成功上传更改\n")
                    f.write(f"提交信息: {upload_result.get('commit_message')}\n\n")
                else:
                    f.write(f"❌ 上传更改失败: {upload_result.get('error')}\n\n")
                
                # 总结
                f.write("## 总结\n\n")
                
                if workflow_result.get("success"):
                    f.write("✅ 工作流程成功完成\n\n")
                else:
                    f.write("❌ 工作流程失败\n\n")
                    
                    # 查找失败步骤
                    failed_steps = []
                    for step, result in workflow_result.get("steps", {}).items():
                        if not result.get("success") and not result.get("skipped"):
                            failed_steps.append(step)
                    
                    f.write(f"失败步骤: {', '.join(failed_steps)}\n\n")
                
                f.write("---\n\n")
                f.write("*此报告由PowerAutomation MCP工具自动生成*\n")
            
            logger.info(f"Generated workflow report: {report_path}")
            
            self.recorder.record_action(
                "generate_workflow_report", 
                {"workflow_result": workflow_result},
                {"success": True, "report_path": report_path}
            )
            
            return {"success": True, "report_path": report_path}
            
        except Exception as e:
            error_msg = f"Error generating workflow report: {str(e)}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "generate_workflow_report", 
                {"workflow_result": workflow_result},
                {"success": False, "error": error_msg}
            )
            
            return {"success": False, "error": error_msg}
