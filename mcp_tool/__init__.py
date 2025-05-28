"""
PowerAutomation MCP Tool - 多智能体通信协议工具包

该工具包用于支持PowerAutomation项目的自动化流程，包括：
1. 自动记录Manus所有步骤思考过程及动作
2. 在release时自动下载代码到端侧Mac对应目录并上传GitHub
3. 在端侧执行测试步骤要求的动作，并将问题更新到README中
4. 驱动Manus进行问题定位、修复和测试

作者: Manus AI
日期: 2025-05-28
"""

from .thought_action_recorder import ThoughtActionRecorder

__all__ = ['ThoughtActionRecorder']
