"""
增强版MCP命令行接口 - 支持自然语言任务指令

该模块扩展了原有的命令行接口，添加了对自然语言任务指令的支持，
使用户能够通过简单的自然语言命令执行复杂的任务。

作者: Manus AI
日期: 2025-05-28
"""

import argparse
import sys
import logging
import json
from typing import Dict, List, Any, Optional

# 导入增强版MCP中央协调器
from mcp_tool.planner_mcp_coordinator import PlannerMCPCentralCoordinator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("enhanced_cli")

def execute_command(args):
    """
    执行自然语言任务指令
    
    Args:
        args: 命令行参数
    """
    # 初始化增强版MCP中央协调器
    coordinator = PlannerMCPCentralCoordinator(config_path=args.config)
    
    # 执行任务
    result = coordinator.execute_task(args.task)
    
    # 输出结果
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"任务执行结果: {result['status']}")
        print(f"消息: {result.get('message', '')}")
        
        if result.get('error'):
            print(f"错误: {result['error']}")
        
        if 'steps' in result:
            print("\n步骤执行情况:")
            for step, status in result['steps'].items():
                print(f"  - {step}: {status}")

def monitor_command(args):
    """
    启动任务监控
    
    Args:
        args: 命令行参数
    """
    # 初始化增强版MCP中央协调器
    coordinator = PlannerMCPCentralCoordinator(config_path=args.config)
    
    # 定义回调函数
    def callback(result):
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"任务 '{result['task_type']}' 执行结果: {result['status']}")
            print(f"消息: {result.get('message', '')}")
    
    # 启动监控
    print(f"启动任务监控，间隔: {args.interval}秒")
    print("按Ctrl+C停止监控")
    
    try:
        # 启动监控并等待
        thread = coordinator.start_task_monitoring(interval=args.interval, callback=callback)
        thread.join()
    except KeyboardInterrupt:
        print("\n监控已停止")

def main():
    """
    命令行入口函数
    """
    parser = argparse.ArgumentParser(description="PowerAutomation MCP工具 - 增强版命令行接口")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # execute命令 - 执行自然语言任务指令
    execute_parser = subparsers.add_parser("execute", help="执行自然语言任务指令")
    execute_parser.add_argument("task", help="任务描述，如'自动记录Manus所有步骤思考过程及动作'")
    execute_parser.add_argument("--config", help="配置文件路径")
    execute_parser.add_argument("--json", action="store_true", help="以JSON格式输出结果")
    execute_parser.set_defaults(func=execute_command)
    
    # monitor命令 - 启动任务监控
    monitor_parser = subparsers.add_parser("monitor", help="启动任务监控")
    monitor_parser.add_argument("--interval", type=float, default=3600.0, help="监控间隔（秒）")
    monitor_parser.add_argument("--config", help="配置文件路径")
    monitor_parser.add_argument("--json", action="store_true", help="以JSON格式输出结果")
    monitor_parser.set_defaults(func=monitor_command)
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有指定命令，显示帮助信息
    if not args.command:
        parser.print_help()
        return
    
    # 执行对应的命令
    args.func(args)

if __name__ == "__main__":
    main()
