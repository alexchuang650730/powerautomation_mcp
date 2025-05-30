"""
跨平台视觉校准工具测试模块

该模块用于测试跨平台视觉校准工具的功能，包括截图、窗口检测、区域选择等。

作者: Manus AI
日期: 2025-05-30
"""

import os
import sys
import unittest
import tempfile
import platform
from unittest.mock import patch, MagicMock
from PIL import Image

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入被测试模块
from mcp_tool.visual_calibrator import (
    VisualCalibrator, 
    WindowsVisualCalibrator, 
    MacVisualCalibrator, 
    get_calibrator
)

class TestVisualCalibratorBase(unittest.TestCase):
    """测试视觉校准器基类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_visual_calibration_")
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_config_default(self):
        """测试加载默认配置"""
        calibrator = VisualCalibrator(output_dir=self.output_dir)
        self.assertEqual(calibrator.config["log_dir"], self.output_dir)
        self.assertFalse(calibrator.simple_mode)
        self.assertFalse(calibrator.manual_regions)
    
    def test_load_config_custom(self):
        """测试加载自定义配置"""
        # 创建测试配置文件
        import json
        with open(self.config_file, 'w') as f:
            json.dump({
                "simple_mode": True,
                "manual_regions": True,
                "calibration_grid_size": 20
            }, f)
        
        calibrator = VisualCalibrator(config_file=self.config_file, output_dir=self.output_dir)
        self.assertEqual(calibrator.config["log_dir"], self.output_dir)
        self.assertTrue(calibrator.simple_mode)
        self.assertTrue(calibrator.manual_regions)
        self.assertEqual(calibrator.config["calibration_grid_size"], 20)
    
    def test_create_calibration_grid(self):
        """测试创建校准网格"""
        # 创建测试图像
        test_img_path = os.path.join(self.temp_dir, "test_img.png")
        img = Image.new('RGB', (800, 600), color='white')
        img.save(test_img_path)
        
        calibrator = VisualCalibrator(output_dir=self.output_dir)
        browser_window = (100, 100, 700, 500)
        grid_path = calibrator.create_calibration_grid(test_img_path, browser_window)
        
        self.assertTrue(os.path.exists(grid_path))
        grid_img = Image.open(grid_path)
        self.assertEqual(grid_img.size, (800, 600))
    
    def test_visualize_detected_regions(self):
        """测试可视化检测区域"""
        # 创建测试图像
        test_img_path = os.path.join(self.temp_dir, "test_img.png")
        img = Image.new('RGB', (800, 600), color='white')
        img.save(test_img_path)
        
        calibrator = VisualCalibrator(output_dir=self.output_dir)
        regions = {
            "work_list": (100, 100, 400, 500),
            "action_list": (500, 100, 700, 500)
        }
        marked_path = calibrator.visualize_detected_regions(test_img_path, regions)
        
        self.assertTrue(os.path.exists(marked_path))
        marked_img = Image.open(marked_path)
        self.assertEqual(marked_img.size, (800, 600))
    
    def test_extract_region_content(self):
        """测试提取区域内容"""
        # 创建测试图像
        test_img_path = os.path.join(self.temp_dir, "test_img.png")
        img = Image.new('RGB', (800, 600), color='white')
        img.save(test_img_path)
        
        calibrator = VisualCalibrator(output_dir=self.output_dir)
        regions = {
            "work_list": (100, 100, 400, 500),
            "action_list": (500, 100, 700, 500)
        }
        region_images = calibrator.extract_region_content(test_img_path, regions)
        
        self.assertEqual(len(region_images), 2)
        for name, path in region_images.items():
            self.assertTrue(os.path.exists(path))
            self.assertIn(name, path)
    
    def test_update_auto_monitor_config(self):
        """测试更新自动监控配置"""
        calibrator = VisualCalibrator(output_dir=self.output_dir)
        regions = {
            "work_list": (100, 100, 400, 500),
            "action_list": (500, 100, 700, 500)
        }
        result = calibrator.update_auto_monitor_config(regions)
        
        self.assertTrue(result)
        config_path = os.path.join(self.output_dir, "auto_web_monitor_config.json")
        self.assertTrue(os.path.exists(config_path))
        
        # 检查配置内容
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(len(config["monitor_regions"]), 2)
        self.assertEqual(config["platform"], platform.system().lower())


class TestWindowsVisualCalibrator(unittest.TestCase):
    """测试Windows视觉校准器"""
    
    @unittest.skipIf(platform.system().lower() != 'windows', "仅在Windows平台运行")
    def test_windows_specific_functions(self):
        """测试Windows特定功能"""
        calibrator = WindowsVisualCalibrator()
        self.assertIsInstance(calibrator, WindowsVisualCalibrator)
    
    @patch('mcp_tool.visual_calibrator.pyautogui')
    def test_capture_screenshot(self, mock_pyautogui):
        """测试捕获屏幕截图"""
        # 模拟pyautogui.screenshot
        mock_pyautogui.screenshot.return_value = None
        
        calibrator = WindowsVisualCalibrator()
        screenshot_path = calibrator.capture_screenshot()
        
        self.assertIsNotNone(screenshot_path)
        mock_pyautogui.screenshot.assert_called_once()
    
    @patch('mcp_tool.visual_calibrator.gw')
    def test_get_active_browser_info(self, mock_gw):
        """测试获取活动浏览器信息"""
        # 模拟gw.getActiveWindow
        mock_window = MagicMock()
        mock_window.title = "Test Browser"
        mock_window.left = 100
        mock_window.top = 100
        mock_window.width = 800
        mock_window.height = 600
        mock_gw.getActiveWindow.return_value = mock_window
        
        calibrator = WindowsVisualCalibrator()
        browser_info = calibrator.get_active_browser_info()
        
        self.assertEqual(browser_info["name"], "Test Browser")
        self.assertEqual(browser_info["position"]["x"], 100)
        self.assertEqual(browser_info["position"]["y"], 100)
        self.assertEqual(browser_info["size"]["width"], 800)
        self.assertEqual(browser_info["size"]["height"], 600)


class TestMacVisualCalibrator(unittest.TestCase):
    """测试Mac视觉校准器"""
    
    @unittest.skipIf(platform.system().lower() != 'darwin', "仅在Mac平台运行")
    def test_mac_specific_functions(self):
        """测试Mac特定功能"""
        calibrator = MacVisualCalibrator()
        self.assertIsInstance(calibrator, MacVisualCalibrator)
    
    @patch('mcp_tool.visual_calibrator.subprocess.run')
    def test_capture_screenshot(self, mock_subprocess_run):
        """测试捕获屏幕截图"""
        # 模拟subprocess.run
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        
        calibrator = MacVisualCalibrator()
        screenshot_path = calibrator.capture_screenshot()
        
        self.assertIsNotNone(screenshot_path)
        mock_subprocess_run.assert_called_once()


class TestFactoryFunction(unittest.TestCase):
    """测试工厂函数"""
    
    @patch('mcp_tool.visual_calibrator.PLATFORM', 'windows')
    def test_get_calibrator_windows(self):
        """测试获取Windows校准器"""
        calibrator = get_calibrator()
        self.assertIsInstance(calibrator, WindowsVisualCalibrator)
    
    @patch('mcp_tool.visual_calibrator.PLATFORM', 'darwin')
    def test_get_calibrator_mac(self):
        """测试获取Mac校准器"""
        calibrator = get_calibrator()
        self.assertIsInstance(calibrator, MacVisualCalibrator)
    
    @patch('mcp_tool.visual_calibrator.PLATFORM', 'linux')
    def test_get_calibrator_unsupported(self):
        """测试获取不支持平台的校准器"""
        calibrator = get_calibrator()
        self.assertIsInstance(calibrator, VisualCalibrator)


if __name__ == '__main__':
    unittest.main()
