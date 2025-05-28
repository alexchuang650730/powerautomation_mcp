"""
测试视觉思考记录器模块

该脚本用于测试VisualThoughtRecorder和EnhancedThoughtRecorder的功能，
包括屏幕捕获、OCR识别、思考分析和记录等。

作者: Manus AI
日期: 2025-05-28
"""

import os
import time
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# 导入测试目标
from mcp_tool.visual_thought_recorder import VisualThoughtRecorder
from mcp_tool.enhanced_thought_recorder import EnhancedThoughtRecorder
from mcp_tool.thought_action_recorder import ThoughtActionRecorder

class TestVisualThoughtRecorder(unittest.TestCase):
    """测试VisualThoughtRecorder类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        
        # 模拟OCR引擎
        self.mock_ocr = MagicMock()
        self.mock_ocr.image_to_string.return_value = "测试思考内容"
        
        # 模拟屏幕捕获工具
        self.mock_grabber = MagicMock()
        self.mock_grabber.grab.return_value = MagicMock()
        
        # 模拟ThoughtActionRecorder
        self.mock_recorder = MagicMock()
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.test_dir)
    
    @patch('mcp_tool.visual_thought_recorder.VisualThoughtRecorder._init_ocr_engine')
    @patch('mcp_tool.visual_thought_recorder.VisualThoughtRecorder._init_screen_grabber')
    def test_initialization(self, mock_init_grabber, mock_init_ocr):
        """测试初始化"""
        # 设置模拟返回值
        mock_init_ocr.return_value = self.mock_ocr
        mock_init_grabber.return_value = self.mock_grabber
        
        # 创建VisualThoughtRecorder实例
        recorder = VisualThoughtRecorder(
            log_dir=self.test_dir,
            enable_visual_capture=False,  # 禁用自动捕获，以便手动测试
            thought_action_recorder=self.mock_recorder
        )
        
        # 验证初始化
        self.assertEqual(recorder.log_dir, self.test_dir)
        self.assertEqual(recorder.ocr_engine, self.mock_ocr)
        self.assertEqual(recorder.screen_grabber, self.mock_grabber)
        self.assertEqual(recorder.thought_action_recorder, self.mock_recorder)
        self.assertFalse(recorder.enable_visual_capture)
    
    @patch('mcp_tool.visual_thought_recorder.VisualThoughtRecorder._init_ocr_engine')
    @patch('mcp_tool.visual_thought_recorder.VisualThoughtRecorder._init_screen_grabber')
    def test_perform_ocr(self, mock_init_grabber, mock_init_ocr):
        """测试OCR识别"""
        # 设置模拟返回值
        mock_init_ocr.return_value = self.mock_ocr
        mock_init_grabber.return_value = self.mock_grabber
        
        # 创建VisualThoughtRecorder实例
        recorder = VisualThoughtRecorder(
            log_dir=self.test_dir,
            enable_visual_capture=False,
            thought_action_recorder=self.mock_recorder
        )
        
        # 执行OCR识别
        image = MagicMock()
        result = recorder._perform_ocr(image)
        
        # 验证结果
        self.assertEqual(result, "测试思考内容")
        self.mock_ocr.image_to_string.assert_called_once()
    
    @patch('mcp_tool.visual_thought_recorder.VisualThoughtRecorder._init_ocr_engine')
    @patch('mcp_tool.visual_thought_recorder.VisualThoughtRecorder._init_screen_grabber')
    def test_process_thought_text(self, mock_init_grabber, mock_init_ocr):
        """测试处理思考文本"""
        # 设置模拟返回值
        mock_init_ocr.return_value = self.mock_ocr
        mock_init_grabber.return_value = self.mock_grabber
        
        # 创建VisualThoughtRecorder实例
        recorder = VisualThoughtRecorder(
            log_dir=self.test_dir,
            enable_visual_capture=False,
            thought_action_recorder=self.mock_recorder
        )
        
        # 模拟_analyze_thought_text方法
        recorder._analyze_thought_text = MagicMock(return_value=("reasoning", "分析问题：测试内容"))
        
        # 处理思考文本
        recorder._process_thought_text("分析问题：测试内容", time.time())
        
        # 验证ThoughtActionRecorder.record_thought被调用
        self.mock_recorder.record_thought.assert_called_once_with(
            "分析问题：测试内容",
            thought_type="reasoning"
        )
    
    @patch('mcp_tool.visual_thought_recorder.VisualThoughtRecorder._init_ocr_engine')
    @patch('mcp_tool.visual_thought_recorder.VisualThoughtRecorder._init_screen_grabber')
    def test_capture_now(self, mock_init_grabber, mock_init_ocr):
        """测试立即捕获"""
        # 设置模拟返回值
        mock_init_ocr.return_value = self.mock_ocr
        mock_init_grabber.return_value = self.mock_grabber
        
        # 创建VisualThoughtRecorder实例
        recorder = VisualThoughtRecorder(
            log_dir=self.test_dir,
            enable_visual_capture=False,
            thought_action_recorder=self.mock_recorder
        )
        
        # 模拟方法
        recorder._perform_ocr = MagicMock(return_value="测试捕获内容")
        recorder._clean_text = MagicMock(return_value="测试捕获内容")
        recorder._process_recognized_text = MagicMock()
        
        # 执行立即捕获
        result = recorder.capture_now()
        
        # 验证结果
        self.assertIsNotNone(result)
        self.mock_grabber.grab.assert_called()
        recorder._perform_ocr.assert_called()
        recorder._process_recognized_text.assert_called()


class TestEnhancedThoughtRecorder(unittest.TestCase):
    """测试EnhancedThoughtRecorder类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.test_dir)
    
    @patch('mcp_tool.enhanced_thought_recorder.ThoughtActionRecorder')
    @patch('mcp_tool.enhanced_thought_recorder.VisualThoughtRecorder')
    def test_initialization(self, MockVisualRecorder, MockThoughtRecorder):
        """测试初始化"""
        # 创建模拟实例
        mock_thought_recorder = MagicMock()
        mock_visual_recorder = MagicMock()
        
        # 设置模拟返回值
        MockThoughtRecorder.return_value = mock_thought_recorder
        MockVisualRecorder.return_value = mock_visual_recorder
        
        # 创建EnhancedThoughtRecorder实例
        recorder = EnhancedThoughtRecorder(
            log_dir=self.test_dir,
            enable_visual_capture=True
        )
        
        # 验证初始化
        self.assertEqual(recorder.log_dir, self.test_dir)
        self.assertEqual(recorder.thought_action_recorder, mock_thought_recorder)
        self.assertEqual(recorder.visual_recorder, mock_visual_recorder)
        
        # 验证构造函数调用
        MockThoughtRecorder.assert_called_once_with(log_dir=self.test_dir)
        MockVisualRecorder.assert_called_once()
    
    @patch('mcp_tool.enhanced_thought_recorder.ThoughtActionRecorder')
    @patch('mcp_tool.enhanced_thought_recorder.VisualThoughtRecorder')
    def test_record_thought(self, MockVisualRecorder, MockThoughtRecorder):
        """测试记录思考"""
        # 创建模拟实例
        mock_thought_recorder = MagicMock()
        mock_visual_recorder = MagicMock()
        
        # 设置模拟返回值
        MockThoughtRecorder.return_value = mock_thought_recorder
        MockVisualRecorder.return_value = mock_visual_recorder
        
        # 创建EnhancedThoughtRecorder实例
        recorder = EnhancedThoughtRecorder(
            log_dir=self.test_dir,
            enable_visual_capture=True
        )
        
        # 记录思考
        recorder.record_thought("测试思考", thought_type="reasoning")
        
        # 验证ThoughtActionRecorder.record_thought被调用
        mock_thought_recorder.record_thought.assert_called_once_with(
            content="测试思考",
            thought_type="reasoning",
            context=None
        )
    
    @patch('mcp_tool.enhanced_thought_recorder.ThoughtActionRecorder')
    @patch('mcp_tool.enhanced_thought_recorder.VisualThoughtRecorder')
    def test_visual_capture_control(self, MockVisualRecorder, MockThoughtRecorder):
        """测试视觉捕获控制"""
        # 创建模拟实例
        mock_thought_recorder = MagicMock()
        mock_visual_recorder = MagicMock()
        
        # 设置模拟返回值
        MockThoughtRecorder.return_value = mock_thought_recorder
        MockVisualRecorder.return_value = mock_visual_recorder
        
        # 创建EnhancedThoughtRecorder实例
        recorder = EnhancedThoughtRecorder(
            log_dir=self.test_dir,
            enable_visual_capture=True
        )
        
        # 启动视觉捕获
        recorder.start_visual_capture()
        mock_visual_recorder._start_monitor.assert_called_once()
        
        # 停止视觉捕获
        recorder.stop_visual_capture()
        mock_visual_recorder.stop_monitor.assert_called_once()
        
        # 设置监控区域
        test_regions = [{"name": "test", "bbox": (0, 0, 100, 100), "type": "thought"}]
        recorder.set_monitor_regions(test_regions)
        mock_visual_recorder.set_monitor_regions.assert_called_once_with(test_regions)


if __name__ == '__main__':
    unittest.main()
