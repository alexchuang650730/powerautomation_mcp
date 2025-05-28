"""
测试思考与操作记录器模块

该脚本用于测试ThoughtActionRecorder模块的功能，包括：
1. 记录思考和操作
2. 获取会话日志
3. 搜索日志
4. 导出会话

作者: Manus AI
日期: 2025-05-28
"""

import os
import sys
import time
import json

# 添加父目录到系统路径，以便导入mcp_tool包
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tool.thought_action_recorder import ThoughtActionRecorder

def test_recorder():
    """测试ThoughtActionRecorder的基本功能"""
    print("开始测试ThoughtActionRecorder...")
    
    # 创建测试目录
    test_log_dir = os.path.join(os.getcwd(), "test_logs")
    os.makedirs(test_log_dir, exist_ok=True)
    
    # 初始化记录器
    recorder = ThoughtActionRecorder(log_dir=test_log_dir)
    print(f"记录器初始化完成，日志目录: {test_log_dir}")
    
    # 测试记录思考
    print("\n测试记录思考...")
    thought1 = recorder.record_thought("这是第一个测试思考")
    thought2 = recorder.record_thought("这是第二个测试思考", {"context_key": "context_value"})
    
    print(f"记录了思考1: {thought1['content']}")
    print(f"记录了思考2: {thought2['content']} (带上下文)")
    
    # 测试记录操作
    print("\n测试记录操作...")
    action1 = recorder.record_action(
        "test_action", 
        {"param1": "value1", "param2": 123},
        {"success": True, "message": "操作成功"}
    )
    
    action2 = recorder.record_action(
        "another_action", 
        {"file": "test.txt", "mode": "write"},
        {"success": False, "error": "文件不存在"}
    )
    
    print(f"记录了操作1: {action1['action_type']}")
    print(f"记录了操作2: {action2['action_type']}")
    
    # 测试获取会话日志
    print("\n测试获取会话日志...")
    logs = recorder.get_session_logs()
    
    print(f"获取到会话 {logs['session_id']} 的日志:")
    print(f"- 思考数量: {len(logs['thoughts'])}")
    print(f"- 操作数量: {len(logs['actions'])}")
    
    # 测试搜索日志
    print("\n测试搜索日志...")
    search_results = recorder.search_logs("测试")
    
    print(f"搜索'测试'的结果:")
    print(f"- 匹配的思考: {len(search_results['thoughts'])}")
    print(f"- 匹配的操作: {len(search_results['actions'])}")
    
    # 测试导出会话
    print("\n测试导出会话...")
    export_result = recorder.export_session(format="json")
    
    if export_result["success"]:
        print(f"成功导出会话到: {export_result['file']}")
    else:
        print(f"导出会话失败: {export_result.get('error')}")
    
    print("\n测试完成!")
    return recorder

if __name__ == "__main__":
    recorder = test_recorder()
    
    # 打印最新的思考和操作
    print("\n最新的思考:")
    for thought in recorder.get_latest_thoughts(2):
        print(f"- {thought['datetime']}: {thought['content']}")
    
    print("\n最新的操作:")
    for action in recorder.get_latest_actions(2):
        print(f"- {action['datetime']}: {action['action_type']}")
