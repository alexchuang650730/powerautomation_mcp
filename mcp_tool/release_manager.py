"""
Release管理器模块 - ReleaseManager

该模块用于管理GitHub release，包括检测新release、下载代码到端侧Mac和上传更改到GitHub。
主要功能：
1. 监控GitHub release事件
2. 自动下载代码到指定Mac路径
3. 处理GitHub上传流程
4. 管理SSH密钥和权限
5. 支持增量和全量更新

作者: Manus AI
日期: 2025-05-28
"""

import os
import json
import time
import datetime
import subprocess
import logging
import shutil
from typing import Dict, List, Any, Optional, Union

# 导入思考与操作记录器
from .thought_action_recorder import ThoughtActionRecorder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ReleaseManager")

class ReleaseManager:
    """
    Release管理器类，用于管理GitHub release
    """
    
    def __init__(self, 
                 local_repo_path: str,
                 github_repo: str,
                 ssh_key_path: str = "~/.ssh/id_rsa",
                 recorder: ThoughtActionRecorder = None):
        """
        初始化Release管理器
        
        Args:
            local_repo_path: 本地仓库路径
            github_repo: GitHub仓库名称，格式为"用户名/仓库名"
            ssh_key_path: SSH密钥路径，默认为"~/.ssh/id_rsa"
            recorder: 思考与操作记录器实例，如果为None则创建新实例
        """
        self.local_repo_path = local_repo_path
        self.github_repo = github_repo
        self.ssh_key_path = os.path.expanduser(ssh_key_path)
        
        # 初始化记录器
        self.recorder = recorder or ThoughtActionRecorder(
            log_dir=os.path.join(local_repo_path, "logs")
        )
        
        logger.info(f"ReleaseManager initialized with local path: {local_repo_path}")
        logger.info(f"GitHub repository: {github_repo}")
        logger.info(f"SSH key path: {self.ssh_key_path}")
    
    def check_for_new_releases(self) -> List[str]:
        """
        检查GitHub上是否有新的release
        
        Returns:
            新release标签列表
        """
        self.recorder.record_thought("检查GitHub上是否有新的release")
        
        cmd = f"git ls-remote --tags git@github.com:{self.github_repo}.git"
        result = self._run_command(cmd)
        
        # 解析远程标签
        remote_tags = []
        if result["success"]:
            for line in result["output"].splitlines():
                if "refs/tags" in line:
                    tag = line.split("refs/tags/")[1]
                    # 过滤掉指向其他对象的标签引用（通常以^{}结尾）
                    if not tag.endswith("^{}"):
                        remote_tags.append(tag)
        
        # 获取本地标签
        cmd = "git tag"
        result = self._run_command(cmd, cwd=self.local_repo_path)
        local_tags = result["output"].splitlines() if result["success"] else []
        
        # 找出新的标签
        new_tags = [tag for tag in remote_tags if tag not in local_tags]
        
        self.recorder.record_action(
            "check_releases", 
            {"github_repo": self.github_repo},
            {"new_tags": new_tags, "remote_tags_count": len(remote_tags), "local_tags_count": len(local_tags)}
        )
        
        logger.info(f"Found {len(new_tags)} new releases: {new_tags}")
        
        return new_tags
    
    def download_release(self, tag_name: str) -> Dict[str, Any]:
        """
        下载指定release到本地路径
        
        Args:
            tag_name: release标签名
            
        Returns:
            下载结果
        """
        self.recorder.record_thought(f"下载release {tag_name}到本地路径 {self.local_repo_path}")
        
        # 确保本地目录存在
        os.makedirs(self.local_repo_path, exist_ok=True)
        
        # 检查是否已经是git仓库
        is_git_repo = os.path.exists(os.path.join(self.local_repo_path, ".git"))
        
        if not is_git_repo:
            # 如果不是git仓库，则克隆
            logger.info(f"Directory is not a git repository, cloning...")
            cmd = f"git clone git@github.com:{self.github_repo}.git {self.local_repo_path}"
            clone_result = self._run_command(cmd)
            
            if not clone_result["success"]:
                error_msg = f"Failed to clone repository: {clone_result['error']}"
                logger.error(error_msg)
                
                self.recorder.record_action(
                    "clone_repo", 
                    {"github_repo": self.github_repo, "local_path": self.local_repo_path},
                    {"success": False, "error": clone_result["error"]}
                )
                
                return {"success": False, "error": error_msg}
            
            logger.info("Repository cloned successfully")
        else:
            # 如果是git仓库，则获取最新更改
            logger.info(f"Directory is already a git repository, fetching updates...")
            cmd = "git fetch --all"
            fetch_result = self._run_command(cmd, cwd=self.local_repo_path)
            
            if not fetch_result["success"]:
                error_msg = f"Failed to fetch updates: {fetch_result['error']}"
                logger.error(error_msg)
                
                self.recorder.record_action(
                    "fetch_updates", 
                    {"local_path": self.local_repo_path},
                    {"success": False, "error": fetch_result["error"]}
                )
                
                return {"success": False, "error": error_msg}
            
            logger.info("Updates fetched successfully")
        
        # 切换到指定的tag
        logger.info(f"Checking out tag: {tag_name}")
        cmd = f"git checkout {tag_name}"
        checkout_result = self._run_command(cmd, cwd=self.local_repo_path)
        
        if not checkout_result["success"]:
            error_msg = f"Failed to checkout tag {tag_name}: {checkout_result['error']}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "checkout_tag", 
                {"tag_name": tag_name, "local_path": self.local_repo_path},
                {"success": False, "error": checkout_result["error"]}
            )
            
            return {"success": False, "error": error_msg}
        
        logger.info(f"Successfully checked out tag {tag_name}")
        
        # 记录操作结果
        self.recorder.record_action(
            "download_release", 
            {"tag_name": tag_name, "local_path": self.local_repo_path},
            {"success": True, "output": checkout_result["output"]}
        )
        
        return {
            "success": True,
            "tag_name": tag_name,
            "local_path": self.local_repo_path,
            "output": checkout_result["output"]
        }
    
    def upload_to_github(self, commit_message: str, branch: str = "main") -> Dict[str, Any]:
        """
        将本地更改上传到GitHub
        
        Args:
            commit_message: 提交信息
            branch: 分支名称，默认为"main"
            
        Returns:
            上传结果
        """
        self.recorder.record_thought(f"将本地更改上传到GitHub，提交信息：{commit_message}")
        
        # 检查本地仓库是否存在
        if not os.path.exists(os.path.join(self.local_repo_path, ".git")):
            error_msg = f"Directory {self.local_repo_path} is not a git repository"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "upload_to_github", 
                {"commit_message": commit_message, "branch": branch},
                {"success": False, "error": error_msg}
            )
            
            return {"success": False, "error": error_msg}
        
        # 添加所有更改
        logger.info("Adding all changes...")
        cmd = "git add ."
        add_result = self._run_command(cmd, cwd=self.local_repo_path)
        
        if not add_result["success"]:
            error_msg = f"Failed to add changes: {add_result['error']}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "git_add", 
                {"cwd": self.local_repo_path},
                {"success": False, "error": add_result["error"]}
            )
            
            return {"success": False, "error": error_msg}
        
        # 提交更改
        logger.info(f"Committing changes with message: {commit_message}")
        cmd = f'git commit -m "{commit_message}"'
        commit_result = self._run_command(cmd, cwd=self.local_repo_path)
        
        # 检查提交结果，如果没有更改需要提交，则继续
        if not commit_result["success"] and "nothing to commit" not in commit_result.get("error", ""):
            error_msg = f"Failed to commit changes: {commit_result['error']}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "git_commit", 
                {"commit_message": commit_message},
                {"success": False, "error": commit_result["error"]}
            )
            
            return {"success": False, "error": error_msg}
        elif "nothing to commit" in commit_result.get("error", ""):
            logger.info("No changes to commit")
            
            self.recorder.record_action(
                "git_commit", 
                {"commit_message": commit_message},
                {"success": True, "message": "No changes to commit"}
            )
        else:
            logger.info("Changes committed successfully")
        
        # 推送到GitHub
        logger.info(f"Pushing to branch {branch}...")
        cmd = f"git push origin {branch}"
        push_result = self._run_command(cmd, cwd=self.local_repo_path)
        
        if not push_result["success"]:
            error_msg = f"Failed to push changes: {push_result['error']}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "git_push", 
                {"branch": branch},
                {"success": False, "error": push_result["error"]}
            )
            
            return {"success": False, "error": error_msg}
        
        logger.info(f"Changes pushed to {branch} successfully")
        
        # 记录操作结果
        self.recorder.record_action(
            "upload_to_github", 
            {"commit_message": commit_message, "branch": branch},
            {"success": True, "output": push_result["output"]}
        )
        
        return {
            "success": True,
            "commit_message": commit_message,
            "branch": branch,
            "output": push_result["output"]
        }
    
    def create_new_release(self, tag_name: str, release_name: str, release_notes: str) -> Dict[str, Any]:
        """
        创建新的GitHub release
        
        Args:
            tag_name: 标签名称
            release_name: release名称
            release_notes: release说明
            
        Returns:
            创建结果
        """
        self.recorder.record_thought(f"创建新的GitHub release：{tag_name}")
        
        # 检查本地仓库是否存在
        if not os.path.exists(os.path.join(self.local_repo_path, ".git")):
            error_msg = f"Directory {self.local_repo_path} is not a git repository"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "create_release", 
                {"tag_name": tag_name, "release_name": release_name},
                {"success": False, "error": error_msg}
            )
            
            return {"success": False, "error": error_msg}
        
        # 创建新标签
        logger.info(f"Creating new tag: {tag_name}")
        cmd = f'git tag -a {tag_name} -m "{release_name}"'
        tag_result = self._run_command(cmd, cwd=self.local_repo_path)
        
        if not tag_result["success"]:
            error_msg = f"Failed to create tag {tag_name}: {tag_result['error']}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "create_tag", 
                {"tag_name": tag_name, "release_name": release_name},
                {"success": False, "error": tag_result["error"]}
            )
            
            return {"success": False, "error": error_msg}
        
        logger.info(f"Tag {tag_name} created successfully")
        
        # 推送标签到GitHub
        logger.info(f"Pushing tag {tag_name} to GitHub...")
        cmd = f"git push origin {tag_name}"
        push_result = self._run_command(cmd, cwd=self.local_repo_path)
        
        if not push_result["success"]:
            error_msg = f"Failed to push tag {tag_name}: {push_result['error']}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "push_tag", 
                {"tag_name": tag_name},
                {"success": False, "error": push_result["error"]}
            )
            
            return {"success": False, "error": error_msg}
        
        logger.info(f"Tag {tag_name} pushed successfully")
        
        # 使用GitHub CLI创建release（如果安装了）
        release_notes_file = os.path.join(self.local_repo_path, "release_notes.md")
        
        try:
            with open(release_notes_file, "w", encoding="utf-8") as f:
                f.write(release_notes)
            
            logger.info(f"Creating GitHub release using gh CLI...")
            cmd = f'gh release create {tag_name} --title "{release_name}" --notes-file {release_notes_file}'
            release_result = self._run_command(cmd, cwd=self.local_repo_path)
            
            # 清理临时文件
            if os.path.exists(release_notes_file):
                os.remove(release_notes_file)
            
            if not release_result["success"]:
                # 如果gh命令失败，可能是因为没有安装GitHub CLI
                logger.warning(f"Failed to create release using gh CLI: {release_result['error']}")
                logger.info("Release tag was created and pushed, but GitHub release was not created")
                
                self.recorder.record_action(
                    "create_release", 
                    {"tag_name": tag_name, "release_name": release_name},
                    {
                        "success": True, 
                        "warning": "GitHub release was not created, only tag was pushed",
                        "tag_pushed": True,
                        "release_created": False
                    }
                )
                
                return {
                    "success": True,
                    "warning": "GitHub release was not created, only tag was pushed",
                    "tag_pushed": True,
                    "release_created": False,
                    "tag_name": tag_name,
                    "release_name": release_name
                }
            
            logger.info(f"GitHub release {tag_name} created successfully")
            
            self.recorder.record_action(
                "create_release", 
                {"tag_name": tag_name, "release_name": release_name},
                {"success": True, "output": release_result["output"]}
            )
            
            return {
                "success": True,
                "tag_name": tag_name,
                "release_name": release_name,
                "output": release_result["output"],
                "tag_pushed": True,
                "release_created": True
            }
            
        except Exception as e:
            error_msg = f"Error creating release: {str(e)}"
            logger.error(error_msg)
            
            # 清理临时文件
            if os.path.exists(release_notes_file):
                os.remove(release_notes_file)
            
            self.recorder.record_action(
                "create_release", 
                {"tag_name": tag_name, "release_name": release_name},
                {"success": False, "error": error_msg}
            )
            
            return {"success": False, "error": error_msg}
    
    def get_release_info(self, tag_name: str) -> Dict[str, Any]:
        """
        获取指定release的信息
        
        Args:
            tag_name: 标签名称
            
        Returns:
            release信息
        """
        self.recorder.record_thought(f"获取release {tag_name}的信息")
        
        # 使用GitHub CLI获取release信息（如果安装了）
        cmd = f"gh release view {tag_name} --json name,tagName,publishedAt,body"
        result = self._run_command(cmd, cwd=self.local_repo_path)
        
        if result["success"]:
            try:
                release_info = json.loads(result["output"])
                
                self.recorder.record_action(
                    "get_release_info", 
                    {"tag_name": tag_name},
                    {"success": True, "release_info": release_info}
                )
                
                logger.info(f"Successfully retrieved release info for {tag_name}")
                
                return {
                    "success": True,
                    "release_info": release_info
                }
            except json.JSONDecodeError:
                error_msg = f"Failed to parse release info: {result['output']}"
                logger.error(error_msg)
                
                self.recorder.record_action(
                    "get_release_info", 
                    {"tag_name": tag_name},
                    {"success": False, "error": error_msg}
                )
                
                return {"success": False, "error": error_msg}
        else:
            # 如果gh命令失败，尝试使用git命令获取标签信息
            cmd = f"git show {tag_name}"
            tag_result = self._run_command(cmd, cwd=self.local_repo_path)
            
            if tag_result["success"]:
                tag_info = {
                    "tagName": tag_name,
                    "name": tag_name,
                    "body": tag_result["output"],
                    "publishedAt": None  # 无法通过git命令获取发布时间
                }
                
                self.recorder.record_action(
                    "get_release_info", 
                    {"tag_name": tag_name},
                    {"success": True, "tag_info": tag_info, "warning": "Limited info available without GitHub CLI"}
                )
                
                logger.info(f"Retrieved limited tag info for {tag_name} (GitHub CLI not available)")
                
                return {
                    "success": True,
                    "release_info": tag_info,
                    "warning": "Limited info available without GitHub CLI"
                }
            else:
                error_msg = f"Failed to get release info: {result['error']}"
                logger.error(error_msg)
                
                self.recorder.record_action(
                    "get_release_info", 
                    {"tag_name": tag_name},
                    {"success": False, "error": error_msg}
                )
                
                return {"success": False, "error": error_msg}
    
    def verify_ssh_key(self) -> Dict[str, Any]:
        """
        验证SSH密钥是否有效
        
        Returns:
            验证结果
        """
        self.recorder.record_thought("验证SSH密钥是否有效")
        
        # 检查SSH密钥文件是否存在
        if not os.path.exists(self.ssh_key_path):
            error_msg = f"SSH key file {self.ssh_key_path} does not exist"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "verify_ssh_key", 
                {"ssh_key_path": self.ssh_key_path},
                {"success": False, "error": error_msg}
            )
            
            return {"success": False, "error": error_msg}
        
        # 测试SSH连接
        cmd = f"ssh -T -o StrictHostKeyChecking=no git@github.com"
        result = self._run_command(cmd)
        
        # GitHub的SSH测试总是返回非零状态码，但如果输出包含"successfully authenticated"，则表示成功
        if "successfully authenticated" in result["output"].lower() or "successfully authenticated" in result["error"].lower():
            logger.info("SSH key is valid")
            
            self.recorder.record_action(
                "verify_ssh_key", 
                {"ssh_key_path": self.ssh_key_path},
                {"success": True}
            )
            
            return {"success": True}
        else:
            error_msg = f"SSH key verification failed: {result['error']}"
            logger.error(error_msg)
            
            self.recorder.record_action(
                "verify_ssh_key", 
                {"ssh_key_path": self.ssh_key_path},
                {"success": False, "error": error_msg}
            )
            
            return {"success": False, "error": error_msg}
    
    def _run_command(self, cmd: str, cwd: str = None) -> Dict[str, Any]:
        """
        运行shell命令并返回结果
        
        Args:
            cmd: 要运行的命令
            cwd: 工作目录，如果为None则使用当前目录
            
        Returns:
            命令执行结果
        """
        try:
            logger.debug(f"Running command: {cmd}")
            
            process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = process.communicate()
            
            output = stdout.decode("utf-8")
            error = stderr.decode("utf-8")
            
            success = process.returncode == 0
            
            if not success:
                logger.debug(f"Command failed with return code {process.returncode}")
                logger.debug(f"Error: {error}")
            
            return {
                "success": success,
                "output": output,
                "error": error if not success else None,
                "return_code": process.returncode
            }
        except Exception as e:
            logger.error(f"Exception running command: {e}")
            return {
                "success": False,
                "output": None,
                "error": str(e),
                "return_code": -1
            }
