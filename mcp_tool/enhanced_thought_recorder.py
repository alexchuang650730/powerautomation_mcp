"""
集成视觉思考记录器与原始思考记录器的增强模块

该模块将VisualThoughtRecorder与ThoughtActionRecorder集成，
提供统一的接口来记录和查询思考与操作，支持自动OCR捕获和手动记录。

作者: Manus AI
日期: 2025-05-28
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# 导入原始记录器和视觉记录器
from .thought_action_recorder import ThoughtActionRecorder
from .visual_thought_recorder import VisualThoughtRecorder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EnhancedThoughtRecorder")

class EnhancedThoughtRecorder:
    """
    增强型思考记录器，集成了原始ThoughtActionRecorder和VisualThoughtRecorder，
    提供统一的接口来记录和查询思考与操作。
    """
    
    def __init__(self, 
                 log_dir: str,
                 enable_visual_capture: bool = True,
                 monitor_regions: Optional[List[Dict[str, Any]]] = None,
                 capture_interval: float = 1.0,
                 ocr_engine: str = "tesseract"):
        """
        初始化增强型思考记录器
        
        Args:
            log_dir: 日志存储目录
            enable_visual_capture: 是否启用视觉捕获
            monitor_regions: 监控区域列表，每个区域是一个字典，包含区域名称、坐标和类型
            capture_interval: 捕获间隔（秒）
            ocr_engine: OCR引擎，支持"tesseract"和"easyocr"
        """
        self.log_dir = log_dir
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 初始化原始思考记录器
        self.thought_action_recorder = ThoughtActionRecorder(log_dir=log_dir)
        
        # 初始化视觉思考记录器（如果启用）
        self.visual_recorder = None
        if enable_visual_capture:
            self.visual_recorder = VisualThoughtRecorder(
                log_dir=log_dir,
                monitor_regions=monitor_regions,
                capture_interval=capture_interval,
                ocr_engine=ocr_engine,
                enable_visual_capture=True,
                thought_action_recorder=self.thought_action_recorder
            )
    
    def record_thought(self, content, thought_type="general", context=None):
        """
        记录思考过程
        
        Args:
            content: 思考内容
            thought_type: 思考类型，如"reasoning"、"decision"、"planning"等
            context: 上下文信息，如当前任务、相关文件等
        """
        return self.thought_action_recorder.record_thought(
            content=content,
            thought_type=thought_type,
            context=context
        )
    
    def record_action(self, action_name, params, result, context=None):
        """
        记录执行的操作
        
        Args:
            action_name: 操作名称
            params: 操作参数
            result: 操作结果
            context: 上下文信息，如当前任务、相关文件等
        """
        return self.thought_action_recorder.record_action(
            action_name=action_name,
            params=params,
            result=result,
            context=context
        )
    
    def get_latest_thoughts(self, limit=10, include_actions=False, filter_type=None):
        """
        获取最近的思考记录
        
        Args:
            limit: 返回的记录数量限制
            include_actions: 是否包含操作记录
            filter_type: 过滤特定类型的记录，如果为None则返回所有类型
            
        Returns:
            最近的思考记录列表
        """
        return self.thought_action_recorder.get_latest_thoughts(
            limit=limit,
            include_actions=include_actions,
            filter_type=filter_type
        )
    
    def start_visual_capture(self):
        """启动视觉捕获"""
        if self.visual_recorder:
            self.visual_recorder._start_monitor()
            logger.info("视觉捕获已启动")
        else:
            logger.warning("视觉记录器未初始化，无法启动视觉捕获")
    
    def stop_visual_capture(self):
        """停止视觉捕获"""
        if self.visual_recorder:
            self.visual_recorder.stop_monitor()
            logger.info("视觉捕获已停止")
        else:
            logger.warning("视觉记录器未初始化，无法停止视觉捕获")
    
    def set_monitor_regions(self, regions):
        """设置监控区域"""
        if self.visual_recorder:
            self.visual_recorder.set_monitor_regions(regions)
        else:
            logger.warning("视觉记录器未初始化，无法设置监控区域")
    
    def add_monitor_region(self, name, bbox, region_type="thought"):
        """添加监控区域"""
        if self.visual_recorder:
            self.visual_recorder.add_monitor_region(name, bbox, region_type)
        else:
            logger.warning("视觉记录器未初始化，无法添加监控区域")
    
    def get_monitor_regions(self):
        """获取监控区域"""
        if self.visual_recorder:
            return self.visual_recorder.get_monitor_regions()
        else:
            logger.warning("视觉记录器未初始化，无法获取监控区域")
            return []
    
    def set_capture_interval(self, interval):
        """设置捕获间隔"""
        if self.visual_recorder:
            self.visual_recorder.set_capture_interval(interval)
        else:
            logger.warning("视觉记录器未初始化，无法设置捕获间隔")
    
    def capture_now(self, region_name=None):
        """立即捕获指定区域"""
        if self.visual_recorder:
            return self.visual_recorder.capture_now(region_name)
        else:
            logger.warning("视觉记录器未初始化，无法执行捕获")
            return None
    
    def take_screenshot(self, region_name=None, save_path=None):
        """截取屏幕并保存"""
        if self.visual_recorder:
            return self.visual_recorder.take_screenshot(region_name, save_path)
        else:
            logger.warning("视觉记录器未初始化，无法截取屏幕")
            return None
    
    def is_visual_capture_enabled(self):
        """检查视觉捕获是否已启用"""
        return self.visual_recorder is not None
    
    def get_ocr_engine_status(self):
        """获取OCR引擎状态"""
        if self.visual_recorder:
            return {
                "engine": self.visual_recorder.ocr_engine_name,
                "initialized": self.visual_recorder.ocr_engine is not None
            }
        else:
            return {
                "engine": None,
                "initialized": False
            }
