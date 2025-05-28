"""
端到端集成测试脚本

该脚本用于测试MCP工具的端到端流程，包括：
1. 初始化和配置
2. 检查并下载release
3. 运行测试并收集问题
4. 分析并解决问题
5. 上传更改
6. 生成报告

作者: Manus AI
日期: 2025-05-28
"""

import os
import sys
import time
import json
import argparse
import logging

# 添加父目录到系统路径，以便导入mcp_tool包
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tool.mcp_central_coordinator import MCPCentralCoordinator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EndToEndTest")

def run_end_to_end_test(config_path=None, tag_name=None, auto_upload=False):
    """
    运行端到端测试
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认配置
        tag_name: 指定的标签名称，如果为None则使用最新的release
        auto_upload: 是否自动上传更改
    """
    logger.info("开始端到端测试...")
    
    # 初始化协调器
    logger.info(f"初始化协调器，配置文件: {config_path or '默认配置'}")
    coordinator = MCPCentralCoordinator(config_path=config_path)
    
    # 运行完整工作流程
    logger.info(f"运行完整工作流程，tag_name={tag_name}, auto_upload={auto_upload}")
    workflow_result = coordinator.run_full_workflow(tag_name=tag_name, auto_upload=auto_upload)
    
    # 生成工作流程报告
    logger.info("生成工作流程报告")
    report_result = coordinator.generate_workflow_report(workflow_result)
    
    if report_result["success"]:
        logger.info(f"成功生成工作流程报告: {report_result['report_path']}")
    else:
        logger.error(f"生成工作流程报告失败: {report_result.get('error')}")
    
    # 输出总体结果
    if workflow_result["success"]:
        logger.info("端到端测试成功完成")
    else:
        logger.error("端到端测试失败")
        
        # 查找失败步骤
        failed_steps = []
        for step, result in workflow_result.get("steps", {}).items():
            if not result.get("success") and not result.get("skipped"):
                failed_steps.append(step)
        
        logger.error(f"失败步骤: {', '.join(failed_steps)}")
    
    return workflow_result, report_result

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="PowerAutomation MCP工具端到端测试")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--tag", help="指定的release标签名称")
    parser.add_argument("--upload", action="store_true", help="是否自动上传更改")
    
    args = parser.parse_args()
    
    run_end_to_end_test(
        config_path=args.config,
        tag_name=args.tag,
        auto_upload=args.upload
    )

if __name__ == "__main__":
    main()
