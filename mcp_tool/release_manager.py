"""
Release下载与GitHub上传模块 - ReleaseManager

该模块负责监控GitHub release事件，自动下载代码到Mac端侧，
并处理GitHub上传流程，支持SSH密钥认证。

作者: Manus AI
日期: 2025-05-28
"""

import os
import time
import logging
import json
import shutil
import subprocess
import requests
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import tempfile
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ReleaseManager")

class ReleaseManager:
    """
    Release管理器，负责监控GitHub release事件，
    自动下载代码到Mac端侧，并处理GitHub上传流程。
    """
    
    def __init__(self, 
                 repo_url: str,
                 local_repo_path: str,
                 github_token: Optional[str] = None,
                 ssh_key_path: Optional[str] = None,
                 check_interval: float = 3600.0):
        """
        初始化Release管理器
        
        Args:
            repo_url: GitHub仓库URL
            local_repo_path: 本地仓库路径
            github_token: GitHub个人访问令牌（可选）
            ssh_key_path: SSH密钥路径（可选）
            check_interval: 检查间隔（秒）
        """
        self.repo_url = repo_url
        self.local_repo_path = os.path.expanduser(local_repo_path)
        self.github_token = github_token
        self.ssh_key_path = os.path.expanduser(ssh_key_path) if ssh_key_path else None
        self.check_interval = check_interval
        
        # 解析仓库信息
        self.repo_owner, self.repo_name = self._parse_repo_url(repo_url)
        
        # 创建本地仓库目录
        os.makedirs(self.local_repo_path, exist_ok=True)
        
        # 最新release信息
        self.latest_release = None
        
        logger.info(f"初始化Release管理器: {self.repo_owner}/{self.repo_name} -> {self.local_repo_path}")
    
    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """
        解析仓库URL，提取所有者和仓库名
        
        Args:
            repo_url: GitHub仓库URL
            
        Returns:
            Tuple[str, str]: 仓库所有者和仓库名
        """
        # 支持多种URL格式
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        # https://github.com/owner/repo
        
        if "github.com" not in repo_url:
            raise ValueError(f"不支持的仓库URL格式: {repo_url}")
        
        if repo_url.startswith("git@github.com:"):
            # SSH格式
            path = repo_url.split("git@github.com:")[1]
        elif "github.com/" in repo_url:
            # HTTPS格式
            path = repo_url.split("github.com/")[1]
        else:
            raise ValueError(f"无法解析仓库URL: {repo_url}")
        
        # 移除.git后缀
        path = path.replace(".git", "")
        
        # 分割所有者和仓库名
        parts = path.split("/")
        if len(parts) != 2:
            raise ValueError(f"无法解析仓库所有者和名称: {path}")
        
        return parts[0], parts[1]
    
    def check_latest_release(self) -> Dict:
        """
        检查最新的release
        
        Returns:
            Dict: 最新release信息
        """
        logger.info(f"检查 {self.repo_owner}/{self.repo_name} 的最新release")
        
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            
            release_info = response.json()
            logger.info(f"获取到最新release: {release_info['tag_name']}")
            
            self.latest_release = release_info
            return release_info
        except requests.exceptions.RequestException as e:
            logger.error(f"获取最新release失败: {e}")
            return None
    
    def is_new_release_available(self) -> bool:
        """
        检查是否有新的release可用
        
        Returns:
            bool: 如果有新的release可用，返回True；否则返回False
        """
        # 获取最新release
        latest_release = self.check_latest_release()
        if not latest_release:
            return False
        
        # 检查本地记录
        local_record_path = os.path.join(self.local_repo_path, ".release_record")
        if not os.path.exists(local_record_path):
            logger.info("本地没有release记录，视为有新release可用")
            return True
        
        try:
            with open(local_record_path, "r") as f:
                local_record = json.load(f)
            
            local_tag = local_record.get("tag_name")
            latest_tag = latest_release.get("tag_name")
            
            if local_tag != latest_tag:
                logger.info(f"发现新release: {local_tag} -> {latest_tag}")
                return True
            else:
                logger.info(f"没有新release可用，当前版本: {local_tag}")
                return False
        except Exception as e:
            logger.error(f"检查本地release记录失败: {e}")
            return True  # 出错时假设有新release可用
    
    def download_release(self, tag_name: Optional[str] = None) -> bool:
        """
        下载指定tag的release代码
        
        Args:
            tag_name: release标签名，如果为None则下载最新release
            
        Returns:
            bool: 如果下载成功，返回True；否则返回False
        """
        # 如果未指定tag，获取最新release
        if not tag_name:
            if not self.latest_release:
                self.check_latest_release()
            
            if not self.latest_release:
                logger.error("无法获取最新release信息")
                return False
            
            tag_name = self.latest_release["tag_name"]
        
        logger.info(f"开始下载release: {tag_name}")
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 克隆仓库到临时目录
            clone_url = self._get_clone_url()
            clone_cmd = ["git", "clone", "--depth", "1"]
            
            if tag_name:
                clone_cmd.extend(["--branch", tag_name])
            
            clone_cmd.extend([clone_url, temp_dir])
            
            logger.info(f"执行克隆命令: {' '.join(clone_cmd)}")
            subprocess.run(clone_cmd, check=True, capture_output=True)
            
            # 移除.git目录
            git_dir = os.path.join(temp_dir, ".git")
            if os.path.exists(git_dir):
                shutil.rmtree(git_dir)
            
            # 清空本地仓库目录（保留.git和.release_record）
            self._clean_local_repo()
            
            # 复制文件到本地仓库
            self._copy_files(temp_dir, self.local_repo_path)
            
            # 更新本地release记录
            self._update_release_record(tag_name)
            
            logger.info(f"成功下载release {tag_name} 到 {self.local_repo_path}")
            return True
        except Exception as e:
            logger.error(f"下载release失败: {e}")
            return False
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
    
    def _get_clone_url(self) -> str:
        """
        获取克隆URL
        
        Returns:
            str: 克隆URL
        """
        if self.ssh_key_path:
            # 使用SSH URL
            return f"git@github.com:{self.repo_owner}/{self.repo_name}.git"
        else:
            # 使用HTTPS URL
            if self.github_token:
                return f"https://{self.github_token}@github.com/{self.repo_owner}/{self.repo_name}.git"
            else:
                return f"https://github.com/{self.repo_owner}/{self.repo_name}.git"
    
    def _clean_local_repo(self):
        """清空本地仓库目录，但保留.git和.release_record"""
        for item in os.listdir(self.local_repo_path):
            if item in [".git", ".release_record"]:
                continue
            
            item_path = os.path.join(self.local_repo_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
    
    def _copy_files(self, src_dir: str, dst_dir: str):
        """
        复制文件
        
        Args:
            src_dir: 源目录
            dst_dir: 目标目录
        """
        for item in os.listdir(src_dir):
            src_path = os.path.join(src_dir, item)
            dst_path = os.path.join(dst_dir, item)
            
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
    
    def _update_release_record(self, tag_name: str):
        """
        更新本地release记录
        
        Args:
            tag_name: release标签名
        """
        record = {
            "tag_name": tag_name,
            "downloaded_at": datetime.now().isoformat()
        }
        
        record_path = os.path.join(self.local_repo_path, ".release_record")
        with open(record_path, "w") as f:
            json.dump(record, f, indent=2)
    
    def upload_to_github(self, commit_message: str, branch: str = "main") -> bool:
        """
        将本地代码上传到GitHub
        
        Args:
            commit_message: 提交信息
            branch: 分支名称
            
        Returns:
            bool: 如果上传成功，返回True；否则返回False
        """
        logger.info(f"开始上传代码到GitHub: {self.repo_owner}/{self.repo_name}")
        
        try:
            # 检查本地仓库是否已初始化Git
            git_dir = os.path.join(self.local_repo_path, ".git")
            if not os.path.exists(git_dir):
                # 初始化Git仓库
                self._init_git_repo()
            
            # 配置Git
            self._configure_git()
            
            # 添加所有文件
            add_cmd = ["git", "add", "."]
            subprocess.run(add_cmd, cwd=self.local_repo_path, check=True)
            
            # 提交更改
            commit_cmd = ["git", "commit", "-m", commit_message]
            subprocess.run(commit_cmd, cwd=self.local_repo_path, check=True)
            
            # 推送到GitHub
            push_cmd = ["git", "push", "-u", "origin", branch]
            subprocess.run(push_cmd, cwd=self.local_repo_path, check=True)
            
            logger.info(f"成功上传代码到GitHub: {self.repo_owner}/{self.repo_name}")
            return True
        except Exception as e:
            logger.error(f"上传代码到GitHub失败: {e}")
            return False
    
    def _init_git_repo(self):
        """初始化Git仓库"""
        logger.info(f"初始化Git仓库: {self.local_repo_path}")
        
        # 初始化仓库
        init_cmd = ["git", "init"]
        subprocess.run(init_cmd, cwd=self.local_repo_path, check=True)
        
        # 添加远程仓库
        remote_url = self._get_clone_url()
        remote_cmd = ["git", "remote", "add", "origin", remote_url]
        subprocess.run(remote_cmd, cwd=self.local_repo_path, check=True)
    
    def _configure_git(self):
        """配置Git"""
        # 配置用户名和邮箱
        subprocess.run(["git", "config", "user.name", "PowerAutomation MCP"], cwd=self.local_repo_path)
        subprocess.run(["git", "config", "user.email", "powerautomation@example.com"], cwd=self.local_repo_path)
        
        # 如果使用SSH密钥，配置SSH
        if self.ssh_key_path:
            # 确保SSH配置目录存在
            ssh_dir = os.path.expanduser("~/.ssh")
            os.makedirs(ssh_dir, exist_ok=True)
            
            # 配置SSH密钥
            ssh_config_path = os.path.join(ssh_dir, "config")
            with open(ssh_config_path, "a+") as f:
                f.seek(0)
                content = f.read()
                
                # 检查是否已配置
                if f"IdentityFile {self.ssh_key_path}" not in content:
                    f.write(f"\nHost github.com\n  IdentityFile {self.ssh_key_path}\n  User git\n")
    
    def create_release(self, tag_name: str, release_name: str, body: str, draft: bool = False, prerelease: bool = False) -> Dict:
        """
        创建新的GitHub release
        
        Args:
            tag_name: 标签名
            release_name: release名称
            body: release描述
            draft: 是否为草稿
            prerelease: 是否为预发布
            
        Returns:
            Dict: 创建的release信息
        """
        if not self.github_token:
            logger.error("创建release需要GitHub令牌")
            return None
        
        logger.info(f"开始创建release: {tag_name}")
        
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.github_token}"
        }
        
        data = {
            "tag_name": tag_name,
            "name": release_name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=data)
            response.raise_for_status()
            
            release_info = response.json()
            logger.info(f"成功创建release: {release_info['tag_name']}")
            
            self.latest_release = release_info
            return release_info
        except requests.exceptions.RequestException as e:
            logger.error(f"创建release失败: {e}")
            return None
    
    def monitor_releases(self, callback=None):
        """
        监控releases，当有新release时执行回调函数
        
        Args:
            callback: 回调函数，接收release信息作为参数
        """
        logger.info(f"开始监控 {self.repo_owner}/{self.repo_name} 的releases")
        
        while True:
            try:
                if self.is_new_release_available():
                    if callback:
                        callback(self.latest_release)
                
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("监控被用户中断")
                break
            except Exception as e:
                logger.error(f"监控releases时发生错误: {e}")
                time.sleep(self.check_interval)
    
    def get_release_by_tag(self, tag_name: str) -> Dict:
        """
        获取指定tag的release信息
        
        Args:
            tag_name: 标签名
            
        Returns:
            Dict: release信息
        """
        logger.info(f"获取tag为 {tag_name} 的release信息")
        
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/tags/{tag_name}"
        
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            
            release_info = response.json()
            logger.info(f"获取到release: {release_info['tag_name']}")
            
            return release_info
        except requests.exceptions.RequestException as e:
            logger.error(f"获取release失败: {e}")
            return None
    
    def list_releases(self, limit: int = 10) -> List[Dict]:
        """
        列出最近的releases
        
        Args:
            limit: 最大数量
            
        Returns:
            List[Dict]: release列表
        """
        logger.info(f"列出 {self.repo_owner}/{self.repo_name} 的releases")
        
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases"
        
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        params = {
            "per_page": limit
        }
        
        try:
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            
            releases = response.json()
            logger.info(f"获取到 {len(releases)} 个releases")
            
            return releases
        except requests.exceptions.RequestException as e:
            logger.error(f"列出releases失败: {e}")
            return []
    
    def get_local_repo_status(self) -> Dict:
        """
        获取本地仓库状态
        
        Returns:
            Dict: 本地仓库状态
        """
        status = {
            "path": self.local_repo_path,
            "exists": os.path.exists(self.local_repo_path),
            "is_git_repo": False,
            "current_branch": None,
            "has_changes": False,
            "last_commit": None,
            "release_record": None
        }
        
        if not status["exists"]:
            return status
        
        # 检查是否为Git仓库
        git_dir = os.path.join(self.local_repo_path, ".git")
        status["is_git_repo"] = os.path.exists(git_dir)
        
        if status["is_git_repo"]:
            try:
                # 获取当前分支
                branch_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
                branch_result = subprocess.run(branch_cmd, cwd=self.local_repo_path, capture_output=True, text=True, check=True)
                status["current_branch"] = branch_result.stdout.strip()
                
                # 检查是否有未提交的更改
                status_cmd = ["git", "status", "--porcelain"]
                status_result = subprocess.run(status_cmd, cwd=self.local_repo_path, capture_output=True, text=True, check=True)
                status["has_changes"] = bool(status_result.stdout.strip())
                
                # 获取最后一次提交
                log_cmd = ["git", "log", "-1", "--pretty=format:%h|%an|%ad|%s"]
                log_result = subprocess.run(log_cmd, cwd=self.local_repo_path, capture_output=True, text=True)
                if log_result.returncode == 0:
                    parts = log_result.stdout.strip().split("|")
                    if len(parts) == 4:
                        status["last_commit"] = {
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3]
                        }
            except Exception as e:
                logger.error(f"获取Git状态失败: {e}")
        
        # 检查release记录
        record_path = os.path.join(self.local_repo_path, ".release_record")
        if os.path.exists(record_path):
            try:
                with open(record_path, "r") as f:
                    status["release_record"] = json.load(f)
            except Exception as e:
                logger.error(f"读取release记录失败: {e}")
        
        return status
