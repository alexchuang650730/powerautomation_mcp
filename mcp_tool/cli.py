"""
PowerAutomation MCP工具 - 命令行接口

该模块提供命令行接口，用于使用MCP工具的各种功能。

作者: Manus AI
日期: 2025-05-28
"""

import os
import sys
import argparse
import logging
import json
from typing import Dict, Any, Optional

# 添加父目录到系统路径，以便导入mcp_tool包
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tool.mcp_central_coordinator import MCPCentralCoordinator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCP-CLI")

def get_config_path(args) -> str:
    """
    获取配置文件路径
    
    Args:
        args: 命令行参数
        
    Returns:
        配置文件路径
    """
    # 优先使用命令行参数
    if hasattr(args, 'config') and args.config:
        return args.config
    
    # 其次使用环境变量
    if 'MCP_CONFIG_PATH' in os.environ:
        return os.environ['MCP_CONFIG_PATH']
    
    # 最后使用默认路径
    default_path = os.path.expanduser("~/.powerautomation_mcp/config.json")
    
    # 如果默认路径不存在，创建一个
    if not os.path.exists(default_path):
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        
        # 创建默认配置
        default_config = {
            "local_repo_path": "/Users/alexchuang/powerassistant/powerautomation",
            "github_repo": "alexchuang650730/powerautomation",
            "ssh_key_path": "~/.ssh/id_ed25519",
            "test_script": "start_and_test.sh",
            "readme_path": "README.md",
            "auto_upload": True,
            "auto_test": True,
            "auto_solve": True
        }
        
        with open(default_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created default configuration at {default_path}")
    
    return default_path

def cmd_config(args) -> None:
    """
    配置命令处理函数
    
    Args:
        args: 命令行参数
    """
    config_path = get_config_path(args)
    
    # 获取配置项
    if args.get:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            if args.get in config:
                print(config[args.get])
            else:
                logger.error(f"Configuration item '{args.get}' not found")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Error reading configuration: {e}")
            sys.exit(1)
    
    # 设置配置项
    elif args.set and args.value:
        try:
            # 读取现有配置
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 更新配置
            config[args.set] = args.value
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Updated configuration item '{args.set}' to '{args.value}'")
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            sys.exit(1)
    
    # 显示所有配置
    else:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            print(json.dumps(config, ensure_ascii=False, indent=2))
        except Exception as e:
            logger.error(f"Error reading configuration: {e}")
            sys.exit(1)

def cmd_download(args) -> None:
    """
    下载命令处理函数
    
    Args:
        args: 命令行参数
    """
    config_path = get_config_path(args)
    
    # 初始化协调器
    coordinator = MCPCentralCoordinator(config_path=config_path)
    
    # 检查并下载release
    download_result = coordinator.check_and_download_release(tag_name=args.tag)
    
    if download_result["success"]:
        logger.info(f"Successfully downloaded release: {download_result.get('tag_name')}")
        logger.info(f"Local path: {download_result.get('local_path')}")
    else:
        logger.error(f"Failed to download release: {download_result.get('error')}")
        sys.exit(1)

def cmd_test(args) -> None:
    """
    测试命令处理函数
    
    Args:
        args: 命令行参数
    """
    config_path = get_config_path(args)
    
    # 初始化协调器
    coordinator = MCPCentralCoordinator(config_path=config_path)
    
    # 运行测试并收集问题
    test_result = coordinator.run_tests_and_collect_issues()
    
    if test_result["success"]:
        logger.info("Successfully ran tests and collected issues")
        
        issues = test_result.get("issues", [])
        logger.info(f"Found {len(issues)} issues")
        
        for i, issue in enumerate(issues, 1):
            logger.info(f"Issue {i}: {issue.get('type', '').upper()} in {issue.get('file', '')}")
    else:
        logger.error(f"Failed to run tests: {test_result.get('error')}")
        sys.exit(1)

def cmd_solve(args) -> None:
    """
    解决问题命令处理函数
    
    Args:
        args: 命令行参数
    """
    config_path = get_config_path(args)
    
    # 初始化协调器
    coordinator = MCPCentralCoordinator(config_path=config_path)
    
    # 分析并解决问题
    solution_result = coordinator.analyze_and_solve_issues()
    
    if solution_result["success"]:
        logger.info("Successfully analyzed and solved issues")
        
        process_result = solution_result.get("process_result", {})
        issues_count = process_result.get("issues_count", 0)
        
        logger.info(f"Processed {issues_count} issues")
        
        if "results_file" in process_result:
            logger.info(f"Results saved to: {process_result['results_file']}")
        if "summary_file" in process_result:
            logger.info(f"Summary report saved to: {process_result['summary_file']}")
    else:
        logger.error(f"Failed to solve issues: {solution_result.get('error')}")
        sys.exit(1)

def cmd_upload(args) -> None:
    """
    上传命令处理函数
    
    Args:
        args: 命令行参数
    """
    config_path = get_config_path(args)
    
    # 初始化协调器
    coordinator = MCPCentralCoordinator(config_path=config_path)
    
    # 上传更改
    upload_result = coordinator.upload_changes(commit_message=args.message)
    
    if upload_result["success"]:
        logger.info("Successfully uploaded changes")
        logger.info(f"Commit message: {upload_result.get('commit_message')}")
    else:
        logger.error(f"Failed to upload changes: {upload_result.get('error')}")
        sys.exit(1)

def cmd_workflow(args) -> None:
    """
    工作流程命令处理函数
    
    Args:
        args: 命令行参数
    """
    config_path = get_config_path(args)
    
    # 初始化协调器
    coordinator = MCPCentralCoordinator(config_path=config_path)
    
    # 运行完整工作流程
    workflow_result = coordinator.run_full_workflow(
        tag_name=args.tag,
        auto_upload=not args.no_upload
    )
    
    # 生成工作流程报告
    report_result = coordinator.generate_workflow_report(workflow_result)
    
    if workflow_result["success"]:
        logger.info("Successfully completed workflow")
        
        if report_result["success"]:
            logger.info(f"Workflow report saved to: {report_result['report_path']}")
    else:
        logger.error("Workflow failed")
        
        # 查找失败步骤
        failed_steps = []
        for step, result in workflow_result.get("steps", {}).items():
            if not result.get("success") and not result.get("skipped"):
                failed_steps.append(step)
        
        logger.error(f"Failed steps: {', '.join(failed_steps)}")
        
        if report_result["success"]:
            logger.info(f"Detailed failure report saved to: {report_result['report_path']}")
        
        sys.exit(1)

def cmd_reset(args) -> None:
    """
    重置命令处理函数
    
    Args:
        args: 命令行参数
    """
    config_path = get_config_path(args)
    
    try:
        # 读取配置
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        local_repo_path = config.get("local_repo_path")
        
        if not local_repo_path:
            logger.error("Local repository path not found in configuration")
            sys.exit(1)
        
        # 清理日志目录
        logs_dir = os.path.join(local_repo_path, "logs")
        if os.path.exists(logs_dir):
            logger.info(f"Cleaning logs directory: {logs_dir}")
            for file in os.listdir(logs_dir):
                file_path = os.path.join(logs_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        
        # 清理报告目录
        reports_dir = os.path.join(local_repo_path, "reports")
        if os.path.exists(reports_dir):
            logger.info(f"Cleaning reports directory: {reports_dir}")
            for file in os.listdir(reports_dir):
                file_path = os.path.join(reports_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        
        # 清理解决方案目录
        solutions_dir = os.path.join(local_repo_path, "manus_solutions")
        if os.path.exists(solutions_dir):
            logger.info(f"Cleaning solutions directory: {solutions_dir}")
            for file in os.listdir(solutions_dir):
                file_path = os.path.join(solutions_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        
        logger.info("Successfully reset MCP tool state")
    except Exception as e:
        logger.error(f"Error resetting MCP tool state: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="PowerAutomation MCP工具命令行接口")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 配置命令
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_parser.add_argument("--get", help="获取配置项")
    config_parser.add_argument("--set", help="设置配置项")
    config_parser.add_argument("--value", help="配置项的值")
    
    # 下载命令
    download_parser = subparsers.add_parser("download", help="检查并下载release")
    download_parser.add_argument("--tag", help="指定的release标签名称")
    
    # 测试命令
    test_parser = subparsers.add_parser("test", help="运行测试并收集问题")
    
    # 解决问题命令
    solve_parser = subparsers.add_parser("solve", help="分析并解决问题")
    
    # 上传命令
    upload_parser = subparsers.add_parser("upload", help="上传更改")
    upload_parser.add_argument("--message", default="自动更新", help="提交信息")
    
    # 工作流程命令
    workflow_parser = subparsers.add_parser("workflow", help="运行完整工作流程")
    workflow_parser.add_argument("--tag", help="指定的release标签名称")
    workflow_parser.add_argument("--no-upload", action="store_true", help="禁用自动上传")
    
    # 重置命令
    reset_parser = subparsers.add_parser("reset", help="重置工具状态")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # 处理命令
    if args.command == "config":
        cmd_config(args)
    elif args.command == "download":
        cmd_download(args)
    elif args.command == "test":
        cmd_test(args)
    elif args.command == "solve":
        cmd_solve(args)
    elif args.command == "upload":
        cmd_upload(args)
    elif args.command == "workflow":
        cmd_workflow(args)
    elif args.command == "reset":
        cmd_reset(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
