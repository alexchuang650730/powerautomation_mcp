"""
命令行接口模块 - CLI

该模块提供命令行接口，用于管理PowerAutomation代码库、运行测试和工作流程。
支持下载、上传、测试和工作流等功能。

作者: Manus AI
日期: 2025-05-30
"""

import os
import sys
import argparse
import logging
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 导入统一配置管理
from .unified_config import get_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CLI")

class CLI:
    """命令行接口类"""
    
    def __init__(self, config_path=None):
        """
        初始化CLI
        
        Args:
            config_path: 配置文件路径，可选
        """
        # 获取统一配置
        self.config_manager = get_config(config_path)
        self.config = self.config_manager.get_all()
        
        logger.info("CLI初始化完成")
    
    def download(self, version=None) -> bool:
        """
        下载指定版本的代码
        
        Args:
            version: 版本号，可选，默认为最新版本
        
        Returns:
            bool: 是否成功下载
        """
        try:
            local_repo_path = self.config.get("local_repo_path")
            repo_url = self.config.get("repo_url")
            
            if not local_repo_path or not repo_url:
                logger.error("配置中缺少本地仓库路径或仓库URL")
                return False
            
            # 确保本地仓库目录存在
            os.makedirs(os.path.dirname(local_repo_path), exist_ok=True)
            
            # 检查本地仓库是否已存在
            if os.path.exists(local_repo_path):
                # 如果已存在，拉取最新代码
                logger.info(f"本地仓库已存在，拉取最新代码: {local_repo_path}")
                cmd = f"cd {local_repo_path} && git pull"
                subprocess.run(cmd, shell=True, check=True)
            else:
                # 如果不存在，克隆仓库
                logger.info(f"克隆仓库: {repo_url} -> {local_repo_path}")
                cmd = f"git clone {repo_url} {local_repo_path}"
                subprocess.run(cmd, shell=True, check=True)
            
            # 如果指定了版本，切换到该版本
            if version:
                logger.info(f"切换到版本: {version}")
                cmd = f"cd {local_repo_path} && git checkout {version}"
                subprocess.run(cmd, shell=True, check=True)
            
            logger.info("下载完成")
            return True
        
        except Exception as e:
            logger.error(f"下载失败: {e}")
            return False
    
    def upload(self, message=None) -> bool:
        """
        上传本地更改
        
        Args:
            message: 提交信息，可选
        
        Returns:
            bool: 是否成功上传
        """
        try:
            local_repo_path = self.config.get("local_repo_path")
            
            if not local_repo_path:
                logger.error("配置中缺少本地仓库路径")
                return False
            
            # 检查本地仓库是否存在
            if not os.path.exists(local_repo_path):
                logger.error(f"本地仓库不存在: {local_repo_path}")
                return False
            
            # 添加所有更改
            logger.info("添加所有更改")
            cmd = f"cd {local_repo_path} && git add ."
            subprocess.run(cmd, shell=True, check=True)
            
            # 提交更改
            commit_message = message or f"自动提交 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            logger.info(f"提交更改: {commit_message}")
            cmd = f"cd {local_repo_path} && git commit -m \"{commit_message}\""
            subprocess.run(cmd, shell=True)
            
            # 推送更改
            logger.info("推送更改")
            cmd = f"cd {local_repo_path} && git push"
            subprocess.run(cmd, shell=True, check=True)
            
            logger.info("上传完成")
            return True
        
        except Exception as e:
            logger.error(f"上传失败: {e}")
            return False
    
    def test(self) -> Dict[str, Any]:
        """
        运行测试
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            local_repo_path = self.config.get("local_repo_path")
            test_script = self.config.get("test_script")
            
            if not local_repo_path or not test_script:
                logger.error("配置中缺少本地仓库路径或测试脚本")
                return {"status": "error", "message": "配置中缺少本地仓库路径或测试脚本"}
            
            # 检查本地仓库是否存在
            if not os.path.exists(local_repo_path):
                logger.error(f"本地仓库不存在: {local_repo_path}")
                return {"status": "error", "message": f"本地仓库不存在: {local_repo_path}"}
            
            # 检查测试脚本是否存在
            test_script_path = os.path.join(local_repo_path, test_script)
            if not os.path.exists(test_script_path):
                logger.error(f"测试脚本不存在: {test_script_path}")
                return {"status": "error", "message": f"测试脚本不存在: {test_script_path}"}
            
            # 运行测试脚本
            logger.info(f"运行测试脚本: {test_script_path}")
            cmd = f"cd {local_repo_path} && bash {test_script}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # 解析测试结果
            if result.returncode == 0:
                logger.info("测试通过")
                return {
                    "status": "success",
                    "message": "测试通过",
                    "output": result.stdout
                }
            else:
                logger.error(f"测试失败: {result.stderr}")
                return {
                    "status": "error",
                    "message": "测试失败",
                    "output": result.stdout,
                    "error": result.stderr
                }
        
        except Exception as e:
            logger.error(f"测试失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def workflow(self) -> Dict[str, Any]:
        """
        运行工作流程
        
        Returns:
            Dict[str, Any]: 工作流程结果
        """
        try:
            # 检查是否启用自动下载
            if self.config.get("auto_upload", True):
                # 下载最新代码
                logger.info("自动下载最新代码")
                self.download()
            
            # 检查是否启用自动测试
            if self.config.get("auto_test", True):
                # 运行测试
                logger.info("自动运行测试")
                test_result = self.test()
                
                # 如果测试失败且启用自动解决问题
                if test_result["status"] == "error" and self.config.get("auto_solve", True):
                    logger.info("测试失败，尝试自动解决问题")
                    # TODO: 调用ManusProblemSolver解决问题
                    
                    # 重新运行测试
                    logger.info("重新运行测试")
                    test_result = self.test()
            
            # 检查是否启用自动上传
            if self.config.get("auto_upload", True):
                # 上传更改
                logger.info("自动上传更改")
                self.upload("自动工作流程更新")
            
            logger.info("工作流程完成")
            return {"status": "success", "message": "工作流程完成"}
        
        except Exception as e:
            logger.error(f"工作流程失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def config_cmd(self, key=None, value=None) -> Dict[str, Any]:
        """
        配置命令
        
        Args:
            key: 配置项键名，可选
            value: 配置项值，可选
        
        Returns:
            Dict[str, Any]: 配置结果
        """
        try:
            # 如果指定了键和值，设置配置项
            if key and value is not None:
                logger.info(f"设置配置项: {key} = {value}")
                self.config_manager.set(key, value)
                self.config_manager.save()
                return {"status": "success", "message": f"已设置配置项: {key} = {value}"}
            
            # 如果只指定了键，获取配置项
            elif key:
                value = self.config_manager.get(key)
                logger.info(f"获取配置项: {key} = {value}")
                return {"status": "success", "key": key, "value": value}
            
            # 如果没有指定键和值，获取所有配置
            else:
                config = self.config_manager.get_all()
                logger.info("获取所有配置")
                return {"status": "success", "config": config}
        
        except Exception as e:
            logger.error(f"配置命令失败: {e}")
            return {"status": "error", "message": str(e)}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="PowerAutomation CLI")
    parser.add_argument("--config", help="配置文件路径")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 下载命令
    download_parser = subparsers.add_parser("download", help="下载代码")
    download_parser.add_argument("--version", help="版本号")
    
    # 上传命令
    upload_parser = subparsers.add_parser("upload", help="上传更改")
    upload_parser.add_argument("--message", help="提交信息")
    
    # 测试命令
    subparsers.add_parser("test", help="运行测试")
    
    # 工作流程命令
    subparsers.add_parser("workflow", help="运行工作流程")
    
    # 配置命令
    config_parser = subparsers.add_parser("config", help="配置命令")
    config_parser.add_argument("--key", help="配置项键名")
    config_parser.add_argument("--value", help="配置项值")
    
    args = parser.parse_args()
    
    # 创建CLI实例
    cli = CLI(args.config)
    
    # 执行命令
    if args.command == "download":
        result = cli.download(args.version)
        print(f"下载{'成功' if result else '失败'}")
    
    elif args.command == "upload":
        result = cli.upload(args.message)
        print(f"上传{'成功' if result else '失败'}")
    
    elif args.command == "test":
        result = cli.test()
        print(f"测试结果: {result['status']}")
        if result["status"] == "error":
            print(f"错误信息: {result['message']}")
    
    elif args.command == "workflow":
        result = cli.workflow()
        print(f"工作流程结果: {result['status']}")
        if result["status"] == "error":
            print(f"错误信息: {result['message']}")
    
    elif args.command == "config":
        result = cli.config_cmd(args.key, args.value)
        if args.key and args.value is None:
            print(f"{args.key} = {result['value']}")
        elif not args.key:
            import json
            print(json.dumps(result["config"], indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
