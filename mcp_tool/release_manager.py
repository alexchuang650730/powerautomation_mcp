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
import requests
import tempfile
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

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
    Release管理器，负责监控GitHub release事件，下载代码到本地，并处理GitHub上传流程。
    """
    
    def __init__(self, 
                 repo_url: Optional[str] = None,
                 local_repo_path: Optional[str] = None,
                 github_token: Optional[str] = None,
                 ssh_key_path: Optional[str] = None,
                 check_interval: float = 3600.0):
        """
        初始化Release管理器
        
        Args:
            repo_url: GitHub仓库URL，如果为None则使用默认URL
            local_repo_path: 本地仓库路径，如果为None则使用默认路径
            github_token: GitHub令牌，如果为None则使用SSH密钥
            ssh_key_path: SSH密钥路径，如果为None则使用默认路径
            check_interval: 检查间隔（秒）
        """
        self.repo_url = repo_url or "https://github.com/alexchuang650730/powerautomation.git"
        self.local_repo_path = local_repo_path or os.path.expanduser("~/powerassistant/powerautomation")
        self.github_token = github_token
        self.ssh_key_path = ssh_key_path or os.path.expanduser("~/.ssh/id_rsa")
        self.check_interval = check_interval
        
        # 提取仓库所有者和名称
        match = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)(?:\.git)?", self.repo_url)
        if match:
            self.repo_owner = match.group(1)
            self.repo_name = match.group(2)
        else:
            self.repo_owner = "alexchuang650730"
            self.repo_name = "powerautomation"
        
        # 记录器
        self.recorder = ThoughtActionRecorder()
        
        # 最后检查时间
        self.last_check_time = 0
        
        # 最后下载的release
        self.last_downloaded_release = None
        
        # 确保本地仓库目录存在
        os.makedirs(self.local_repo_path, exist_ok=True)
        
        logger.info(f"Release管理器初始化完成，仓库: {self.repo_url}, 本地路径: {self.local_repo_path}")
    
    def is_new_release_available(self) -> bool:
        """
        检查是否有新的release可用
        
        Returns:
            bool: 是否有新的release
        """
        self.recorder.record_thought("检查是否有新的release可用")
        
        # 获取最新release
        latest_release = self._get_latest_release()
        
        if latest_release is None:
            logger.info("无法获取最新release信息")
            return False
        
        # 检查本地是否已有该release
        if self._is_release_downloaded(latest_release["tag_name"]):
            logger.info(f"最新release {latest_release['tag_name']} 已下载")
            return False
        
        logger.info(f"发现新release: {latest_release['tag_name']}")
        return True
    
    def download_release(self, tag_name: Optional[str] = None) -> Dict:
        """
        下载指定标签的release，如果未指定则下载最新release
        
        Args:
            tag_name: release标签名，如果为None则下载最新release
            
        Returns:
            Dict: 下载结果
        """
        self.recorder.record_thought(f"下载release: {tag_name or '最新'}")
        
        # 获取release信息
        if tag_name is None:
            release = self._get_latest_release()
            if release is None:
                error_message = "无法获取最新release信息"
                logger.error(error_message)
                
                return {
                    "status": "failed",
                    "message": error_message,
                    "timestamp": datetime.now().isoformat()
                }
        else:
            release = self._get_release_by_tag(tag_name)
            if release is None:
                error_message = f"无法获取标签为 {tag_name} 的release信息"
                logger.error(error_message)
                
                return {
                    "status": "failed",
                    "message": error_message,
                    "timestamp": datetime.now().isoformat()
                }
        
        # 下载release
        try:
            # 备份当前代码
            self._backup_current_code()
            
            # 下载代码
            self._download_release_code(release)
            
            # 更新最后下载的release
            self.last_downloaded_release = release["tag_name"]
            
            result = {
                "status": "success",
                "message": f"成功下载release {release['tag_name']}",
                "tag": release["tag_name"],
                "timestamp": datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "download_release", 
                {"tag_name": tag_name},
                result
            )
            
            return result
        
        except Exception as e:
            error_message = f"下载release异常: {str(e)}"
            logger.error(error_message)
            
            # 恢复备份
            self._restore_backup()
            
            result = {
                "status": "failed",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "download_release", 
                {"tag_name": tag_name},
                result
            )
            
            return result
    
    def get_local_repo_status(self) -> Dict:
        """
        获取本地仓库状态
        
        Returns:
            Dict: 本地仓库状态
        """
        self.recorder.record_thought("获取本地仓库状态")
        
        # 检查本地仓库是否存在
        if not os.path.exists(os.path.join(self.local_repo_path, ".git")):
            return {
                "status": "not_git_repo",
                "has_changes": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # 获取git状态
        try:
            # 获取未暂存的更改
            unstaged_changes = self._run_git_command("git status --porcelain")
            
            # 获取当前分支
            current_branch = self._run_git_command("git rev-parse --abbrev-ref HEAD").strip()
            
            # 获取最后一次提交
            last_commit = self._run_git_command("git log -1 --pretty=format:'%h - %s (%cr)'").strip()
            
            result = {
                "status": "ok",
                "has_changes": bool(unstaged_changes),
                "current_branch": current_branch,
                "last_commit": last_commit,
                "timestamp": datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "get_local_repo_status", 
                {},
                result
            )
            
            return result
        
        except Exception as e:
            error_message = f"获取本地仓库状态异常: {str(e)}"
            logger.error(error_message)
            
            result = {
                "status": "error",
                "message": error_message,
                "has_changes": False,
                "timestamp": datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "get_local_repo_status", 
                {},
                result
            )
            
            return result
    
    def upload_to_github(self, commit_message: str) -> Dict:
        """
        将本地更改上传到GitHub
        
        Args:
            commit_message: 提交信息
            
        Returns:
            Dict: 上传结果
        """
        self.recorder.record_thought(f"上传本地更改到GitHub: {commit_message}")
        
        # 检查本地仓库是否存在
        if not os.path.exists(os.path.join(self.local_repo_path, ".git")):
            error_message = "本地目录不是git仓库"
            logger.error(error_message)
            
            return {
                "status": "failed",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
        
        # 上传更改
        try:
            # 添加所有更改
            self._run_git_command("git add .")
            
            # 提交更改
            self._run_git_command(f"git commit -m '{commit_message}'")
            
            # 推送到GitHub
            self._run_git_command("git push origin HEAD")
            
            # 获取提交ID
            commit_id = self._run_git_command("git rev-parse HEAD").strip()
            
            result = {
                "status": "success",
                "message": f"成功上传更改: {commit_message}",
                "commit_id": commit_id,
                "timestamp": datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "upload_to_github", 
                {"commit_message": commit_message},
                result
            )
            
            return result
        
        except Exception as e:
            error_message = f"上传更改异常: {str(e)}"
            logger.error(error_message)
            
            result = {
                "status": "failed",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
            
            self.recorder.record_action(
                "upload_to_github", 
                {"commit_message": commit_message},
                result
            )
            
            return result
    
    def monitor_releases(self, callback: Optional[callable] = None) -> None:
        """
        监控releases，当有新release时调用回调函数
        
        Args:
            callback: 回调函数，接收release信息作为参数
        """
        self.recorder.record_thought("开始监控releases")
        
        while True:
            try:
                # 检查是否有新release
                if self.is_new_release_available():
                    # 获取最新release
                    latest_release = self._get_latest_release()
                    
                    # 调用回调函数
                    if callback is not None:
                        callback(latest_release)
                
                # 更新最后检查时间
                self.last_check_time = time.time()
                
                # 等待下一次检查
                time.sleep(self.check_interval)
            
            except Exception as e:
                error_message = f"监控releases异常: {str(e)}"
                logger.error(error_message)
                
                # 短暂等待后继续
                time.sleep(60)
    
    def _get_latest_release(self) -> Optional[Dict]:
        """
        获取最新release信息
        
        Returns:
            Optional[Dict]: 最新release信息，如果获取失败则返回None
        """
        # 构建API URL
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        
        # 设置请求头
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            # 发送请求
            response = requests.get(api_url, headers=headers)
            
            # 检查响应状态
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取最新release失败: {response.status_code} {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"获取最新release异常: {str(e)}")
            return None
    
    def _get_release_by_tag(self, tag_name: str) -> Optional[Dict]:
        """
        获取指定标签的release信息
        
        Args:
            tag_name: release标签名
            
        Returns:
            Optional[Dict]: release信息，如果获取失败则返回None
        """
        # 构建API URL
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/tags/{tag_name}"
        
        # 设置请求头
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            # 发送请求
            response = requests.get(api_url, headers=headers)
            
            # 检查响应状态
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取release {tag_name} 失败: {response.status_code} {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"获取release {tag_name} 异常: {str(e)}")
            return None
    
    def _is_release_downloaded(self, tag_name: str) -> bool:
        """
        检查指定标签的release是否已下载
        
        Args:
            tag_name: release标签名
            
        Returns:
            bool: 是否已下载
        """
        # 检查最后下载的release
        if self.last_downloaded_release == tag_name:
            return True
        
        # 检查本地仓库是否存在
        if not os.path.exists(os.path.join(self.local_repo_path, ".git")):
            return False
        
        # 检查本地标签
        try:
            local_tags = self._run_git_command("git tag").splitlines()
            return tag_name in local_tags
        
        except Exception:
            return False
    
    def _backup_current_code(self) -> str:
        """
        备份当前代码
        
        Returns:
            str: 备份目录路径
        """
        # 创建备份目录
        backup_dir = os.path.join(
            os.path.dirname(self.local_repo_path),
            f"backup_{os.path.basename(self.local_repo_path)}_{int(time.time())}"
        )
        
        # 复制当前代码到备份目录
        if os.path.exists(self.local_repo_path):
            shutil.copytree(self.local_repo_path, backup_dir)
            logger.info(f"已备份当前代码到: {backup_dir}")
        
        return backup_dir
    
    def _restore_backup(self) -> bool:
        """
        恢复最近的备份
        
        Returns:
            bool: 是否成功恢复
        """
        # 查找最近的备份
        backup_pattern = os.path.join(
            os.path.dirname(self.local_repo_path),
            f"backup_{os.path.basename(self.local_repo_path)}_*"
        )
        
        backup_dirs = sorted(
            [d for d in glob.glob(backup_pattern) if os.path.isdir(d)],
            key=os.path.getmtime,
            reverse=True
        )
        
        if not backup_dirs:
            logger.error("未找到备份")
            return False
        
        # 使用最近的备份
        latest_backup = backup_dirs[0]
        
        # 删除当前代码
        if os.path.exists(self.local_repo_path):
            shutil.rmtree(self.local_repo_path)
        
        # 复制备份到当前目录
        shutil.copytree(latest_backup, self.local_repo_path)
        
        logger.info(f"已恢复备份: {latest_backup}")
        return True
    
    def _download_release_code(self, release: Dict) -> None:
        """
        下载release代码
        
        Args:
            release: release信息
        """
        # 获取下载URL
        download_url = None
        for asset in release.get("assets", []):
            if asset["name"].endswith(".zip") or asset["name"].endswith(".tar.gz"):
                download_url = asset["browser_download_url"]
                break
        
        # 如果没有找到下载URL，使用源代码下载URL
        if download_url is None:
            download_url = release["zipball_url"]
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 下载文件
            archive_path = os.path.join(temp_dir, "release_archive")
            self._download_file(download_url, archive_path)
            
            # 解压文件
            extract_dir = os.path.join(temp_dir, "extract")
            os.makedirs(extract_dir, exist_ok=True)
            
            if download_url.endswith(".zip"):
                self._run_command(f"unzip -q {archive_path} -d {extract_dir}")
            else:
                self._run_command(f"tar -xzf {archive_path} -C {extract_dir}")
            
            # 查找解压后的目录
            extracted_dirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
            if not extracted_dirs:
                raise Exception("解压后未找到目录")
            
            extracted_dir = os.path.join(extract_dir, extracted_dirs[0])
            
            # 清空本地仓库（保留.git目录）
            for item in os.listdir(self.local_repo_path):
                if item == ".git":
                    continue
                
                item_path = os.path.join(self.local_repo_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            
            # 复制解压后的文件到本地仓库
            for item in os.listdir(extracted_dir):
                src_path = os.path.join(extracted_dir, item)
                dst_path = os.path.join(self.local_repo_path, item)
                
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
        
        # 如果本地仓库不是git仓库，初始化git
        if not os.path.exists(os.path.join(self.local_repo_path, ".git")):
            self._run_git_command("git init")
            self._run_git_command(f"git remote add origin {self.repo_url}")
        
        # 创建标签
        self._run_git_command(f"git tag {release['tag_name']}")
        
        logger.info(f"已下载release {release['tag_name']} 到 {self.local_repo_path}")
    
    def _download_file(self, url: str, output_path: str) -> None:
        """
        下载文件
        
        Args:
            url: 下载URL
            output_path: 输出路径
        """
        # 设置请求头
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        # 下载文件
        with requests.get(url, headers=headers, stream=True) as response:
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
    
    def _run_git_command(self, command: str) -> str:
        """
        运行git命令
        
        Args:
            command: git命令
            
        Returns:
            str: 命令输出
        """
        # 设置环境变量
        env = os.environ.copy()
        
        # 如果使用SSH密钥，设置GIT_SSH_COMMAND
        if not self.github_token and self.ssh_key_path:
            env["GIT_SSH_COMMAND"] = f"ssh -i {self.ssh_key_path} -o StrictHostKeyChecking=no"
        
        # 运行命令
        return self._run_command(command, env=env, cwd=self.local_repo_path)
    
    def _run_command(self, command: str, env: Optional[Dict] = None, cwd: Optional[str] = None) -> str:
        """
        运行命令
        
        Args:
            command: 命令
            env: 环境变量
            cwd: 工作目录
            
        Returns:
            str: 命令输出
        """
        # 运行命令
        process = subprocess.run(
            command,
            shell=True,
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        # 检查返回码
        if process.returncode != 0:
            raise Exception(f"命令执行失败: {process.stderr}")
        
        return process.stdout
