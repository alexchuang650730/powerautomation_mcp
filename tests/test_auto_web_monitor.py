"""
自动网页监控与抓取模块测试

该测试文件用于测试AutoWebMonitor模块的功能，
包括URL检测、页面抓取和内容分析等功能。

作者: Manus AI
日期: 2025-05-29
"""

import os
import sys
import unittest
import tempfile
import shutil
import time
import json
from unittest.mock import MagicMock, patch

# 导入被测模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_tool.auto_web_monitor import AutoWebMonitor, get_instance

class TestAutoWebMonitor(unittest.TestCase):
    """测试AutoWebMonitor类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, "test_config.json")
        
        # 创建测试配置
        self.test_config = {
            "target_url": "https://manus.im",
            "capture_interval": 1.0,
            "log_dir": self.test_dir,
            "browser_check_interval": 0.5
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_config, f)
        
        # 创建测试实例
        self.monitor = AutoWebMonitor(self.config_file)
    
    def tearDown(self):
        """测试后清理"""
        # 停止监控
        if hasattr(self, 'monitor') and self.monitor.running:
            self.monitor.stop_monitoring()
        
        # 删除临时目录
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """测试初始化"""
        # 验证配置加载
        self.assertEqual(self.monitor.config["target_url"], "https://manus.im")
        self.assertEqual(self.monitor.config["capture_interval"], 1.0)
        self.assertEqual(self.monitor.config["log_dir"], self.test_dir)
        
        # 验证初始状态
        self.assertFalse(self.monitor.running)
        self.assertIsNone(self.monitor.monitor_thread)
    
    def test_start_stop_monitoring(self):
        """测试开始和停止监控"""
        # 开始监控
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.running)
        self.assertIsNotNone(self.monitor.monitor_thread)
        
        # 停止监控
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.running)
    
    @patch('mcp_tool.auto_web_monitor.AutoWebMonitor._get_current_browser_url')
    def test_url_detection(self, mock_get_url):
        """测试URL检测"""
        # 模拟返回目标URL
        mock_get_url.return_value = "https://manus.im/dashboard"
        
        # 手动调用监控循环的单次迭代，而不是整个循环
        with patch('mcp_tool.auto_web_monitor.AutoWebMonitor._capture_page_content') as mock_capture:
            # 设置running为True，但确保只执行一次循环
            self.monitor.running = True
            
            # 直接调用单次检测逻辑，而不是整个循环
            current_url = self.monitor._get_current_browser_url()
            if current_url and self.monitor.target_url_pattern.search(current_url):
                self.monitor._capture_page_content(current_url)
            
            # 验证捕获方法被调用
            mock_capture.assert_called_once_with("https://manus.im/dashboard")
        
        # 模拟返回非目标URL
        mock_get_url.return_value = "https://example.com"
        
        # 再次测试单次检测逻辑
        with patch('mcp_tool.auto_web_monitor.AutoWebMonitor._capture_page_content') as mock_capture:
            current_url = self.monitor._get_current_browser_url()
            if current_url and self.monitor.target_url_pattern.search(current_url):
                self.monitor._capture_page_content(current_url)
            
            # 验证捕获方法未被调用
            mock_capture.assert_not_called()
    
    @patch('mcp_tool.auto_web_monitor.AutoWebMonitor._get_url_from_os_command')
    def test_get_browser_url(self, mock_os_command):
        """测试获取浏览器URL"""
        # 模拟操作系统命令返回URL
        mock_os_command.return_value = "https://manus.im/tasks"
        
        # 调用方法
        url = self.monitor._get_current_browser_url()
        
        # 验证结果
        self.assertEqual(url, "https://manus.im/tasks")
    
    @patch('mcp_tool.auto_web_monitor.subprocess.run')
    @patch('mcp_tool.auto_web_monitor.sys.platform', 'darwin')
    def test_get_url_from_os_command_macos(self, mock_run):
        """测试在macOS上获取URL"""
        # 模拟Chrome返回URL
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "https://manus.im/dashboard\n"
        mock_run.return_value = mock_process
        
        # 调用方法
        url = self.monitor._get_url_from_os_command()
        
        # 验证结果
        self.assertEqual(url, "https://manus.im/dashboard")
        
        # 验证调用了正确的命令
        mock_run.assert_called_with(
            """osascript -e 'tell application "Google Chrome" to get URL of active tab of front window'""",
            shell=True, capture_output=True, text=True
        )
    
    @patch('mcp_tool.auto_web_monitor.subprocess.run')
    @patch('mcp_tool.auto_web_monitor.sys.platform', 'win32')
    def test_get_url_from_os_command_windows(self, mock_run):
        """测试在Windows上获取URL"""
        # 模拟PowerShell返回窗口标题
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Manus.im - Dashboard - Google Chrome\n"
        mock_run.return_value = mock_process
        
        # 调用方法
        url = self.monitor._get_url_from_os_command()
        
        # 验证结果
        self.assertEqual(url, "https://manus.im/")
    
    @patch('mcp_tool.auto_web_monitor.requests.get')
    def test_extract_page_content(self, mock_get):
        """测试提取页面内容"""
        # 模拟请求响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <div class="work-list">
                    <div>任务1</div>
                    <div>任务2</div>
                </div>
                <div class="action-list">
                    <div>操作1</div>
                    <div>操作2</div>
                </div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # 调用方法
        with patch('mcp_tool.auto_web_monitor.AutoWebMonitor._parse_html_content') as mock_parse:
            self.monitor._extract_page_content("https://manus.im", "20250529_123456")
            
            # 验证解析方法被调用
            mock_parse.assert_called_once()
            self.assertEqual(mock_parse.call_args[0][0], mock_response.text)
    
    def test_parse_html_content(self):
        """测试解析HTML内容"""
        # 测试HTML
        html_content = """
        <html>
            <body>
                <div class="work-list">
                    <div>任务1</div>
                    <div>任务2</div>
                </div>
                <div class="action-list">
                    <div>操作1</div>
                    <div>操作2</div>
                </div>
            </body>
        </html>
        """
        
        # 调用方法
        timestamp = "20250529_123456"
        self.monitor._parse_html_content(html_content, timestamp)
        
        # 验证文件创建
        work_list_path = os.path.join(self.test_dir, f"work_list_html_{timestamp}.txt")
        action_list_path = os.path.join(self.test_dir, f"action_list_html_{timestamp}.txt")
        
        self.assertTrue(os.path.exists(work_list_path))
        self.assertTrue(os.path.exists(action_list_path))
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # 获取两个实例
        instance1 = get_instance(self.config_file)
        instance2 = get_instance()
        
        # 验证是同一个实例
        self.assertIs(instance1, instance2)

if __name__ == "__main__":
    unittest.main()
