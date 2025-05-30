"""
Mac专用视觉校准与区域检测模块 - MacVisualCalibrator

该模块专为Mac环境设计，用于校准和测试自动网页监控的视觉抓取区域，
支持动态识别网页元素位置，适应不同屏幕分辨率和浏览器窗口大小。

作者: Manus AI
日期: 2025-05-30
"""

import os
import sys
import json
import time
import logging
import re
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont

# 导入统一配置管理
from .unified_config import get_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MacVisualCalibrator")

class MacVisualCalibrator:
    """Mac专用视觉校准器类"""
    
    def __init__(self, config_path=None, output_dir=None, simple_mode=False, manual_regions=False):
        """
        初始化Mac视觉校准器
        
        Args:
            config_path: 配置文件路径，可选
            output_dir: 输出目录路径，可选，优先级高于配置文件
            simple_mode: 是否使用简化模式（不使用AppleScript），可选
            manual_regions: 是否使用手动区域标定模式，可选
        """
        # 获取统一配置
        self.config_manager = get_config(config_path)
        self.config = self.config_manager.get_all()
        
        # 命令行参数优先级高于配置文件
        if output_dir:
            self.config["log_dir"] = output_dir
        if simple_mode:
            self.config["simple_mode"] = simple_mode
        if manual_regions:
            self.config["manual_regions"] = manual_regions
            
        self.temp_dir = tempfile.mkdtemp(prefix="mac_visual_calibration_")
        
        # 创建日志目录
        os.makedirs(self.config.get("log_dir", os.path.expanduser("~/mcp_logs")), exist_ok=True)
        
        logger.info("Mac视觉校准器初始化完成")
        logger.info(f"临时文件目录: {self.temp_dir}")
        logger.info(f"日志目录: {self.config.get('log_dir')}")
        logger.info(f"简化模式: {self.config.get('simple_mode')}")
        logger.info(f"手动区域标定模式: {self.config.get('manual_regions')}")
    
    def _save_config(self) -> bool:
        """
        保存配置
        
        Returns:
            bool: 是否成功保存
        """
        try:
            return self.config_manager.save()
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def capture_screenshot(self) -> Optional[str]:
        """
        使用Mac原生screencapture命令捕获屏幕
        
        Returns:
            Optional[str]: 截图文件路径，如果失败则返回None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.temp_dir, f"calibration_screenshot_{timestamp}.png")
            
            # 使用Mac原生screencapture命令
            cmd = f"""screencapture -x "{screenshot_path}" """
            subprocess.run(cmd, shell=True, check=True)
            
            logger.info(f"全屏截图已保存: {screenshot_path}")
            return screenshot_path
        
        except Exception as e:
            logger.error(f"捕获全屏截图失败: {e}")
            return None
    
    def get_active_browser_info(self) -> Dict[str, Any]:
        """
        获取活动浏览器信息
        
        Returns:
            Dict[str, Any]: 浏览器信息，包括名称、窗口位置等
        """
        # 如果使用简化模式，返回默认值
        if self.config.get("simple_mode"):
            logger.info("使用简化模式，返回默认浏览器信息")
            return {
                "name": "SimpleBrowser",
                "path": "",
                "id": "",
                "position": {"x": 0, "y": 0},
                "size": {"width": 0, "height": 0}
            }
        
        try:
            # 使用AppleScript获取前台应用信息
            script = """
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set frontAppPath to path of first application process whose frontmost is true
                set frontAppId to bundle identifier of first application process whose frontmost is true
                
                set windowPosition to {}
                set windowSize to {}
                
                try
                    tell process frontApp
                        set appWindow to first window
                        set windowPosition to position of appWindow
                        set windowSize to size of appWindow
                    end tell
                end try
                
                return {frontApp, frontAppPath, frontAppId, windowPosition, windowSize}
            end tell
            """
            
            # 执行AppleScript
            cmd = ["osascript", "-e", script]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # 解析结果
            output = result.stdout.strip()
            parts = output.split(", ")
            
            # 提取浏览器信息
            browser_info = {
                "name": parts[0] if len(parts) > 0 else "Unknown",
                "path": parts[1] if len(parts) > 1 else "",
                "id": parts[2] if len(parts) > 2 else "",
                "position": {
                    "x": int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0,
                    "y": int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                },
                "size": {
                    "width": int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else 0,
                    "height": int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else 0
                }
            }
            
            logger.info(f"获取到活动浏览器信息: {browser_info}")
            return browser_info
        
        except Exception as e:
            logger.error(f"获取活动浏览器信息失败: {e}")
            return {
                "name": "Unknown",
                "path": "",
                "id": "",
                "position": {"x": 0, "y": 0},
                "size": {"width": 0, "height": 0}
            }
    
    def get_browser_url(self) -> Optional[str]:
        """
        获取浏览器当前URL
        
        Returns:
            Optional[str]: 当前URL，如果失败则返回None
        """
        # 如果使用简化模式，返回默认值
        if self.config.get("simple_mode"):
            logger.info("使用简化模式，返回默认URL")
            return self.config.get("manus_url", "https://manus.im/")
        
        try:
            # 获取浏览器信息
            browser_info = self.get_active_browser_info()
            browser_name = browser_info["name"].lower()
            
            # 根据不同浏览器使用不同的AppleScript
            if "safari" in browser_name:
                script = """
                tell application "Safari"
                    return URL of current tab of front window
                end tell
                """
            elif "chrome" in browser_name:
                script = """
                tell application "Google Chrome"
                    return URL of active tab of front window
                end tell
                """
            elif "firefox" in browser_name:
                script = """
                tell application "Firefox"
                    return URL of active tab of front window
                end tell
                """
            else:
                logger.warning(f"不支持的浏览器: {browser_name}")
                return None
            
            # 执行AppleScript
            cmd = ["osascript", "-e", script]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                url = result.stdout.strip()
                logger.info(f"获取到浏览器URL: {url}")
                return url
            else:
                logger.error(f"获取浏览器URL失败: {result.stderr}")
                return None
        
        except Exception as e:
            logger.error(f"获取浏览器URL失败: {e}")
            return None
    
    def detect_browser_window(self, screenshot_path: str) -> Optional[Tuple[int, int, int, int]]:
        """
        检测浏览器窗口位置
        
        Args:
            screenshot_path: 截图文件路径
        
        Returns:
            Optional[Tuple[int, int, int, int]]: 浏览器窗口坐标 (x1, y1, x2, y2)，如果检测失败则返回None
        """
        try:
            # 如果使用简化模式，使用全屏作为浏览器窗口
            if self.config.get("simple_mode"):
                # 获取屏幕尺寸
                img = Image.open(screenshot_path)
                width, height = img.size
                
                # 使用全屏作为浏览器窗口
                browser_window = (0, 0, width, height)
                
                logger.info(f"简化模式，使用全屏作为浏览器窗口: {browser_window}")
                return browser_window
            
            # 获取浏览器信息
            browser_info = self.get_active_browser_info()
            
            # 提取窗口位置和大小
            x = browser_info["position"]["x"]
            y = browser_info["position"]["y"]
            width = browser_info["size"]["width"]
            height = browser_info["size"]["height"]
            
            # 计算窗口坐标
            browser_window = (x, y, x + width, y + height)
            
            logger.info(f"检测到浏览器窗口: {browser_window}")
            return browser_window
        
        except Exception as e:
            logger.error(f"检测浏览器窗口失败: {e}")
            
            # 如果无法获取浏览器窗口，使用图像处理方法估计
            try:
                # 获取屏幕尺寸
                img = Image.open(screenshot_path)
                width, height = img.size
                
                # 假设浏览器窗口占据了大部分屏幕
                margin = min(width, height) // 10
                browser_window = (margin, margin, width - margin, height - margin)
                
                logger.info(f"使用估计的浏览器窗口: {browser_window}")
                return browser_window
            
            except Exception as e2:
                logger.error(f"估计浏览器窗口失败: {e2}")
                return None
    
    def create_calibration_grid(self, screenshot_path: str, browser_window: Tuple[int, int, int, int]) -> str:
        """
        创建校准网格
        
        Args:
            screenshot_path: 截图文件路径
            browser_window: 浏览器窗口坐标 (x1, y1, x2, y2)
        
        Returns:
            str: 带网格的截图文件路径
        """
        try:
            # 加载截图
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)
            
            # 获取浏览器窗口尺寸
            x1, y1, x2, y2 = browser_window
            width = x2 - x1
            height = y2 - y1
            
            # 绘制边框
            draw.rectangle(browser_window, outline="red", width=2)
            
            # 绘制网格
            grid_size = self.config.get("calibration_grid_size", 10)
            cell_width = width // grid_size
            cell_height = height // grid_size
            
            # 绘制水平线
            for i in range(1, grid_size):
                y = y1 + i * cell_height
                draw.line([(x1, y), (x2, y)], fill="blue", width=1)
            
            # 绘制垂直线
            for i in range(1, grid_size):
                x = x1 + i * cell_width
                draw.line([(x, y1), (x, y2)], fill="blue", width=1)
            
            # 标记坐标
            try:
                # 尝试加载字体
                font = ImageFont.truetype("Arial.ttf", 12)
            except IOError:
                # 如果无法加载字体，使用默认字体
                font = ImageFont.load_default()
            
            # 标记网格坐标
            for i in range(grid_size + 1):
                for j in range(grid_size + 1):
                    x = x1 + j * cell_width
                    y = y1 + i * cell_height
                    coord_text = f"({j},{i})"
                    draw.text((x - 15, y - 15), coord_text, fill="red", font=font)
            
            # 保存带网格的截图
            grid_path = os.path.join(self.temp_dir, f"calibration_grid_{os.path.basename(screenshot_path)}")
            img.save(grid_path)
            
            logger.info(f"校准网格已创建: {grid_path}")
            return grid_path
        
        except Exception as e:
            logger.error(f"创建校准网格失败: {e}")
            return screenshot_path
    
    def detect_content_regions(self, screenshot_path: str, browser_window: Tuple[int, int, int, int]) -> Dict[str, Tuple[int, int, int, int]]:
        """
        检测内容区域
        
        Args:
            screenshot_path: 截图文件路径
            browser_window: 浏览器窗口坐标 (x1, y1, x2, y2)
        
        Returns:
            Dict[str, Tuple[int, int, int, int]]: 检测到的区域，格式为 {"work_list": (x1, y1, x2, y2), "action_list": (x1, y1, x2, y2)}
        """
        try:
            # 获取浏览器窗口尺寸
            x1, y1, x2, y2 = browser_window
            width = x2 - x1
            height = y2 - y1
            
            # 如果使用手动区域标定模式，提示用户手动标定
            if self.config.get("manual_regions"):
                logger.info("使用手动区域标定模式")
                return self._manual_region_selection(screenshot_path, browser_window)
            
            # 获取当前URL
            url = self.get_browser_url() if not self.config.get("simple_mode") else self.config.get("manus_url", "https://manus.im/")
            
            # 检查是否为目标网站
            pattern = self.config.get("browser_window_title_pattern", r".*manus\.im.*")
            if url and re.search(pattern, url, re.IGNORECASE):
                logger.info(f"检测到目标网站: {url}")
                
                # 根据manus.im网站的布局估计区域位置
                # 使用配置中的默认区域比例
                work_list_region = self.config.get("default_work_list_region", [0.05, 0.2, 0.45, 0.8])
                action_list_region = self.config.get("default_action_list_region", [0.55, 0.2, 0.95, 0.8])
                
                # 工作列表
                work_list_x1 = x1 + width * work_list_region[0]
                work_list_y1 = y1 + height * work_list_region[1]
                work_list_x2 = x1 + width * work_list_region[2]
                work_list_y2 = y1 + height * work_list_region[3]
                
                # 操作列表
                action_list_x1 = x1 + width * action_list_region[0]
                action_list_y1 = y1 + height * action_list_region[1]
                action_list_x2 = x1 + width * action_list_region[2]
                action_list_y2 = y1 + height * action_list_region[3]
                
                regions = {
                    "work_list": (int(work_list_x1), int(work_list_y1), int(work_list_x2), int(work_list_y2)),
                    "action_list": (int(action_list_x1), int(action_list_y1), int(action_list_x2), int(action_list_y2))
                }
            else:
                logger.warning(f"未检测到目标网站，当前URL: {url}")
                
                # 使用默认区域
                work_list_region = self.config.get("default_work_list_region", [0.05, 0.2, 0.45, 0.8])
                action_list_region = self.config.get("default_action_list_region", [0.55, 0.2, 0.95, 0.8])
                
                # 工作列表
                work_list_x1 = x1 + width * work_list_region[0]
                work_list_y1 = y1 + height * work_list_region[1]
                work_list_x2 = x1 + width * work_list_region[2]
                work_list_y2 = y1 + height * work_list_region[3]
                
                # 操作列表
                action_list_x1 = x1 + width * action_list_region[0]
                action_list_y1 = y1 + height * action_list_region[1]
                action_list_x2 = x1 + width * action_list_region[2]
                action_list_y2 = y1 + height * action_list_region[3]
                
                regions = {
                    "work_list": (int(work_list_x1), int(work_list_y1), int(work_list_x2), int(work_list_y2)),
                    "action_list": (int(action_list_x1), int(action_list_y1), int(action_list_x2), int(action_list_y2))
                }
            
            logger.info(f"检测到内容区域: {regions}")
            return regions
        
        except Exception as e:
            logger.error(f"检测内容区域失败: {e}")
            return {
                "work_list": (0, 0, 0, 0),
                "action_list": (0, 0, 0, 0)
            }
    
    def _manual_region_selection(self, screenshot_path: str, browser_window: Tuple[int, int, int, int]) -> Dict[str, Tuple[int, int, int, int]]:
        """
        手动区域选择
        
        Args:
            screenshot_path: 截图文件路径
            browser_window: 浏览器窗口坐标 (x1, y1, x2, y2)
        
        Returns:
            Dict[str, Tuple[int, int, int, int]]: 手动选择的区域
        """
        try:
            # 创建带网格的截图
            grid_path = self.create_calibration_grid(screenshot_path, browser_window)
            
            # 显示带网格的截图
            print(f"\n请查看带网格的截图: {grid_path}")
            print("根据网格坐标，请输入工作列表和操作列表的区域坐标。")
            
            # 获取浏览器窗口尺寸
            x1, y1, x2, y2 = browser_window
            width = x2 - x1
            height = y2 - y1
            
            # 获取网格大小
            grid_size = self.config.get("calibration_grid_size", 10)
            cell_width = width // grid_size
            cell_height = height // grid_size
            
            # 提示用户输入工作列表区域
            print("\n请输入工作列表区域的网格坐标:")
            work_list_x1 = int(input("左上角X坐标 (0-10): "))
            work_list_y1 = int(input("左上角Y坐标 (0-10): "))
            work_list_x2 = int(input("右下角X坐标 (0-10): "))
            work_list_y2 = int(input("右下角Y坐标 (0-10): "))
            
            # 提示用户输入操作列表区域
            print("\n请输入操作列表区域的网格坐标:")
            action_list_x1 = int(input("左上角X坐标 (0-10): "))
            action_list_y1 = int(input("左上角Y坐标 (0-10): "))
            action_list_x2 = int(input("右下角X坐标 (0-10): "))
            action_list_y2 = int(input("右下角Y坐标 (0-10): "))
            
            # 转换网格坐标为像素坐标
            work_list_region = (
                x1 + work_list_x1 * cell_width,
                y1 + work_list_y1 * cell_height,
                x1 + work_list_x2 * cell_width,
                y1 + work_list_y2 * cell_height
            )
            
            action_list_region = (
                x1 + action_list_x1 * cell_width,
                y1 + action_list_y1 * cell_height,
                x1 + action_list_x2 * cell_width,
                y1 + action_list_y2 * cell_height
            )
            
            # 更新配置中的默认区域比例
            self.config["default_work_list_region"] = [
                (work_list_x1 * cell_width) / width,
                (work_list_y1 * cell_height) / height,
                (work_list_x2 * cell_width) / width,
                (work_list_y2 * cell_height) / height
            ]
            
            self.config["default_action_list_region"] = [
                (action_list_x1 * cell_width) / width,
                (action_list_y1 * cell_height) / height,
                (action_list_x2 * cell_width) / width,
                (action_list_y2 * cell_height) / height
            ]
            
            # 保存配置
            self.config_manager.update({
                "default_work_list_region": self.config["default_work_list_region"],
                "default_action_list_region": self.config["default_action_list_region"]
            })
            
            regions = {
                "work_list": work_list_region,
                "action_list": action_list_region
            }
            
            logger.info(f"手动选择的区域: {regions}")
            return regions
        
        except Exception as e:
            logger.error(f"手动区域选择失败: {e}")
            return {
                "work_list": (0, 0, 0, 0),
                "action_list": (0, 0, 0, 0)
            }
    
    def visualize_detected_regions(self, screenshot_path: str, regions: Dict[str, Tuple[int, int, int, int]]) -> str:
        """
        可视化检测到的区域
        
        Args:
            screenshot_path: 截图文件路径
            regions: 检测到的区域
        
        Returns:
            str: 带标记的截图文件路径
        """
        try:
            # 加载截图
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)
            
            # 绘制区域
            colors = {
                "work_list": "green",
                "action_list": "blue"
            }
            
            for name, region in regions.items():
                if region == (0, 0, 0, 0):
                    continue
                
                x1, y1, x2, y2 = region
                color = colors.get(name, "yellow")
                draw.rectangle(region, outline=color, width=2)
                
                # 添加标签
                try:
                    font = ImageFont.truetype("Arial.ttf", 16)
                except IOError:
                    font = ImageFont.load_default()
                
                draw.text((x1 + 5, y1 + 5), name, fill=color, font=font)
            
            # 保存带标记的截图
            marked_path = os.path.join(self.temp_dir, f"detected_regions_{os.path.basename(screenshot_path)}")
            img.save(marked_path)
            
            logger.info(f"已可视化检测区域: {marked_path}")
            return marked_path
        
        except Exception as e:
            logger.error(f"可视化检测区域失败: {e}")
            return screenshot_path
    
    def extract_region_content(self, screenshot_path: str, regions: Dict[str, Tuple[int, int, int, int]]) -> Dict[str, str]:
        """
        提取区域内容
        
        Args:
            screenshot_path: 截图文件路径
            regions: 检测到的区域
        
        Returns:
            Dict[str, str]: 提取的区域内容图像路径
        """
        try:
            # 加载截图
            img = Image.open(screenshot_path)
            
            # 提取区域内容
            region_images = {}
            
            for name, region in regions.items():
                if region == (0, 0, 0, 0):
                    continue
                
                # 裁剪区域
                region_img = img.crop(region)
                
                # 保存区域图像
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                region_path = os.path.join(
                    self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                    f"{name}_{timestamp}.png"
                )
                region_img.save(region_path)
                
                region_images[name] = region_path
            
            logger.info(f"已提取区域内容: {region_images}")
            return region_images
        
        except Exception as e:
            logger.error(f"提取区域内容失败: {e}")
            return {}
    
    def update_auto_monitor_config(self, regions: Dict[str, Tuple[int, int, int, int]]) -> bool:
        """
        更新自动监控配置
        
        Args:
            regions: 检测到的区域
        
        Returns:
            bool: 是否成功更新
        """
        try:
            # 更新监控区域
            monitor_regions = {}
            
            for name, region in regions.items():
                if region == (0, 0, 0, 0):
                    continue
                
                x1, y1, x2, y2 = region
                monitor_regions[name] = {
                    "x": x1,
                    "y": y1,
                    "width": x2 - x1,
                    "height": y2 - y1
                }
            
            # 更新配置
            self.config_manager.update({
                "monitor_regions": monitor_regions,
                "platform": "darwin",
                "last_updated": datetime.now().isoformat()
            })
            
            logger.info(f"已更新自动监控配置: {monitor_regions}")
            return True
        
        except Exception as e:
            logger.error(f"更新自动监控配置失败: {e}")
            return False
    
    def run(self) -> Dict[str, Any]:
        """
        运行视觉校准
        
        Returns:
            Dict[str, Any]: 校准结果
        """
        try:
            # 捕获屏幕截图
            screenshot_path = self.capture_screenshot()
            if not screenshot_path:
                return {"status": "error", "message": "捕获屏幕截图失败"}
            
            # 检测浏览器窗口
            browser_window = self.detect_browser_window(screenshot_path)
            if not browser_window:
                return {"status": "error", "message": "检测浏览器窗口失败"}
            
            # 检测内容区域
            regions = self.detect_content_regions(screenshot_path, browser_window)
            
            # 可视化检测到的区域
            marked_path = self.visualize_detected_regions(screenshot_path, regions)
            
            # 提取区域内容
            region_images = self.extract_region_content(screenshot_path, regions)
            
            # 更新自动监控配置
            self.update_auto_monitor_config(regions)
            
            result = {
                "status": "success",
                "screenshot_path": screenshot_path,
                "marked_path": marked_path,
                "regions": regions,
                "region_images": region_images,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("视觉校准完成")
            return result
        
        except Exception as e:
            logger.error(f"视觉校准失败: {e}")
            return {"status": "error", "message": str(e)}


def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Mac视觉校准工具")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--output_dir", help="输出目录路径")
    parser.add_argument("--simple_mode", action="store_true", help="使用简化模式（不使用AppleScript）")
    parser.add_argument("--manual_regions", action="store_true", help="使用手动区域标定模式")
    
    args = parser.parse_args()
    
    # 创建Mac视觉校准器
    calibrator = MacVisualCalibrator(
        config_path=args.config,
        output_dir=args.output_dir,
        simple_mode=args.simple_mode,
        manual_regions=args.manual_regions
    )
    
    # 运行视觉校准
    result = calibrator.run()
    
    # 输出结果
    if result["status"] == "success":
        print("\n视觉校准成功！")
        print(f"截图路径: {result['screenshot_path']}")
        print(f"标记路径: {result['marked_path']}")
        print("检测到的区域:")
        for name, region in result["regions"].items():
            print(f"  {name}: {region}")
        print("区域内容图像:")
        for name, path in result["region_images"].items():
            print(f"  {name}: {path}")
    else:
        print(f"\n视觉校准失败: {result['message']}")


if __name__ == "__main__":
    main()
