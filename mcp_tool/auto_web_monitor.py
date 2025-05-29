"""
自动网页监控与抓取模块 - AutoWebMonitor

该模块用于自动检测浏览器是否访问了特定网站（如https://manus.im/），
并在访问时自动截取工作列表和操作列表。不依赖GUI界面，适合在各种环境下运行。

作者: Manus AI
日期: 2025-05-29
"""

import os
import sys
import json
import time
import logging
import re
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import subprocess
import requests
from PIL import Image
import tempfile

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AutoWebMonitor")

class AutoWebMonitor:
    """自动网页监控与抓取类"""
    
    def __init__(self, config_file=None):
        """
        初始化自动网页监控器
        
        Args:
            config_file: 配置文件路径，可选
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.running = False
        self.monitor_thread = None
        self.last_capture_time = 0
        self.target_url_pattern = re.compile(r'https?://manus\.im')
        
        # 创建日志目录
        os.makedirs(self.config.get("log_dir", os.path.expanduser("~/mcp_logs")), exist_ok=True)
        
        logger.info("自动网页监控器初始化完成")
    
    def _load_config(self) -> Dict:
        """
        加载配置
        
        Returns:
            Dict: 配置字典
        """
        default_config = {
            "target_url": "https://manus.im",
            "capture_interval": 2.0,  # 捕获间隔（秒）
            "log_dir": os.path.expanduser("~/mcp_logs"),
            "browser_check_interval": 1.0,  # 浏览器检查间隔（秒）
            "work_list_selector": ".work-list-container",  # 工作列表的CSS选择器
            "action_list_selector": ".action-list-container"  # 操作列表的CSS选择器
        }
        
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"已加载配置文件: {self.config_file}")
                return {**default_config, **config}  # 合并默认配置和文件配置
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        
        return default_config
    
    def _save_config(self) -> bool:
        """
        保存配置
        
        Returns:
            bool: 是否成功保存
        """
        if not self.config_file:
            self.config_file = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                "auto_web_monitor_config.json"
            )
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存配置文件: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def start_monitoring(self):
        """开始监控浏览器"""
        if self.running:
            logger.warning("监控已在运行中")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("开始监控浏览器")
    
    def stop_monitoring(self):
        """停止监控浏览器"""
        if not self.running:
            logger.warning("监控未在运行")
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        logger.info("停止监控浏览器")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 检查当前浏览器URL
                current_url = self._get_current_browser_url()
                
                # 如果URL匹配目标网站
                if current_url and self.target_url_pattern.search(current_url):
                    logger.info(f"检测到目标网站: {current_url}")
                    
                    # 检查是否需要捕获（根据时间间隔）
                    current_time = time.time()
                    if current_time - self.last_capture_time >= self.config.get("capture_interval", 2.0):
                        self._capture_page_content(current_url)
                        self.last_capture_time = current_time
                
                # 等待下一次检查
                time.sleep(self.config.get("browser_check_interval", 1.0))
            
            except Exception as e:
                logger.error(f"监控过程中发生错误: {e}")
                time.sleep(5.0)  # 发生错误后等待较长时间再重试
    
    def _get_current_browser_url(self) -> Optional[str]:
        """
        获取当前浏览器URL
        
        Returns:
            Optional[str]: 当前URL，如果无法获取则返回None
        """
        try:
            # 尝试多种方法获取浏览器URL
            
            # 方法1: 使用浏览器扩展API（需要预先安装扩展）
            url = self._get_url_from_browser_extension()
            if url:
                return url
            
            # 方法2: 使用操作系统特定命令
            url = self._get_url_from_os_command()
            if url:
                return url
            
            # 方法3: 使用浏览器自动化工具（如果可用）
            url = self._get_url_from_automation_tool()
            if url:
                return url
            
            return None
        
        except Exception as e:
            logger.error(f"获取浏览器URL失败: {e}")
            return None
    
    def _get_url_from_browser_extension(self) -> Optional[str]:
        """
        从浏览器扩展获取URL（需要预先安装扩展）
        
        Returns:
            Optional[str]: 当前URL，如果无法获取则返回None
        """
        # 这里需要实现与浏览器扩展的通信
        # 由于需要预先安装扩展，这里只是一个占位实现
        return None
    
    def _get_url_from_os_command(self) -> Optional[str]:
        """
        使用操作系统特定命令获取URL
        
        Returns:
            Optional[str]: 当前URL，如果无法获取则返回None
        """
        try:
            # 检测操作系统类型
            if sys.platform == "darwin":  # macOS
                # 获取Chrome当前URL (AppleScript)
                cmd = """osascript -e 'tell application "Google Chrome" to get URL of active tab of front window'"""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                
                # 尝试获取Safari当前URL
                cmd = """osascript -e 'tell application "Safari" to get URL of current tab of front window'"""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            
            elif sys.platform == "win32":  # Windows
                # 使用PowerShell获取Chrome当前URL
                cmd = """powershell -command "$chrome = Get-Process chrome | Where-Object {$_.MainWindowTitle -ne ''}; $chrome.MainWindowTitle" """
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    # 从窗口标题中提取URL（不太可靠，但可能有效）
                    title = result.stdout.strip()
                    if "manus.im" in title.lower():
                        return "https://manus.im/"
            
            elif sys.platform.startswith("linux"):  # Linux
                # 使用xdotool获取浏览器窗口标题
                cmd = """xdotool getactivewindow getwindowname"""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    title = result.stdout.strip()
                    if "manus.im" in title.lower():
                        return "https://manus.im/"
            
            return None
        
        except Exception as e:
            logger.error(f"使用操作系统命令获取URL失败: {e}")
            return None
    
    def _get_url_from_automation_tool(self) -> Optional[str]:
        """
        使用浏览器自动化工具获取URL
        
        Returns:
            Optional[str]: 当前URL，如果无法获取则返回None
        """
        # 这里可以集成Selenium或Playwright
        # 由于这些工具需要额外安装，这里只是一个占位实现
        return None
    
    def _capture_page_content(self, url: str):
        """
        捕获页面内容
        
        Args:
            url: 当前URL
        """
        logger.info(f"开始捕获页面内容: {url}")
        
        try:
            # 创建捕获时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 捕获方法1: 截取屏幕
            self._capture_screenshot(timestamp)
            
            # 捕获方法2: 提取页面内容
            self._extract_page_content(url, timestamp)
            
            logger.info(f"页面内容捕获完成: {url}")
        
        except Exception as e:
            logger.error(f"捕获页面内容失败: {e}")
    
    def _capture_screenshot(self, timestamp: str):
        """
        截取屏幕
        
        Args:
            timestamp: 时间戳
        """
        try:
            # 检测操作系统类型并使用相应的截图方法
            screenshot_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                f"screenshot_{timestamp}.png"
            )
            
            if sys.platform == "darwin":  # macOS
                cmd = f"""screencapture -x "{screenshot_path}" """
                subprocess.run(cmd, shell=True, check=True)
            
            elif sys.platform == "win32":  # Windows
                # 使用PIL的ImageGrab
                try:
                    from PIL import ImageGrab
                    screenshot = ImageGrab.grab()
                    screenshot.save(screenshot_path)
                except ImportError:
                    # 如果PIL不可用，尝试使用pyautogui
                    try:
                        import pyautogui
                        screenshot = pyautogui.screenshot()
                        screenshot.save(screenshot_path)
                    except ImportError:
                        logger.error("无法截图: 缺少必要的库 (PIL 或 pyautogui)")
                        return
            
            elif sys.platform.startswith("linux"):  # Linux
                cmd = f"""import -window root "{screenshot_path}" """
                subprocess.run(cmd, shell=True, check=True)
            
            logger.info(f"截图已保存: {screenshot_path}")
            
            # 分析截图中的工作列表和操作列表区域
            self._analyze_screenshot(screenshot_path, timestamp)
        
        except Exception as e:
            logger.error(f"截图失败: {e}")
    
    def _analyze_screenshot(self, screenshot_path: str, timestamp: str):
        """
        分析截图中的工作列表和操作列表区域
        
        Args:
            screenshot_path: 截图路径
            timestamp: 时间戳
        """
        try:
            # 这里可以集成OCR或图像分析库来识别和提取工作列表和操作列表
            # 由于这需要额外的依赖，这里只是一个占位实现
            
            # 示例: 使用预定义的区域（实际应用中应该动态识别）
            work_list_region = (100, 100, 500, 400)  # 示例坐标 (x1, y1, x2, y2)
            action_list_region = (600, 100, 1000, 400)  # 示例坐标
            
            # 从截图中裁剪区域
            try:
                img = Image.open(screenshot_path)
                
                # 裁剪工作列表区域
                work_list_img = img.crop(work_list_region)
                work_list_path = os.path.join(
                    self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                    f"work_list_{timestamp}.png"
                )
                work_list_img.save(work_list_path)
                
                # 裁剪操作列表区域
                action_list_img = img.crop(action_list_region)
                action_list_path = os.path.join(
                    self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                    f"action_list_{timestamp}.png"
                )
                action_list_img.save(action_list_path)
                
                logger.info(f"已提取工作列表和操作列表区域")
                
                # 可以在这里添加OCR处理
                self._perform_ocr_on_regions(work_list_path, action_list_path, timestamp)
            
            except Exception as e:
                logger.error(f"处理截图区域失败: {e}")
        
        except Exception as e:
            logger.error(f"分析截图失败: {e}")
    
    def _perform_ocr_on_regions(self, work_list_path: str, action_list_path: str, timestamp: str):
        """
        对区域图像执行OCR识别
        
        Args:
            work_list_path: 工作列表图像路径
            action_list_path: 操作列表图像路径
            timestamp: 时间戳
        """
        try:
            # 这里可以集成OCR库（如Tesseract、EasyOCR等）
            # 由于这需要额外的依赖，这里只是一个占位实现
            
            # 示例: 保存OCR结果
            work_list_text = "工作列表OCR结果将在这里显示"
            action_list_text = "操作列表OCR结果将在这里显示"
            
            # 保存OCR结果
            work_list_text_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                f"work_list_{timestamp}.txt"
            )
            with open(work_list_text_path, 'w', encoding='utf-8') as f:
                f.write(work_list_text)
            
            action_list_text_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                f"action_list_{timestamp}.txt"
            )
            with open(action_list_text_path, 'w', encoding='utf-8') as f:
                f.write(action_list_text)
            
            logger.info(f"OCR结果已保存")
        
        except Exception as e:
            logger.error(f"OCR处理失败: {e}")
    
    def _extract_page_content(self, url: str, timestamp: str):
        """
        提取页面内容
        
        Args:
            url: 当前URL
            timestamp: 时间戳
        """
        try:
            # 方法1: 使用requests直接获取页面内容
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    html_content = response.text
                    
                    # 保存原始HTML
                    html_path = os.path.join(
                        self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                        f"page_{timestamp}.html"
                    )
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    logger.info(f"页面HTML已保存: {html_path}")
                    
                    # 解析HTML提取工作列表和操作列表
                    self._parse_html_content(html_content, timestamp)
            
            except Exception as e:
                logger.error(f"使用requests获取页面内容失败: {e}")
            
            # 方法2: 使用浏览器自动化工具（如果可用）
            self._extract_content_with_automation(url, timestamp)
        
        except Exception as e:
            logger.error(f"提取页面内容失败: {e}")
    
    def _parse_html_content(self, html_content: str, timestamp: str):
        """
        解析HTML内容提取工作列表和操作列表
        
        Args:
            html_content: HTML内容
            timestamp: 时间戳
        """
        try:
            # 使用正则表达式或HTML解析库提取内容
            # 这里使用简单的正则表达式示例
            
            # 提取工作列表
            work_list_pattern = r'<div[^>]*class="[^"]*work-list[^"]*"[^>]*>(.*?)</div>'
            work_list_matches = re.findall(work_list_pattern, html_content, re.DOTALL)
            
            work_list_text = "\n".join(work_list_matches) if work_list_matches else "未找到工作列表"
            
            # 提取操作列表
            action_list_pattern = r'<div[^>]*class="[^"]*action-list[^"]*"[^>]*>(.*?)</div>'
            action_list_matches = re.findall(action_list_pattern, html_content, re.DOTALL)
            
            action_list_text = "\n".join(action_list_matches) if action_list_matches else "未找到操作列表"
            
            # 保存提取结果
            work_list_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                f"work_list_html_{timestamp}.txt"
            )
            with open(work_list_path, 'w', encoding='utf-8') as f:
                f.write(work_list_text)
            
            action_list_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                f"action_list_html_{timestamp}.txt"
            )
            with open(action_list_path, 'w', encoding='utf-8') as f:
                f.write(action_list_text)
            
            logger.info(f"已从HTML提取工作列表和操作列表")
            
            # 可以在这里添加更多处理，如清理HTML标签、格式化等
        
        except Exception as e:
            logger.error(f"解析HTML内容失败: {e}")
    
    def _extract_content_with_automation(self, url: str, timestamp: str):
        """
        使用浏览器自动化工具提取内容
        
        Args:
            url: 当前URL
            timestamp: 时间戳
        """
        # 这里可以集成Selenium或Playwright
        # 由于这些工具需要额外安装，这里只是一个占位实现
        pass

# 单例模式
_instance = None

def get_instance(config_file=None):
    """
    获取AutoWebMonitor实例（单例模式）
    
    Args:
        config_file: 配置文件路径，可选
    
    Returns:
        AutoWebMonitor: 实例
    """
    global _instance
    if _instance is None:
        _instance = AutoWebMonitor(config_file)
    return _instance

def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='自动网页监控与抓取工具')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--start', action='store_true', help='启动监控')
    parser.add_argument('--stop', action='store_true', help='停止监控')
    args = parser.parse_args()
    
    # 获取实例
    monitor = get_instance(args.config)
    
    if args.start:
        monitor.start_monitoring()
        print("监控已启动，按Ctrl+C停止...")
        try:
            # 保持主线程运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("正在停止监控...")
            monitor.stop_monitoring()
    elif args.stop:
        monitor.stop_monitoring()
        print("监控已停止")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
