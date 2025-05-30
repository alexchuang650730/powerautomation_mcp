"""
跨平台视觉校准与区域检测模块 - VisualCalibrator

该模块设计为跨平台使用，支持Windows和Mac环境，用于校准和测试自动网页监控的视觉抓取区域，
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
import platform
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont

# 根据平台导入特定模块
PLATFORM = platform.system().lower()
if PLATFORM == 'windows':
    import pyautogui
    import pygetwindow as gw
    try:
        import win32gui
        import win32process
        import win32con
    except ImportError:
        logging.warning("win32gui模块未安装，部分功能可能受限")
elif PLATFORM == 'darwin':  # macOS
    pass  # Mac特定导入在需要时进行
else:
    logging.warning(f"不支持的平台: {PLATFORM}")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VisualCalibrator")

class VisualCalibrator:
    """跨平台视觉校准器基类"""
    
    def __init__(self, config_file=None, output_dir=None, simple_mode=False, manual_regions=False):
        """
        初始化视觉校准器
        
        Args:
            config_file: 配置文件路径，可选
            output_dir: 输出目录路径，可选，优先级高于配置文件
            simple_mode: 是否使用简化模式，可选
            manual_regions: 是否使用手动区域标定模式，可选
        """
        self.config_file = config_file
        self.output_dir = output_dir
        self.simple_mode = simple_mode
        self.manual_regions = manual_regions
        self.config = self._load_config()
        self.temp_dir = tempfile.mkdtemp(prefix="visual_calibration_")
        
        # 如果指定了输出目录，覆盖配置中的日志目录
        if self.output_dir:
            self.config["log_dir"] = self.output_dir
        
        # 创建日志目录
        os.makedirs(self.config.get("log_dir", os.path.expanduser("~/mcp_logs")), exist_ok=True)
        
        logger.info(f"{PLATFORM.capitalize()}视觉校准器初始化完成")
        logger.info(f"临时文件目录: {self.temp_dir}")
        logger.info(f"日志目录: {self.config.get('log_dir', os.path.expanduser('~/mcp_logs'))}")
        logger.info(f"简化模式: {self.simple_mode}")
        logger.info(f"手动区域标定模式: {self.manual_regions}")
    
    def _load_config(self) -> Dict:
        """
        加载配置
        
        Returns:
            Dict: 配置字典
        """
        default_config = {
            "log_dir": os.path.expanduser("~/mcp_logs"),
            "browser_window_title_pattern": r".*manus\.im.*",
            "work_list_pattern": r"work[-_\s]*list|task[-_\s]*list",
            "action_list_pattern": r"action[-_\s]*list|operation[-_\s]*list",
            "calibration_grid_size": 10,  # 校准网格大小
            "detection_confidence_threshold": 0.7,  # 检测置信度阈值
            "work_list_css_selector": ".work-list-container",  # 工作列表CSS选择器
            "action_list_css_selector": ".action-list-container",  # 操作列表CSS选择器
            "simple_mode": False,  # 是否使用简化模式
            "manual_regions": False,  # 是否使用手动区域标定模式
            "default_work_list_region": [0.05, 0.2, 0.45, 0.8],  # 默认工作列表区域 [左, 上, 右, 下] 相对比例
            "default_action_list_region": [0.55, 0.2, 0.95, 0.8]  # 默认操作列表区域 [左, 上, 右, 下] 相对比例
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
                f"{PLATFORM}_visual_calibration.json"
            )
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存配置文件: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def capture_screenshot(self) -> Optional[str]:
        """
        捕获屏幕截图（平台特定实现）
        
        Returns:
            Optional[str]: 截图文件路径，如果失败则返回None
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def get_active_browser_info(self) -> Dict[str, Any]:
        """
        获取活动浏览器信息（平台特定实现）
        
        Returns:
            Dict[str, Any]: 浏览器信息，包括名称、窗口位置等
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def get_browser_url(self) -> Optional[str]:
        """
        获取浏览器当前URL（平台特定实现）
        
        Returns:
            Optional[str]: 当前URL，如果失败则返回None
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def detect_browser_window(self, screenshot_path: str) -> Optional[Tuple[int, int, int, int]]:
        """
        检测浏览器窗口位置（平台特定实现）
        
        Args:
            screenshot_path: 截图文件路径
        
        Returns:
            Optional[Tuple[int, int, int, int]]: 浏览器窗口坐标 (x1, y1, x2, y2)，如果检测失败则返回None
        """
        raise NotImplementedError("子类必须实现此方法")
    
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
            if self.manual_regions:
                logger.info("使用手动区域标定模式")
                return self._manual_region_selection(screenshot_path, browser_window)
            
            # 获取当前URL
            url = self.get_browser_url() if not self.simple_mode else "https://manus.im/"
            
            # 检查是否为目标网站
            if url and "manus.im" in url:
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
        手动区域选择（平台特定实现）
        
        Args:
            screenshot_path: 截图文件路径
            browser_window: 浏览器窗口坐标 (x1, y1, x2, y2)
        
        Returns:
            Dict[str, Tuple[int, int, int, int]]: 手动选择的区域
        """
        raise NotImplementedError("子类必须实现此方法")
    
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
            # 加载自动监控配置
            auto_monitor_config_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                "auto_web_monitor_config.json"
            )
            
            if os.path.exists(auto_monitor_config_path):
                with open(auto_monitor_config_path, 'r', encoding='utf-8') as f:
                    auto_monitor_config = json.load(f)
            else:
                auto_monitor_config = {}
            
            # 更新监控区域
            monitor_regions = []
            
            for name, region in regions.items():
                if region == (0, 0, 0, 0):
                    continue
                
                monitor_regions.append({
                    "name": name,
                    "type": "thought" if name == "work_list" else "action",
                    "bbox": region
                })
            
            auto_monitor_config["monitor_regions"] = monitor_regions
            auto_monitor_config["platform"] = PLATFORM
            auto_monitor_config["last_updated"] = datetime.now().isoformat()
            
            # 保存配置
            with open(auto_monitor_config_path, 'w', encoding='utf-8') as f:
                json.dump(auto_monitor_config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已更新自动监控配置: {auto_monitor_config_path}")
            return True
        
        except Exception as e:
            logger.error(f"更新自动监控配置失败: {e}")
            return False
    
    def run_calibration(self) -> Dict[str, Any]:
        """
        运行校准
        
        Returns:
            Dict[str, Any]: 校准结果
        """
        try:
            # 步骤1: 捕获全屏截图
            logger.info("步骤1: 捕获全屏截图")
            screenshot_path = self.capture_screenshot()
            if not screenshot_path:
                return {"success": False, "error": "捕获全屏截图失败"}
            
            # 步骤2: 检测浏览器窗口
            logger.info("步骤2: 检测浏览器窗口")
            browser_window = self.detect_browser_window(screenshot_path)
            if not browser_window:
                return {"success": False, "error": "检测浏览器窗口失败"}
            
            # 步骤3: 创建校准网格
            logger.info("步骤3: 创建校准网格")
            grid_path = self.create_calibration_grid(screenshot_path, browser_window)
            
            # 步骤4: 检测内容区域
            logger.info("步骤4: 检测内容区域")
            regions = self.detect_content_regions(screenshot_path, browser_window)
            
            # 步骤5: 可视化检测到的区域
            logger.info("步骤5: 可视化检测到的区域")
            marked_path = self.visualize_detected_regions(screenshot_path, regions)
            
            # 步骤6: 提取区域内容
            logger.info("步骤6: 提取区域内容")
            region_images = self.extract_region_content(screenshot_path, regions)
            
            # 步骤7: 更新自动监控配置
            logger.info("步骤7: 更新自动监控配置")
            self.update_auto_monitor_config(regions)
            
            # 复制最终结果到输出目录
            final_screenshot_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            final_grid_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                f"grid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            final_marked_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                f"marked_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            
            # 复制文件
            img = Image.open(screenshot_path)
            img.save(final_screenshot_path)
            
            img = Image.open(grid_path)
            img.save(final_grid_path)
            
            img = Image.open(marked_path)
            img.save(final_marked_path)
            
            # 返回结果
            result = {
                "success": True,
                "screenshot_path": final_screenshot_path,
                "grid_path": final_grid_path,
                "marked_path": final_marked_path,
                "regions": regions,
                "region_images": region_images
            }
            
            logger.info("校准完成")
            return result
        
        except Exception as e:
            logger.error(f"校准失败: {e}")
            return {"success": False, "error": str(e)}


class WindowsVisualCalibrator(VisualCalibrator):
    """Windows专用视觉校准器类"""
    
    def capture_screenshot(self) -> Optional[str]:
        """
        使用pyautogui捕获屏幕
        
        Returns:
            Optional[str]: 截图文件路径，如果失败则返回None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.temp_dir, f"calibration_screenshot_{timestamp}.png")
            
            # 使用pyautogui捕获全屏
            pyautogui.screenshot(screenshot_path)
            
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
        if self.simple_mode:
            logger.info("使用简化模式，返回默认浏览器信息")
            return {
                "name": "SimpleBrowser",
                "path": "",
                "id": "",
                "position": {"x": 0, "y": 0},
                "size": {"width": 0, "height": 0}
            }
        
        try:
            # 尝试获取活动窗口
            active_window = gw.getActiveWindow()
            
            if active_window:
                browser_info = {
                    "name": active_window.title,
                    "path": "",
                    "id": "",
                    "position": {
                        "x": active_window.left,
                        "y": active_window.top
                    },
                    "size": {
                        "width": active_window.width,
                        "height": active_window.height
                    }
                }
                
                logger.info(f"获取到活动浏览器信息: {browser_info}")
                return browser_info
            else:
                logger.warning("未获取到活动窗口")
                return {
                    "name": "Unknown",
                    "path": "",
                    "id": "",
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 0, "height": 0}
                }
        
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
        if self.simple_mode:
            logger.info("使用简化模式，返回默认URL")
            return "https://manus.im/"
        
        try:
            # 获取活动窗口标题
            active_window = gw.getActiveWindow()
            
            if active_window:
                title = active_window.title
                
                # 尝试从标题中提取URL
                # 常见浏览器标题格式: "页面标题 - 浏览器名称"
                # 或者 "manus.im - Google Chrome"
                if "manus.im" in title.lower():
                    logger.info(f"从窗口标题中检测到manus.im: {title}")
                    return "https://manus.im/"
            
            logger.warning("无法从窗口标题中检测URL")
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
            if self.simple_mode:
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
            
            # 复制到输出目录
            output_grid_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                f"grid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            img = Image.open(grid_path)
            img.save(output_grid_path)
            
            # 提示用户查看网格图像
            print("\n" + "="*80)
            print("请查看网格图像，并记下工作列表和操作列表区域的坐标")
            print(f"网格图像已保存到: {output_grid_path}")
            print("="*80 + "\n")
            
            # 获取浏览器窗口尺寸
            x1, y1, x2, y2 = browser_window
            width = x2 - x1
            height = y2 - y1
            
            # 提示用户输入工作列表区域坐标
            print("请输入工作列表区域坐标 (格式: x1,y1,x2,y2)，或直接按回车使用默认值:")
            work_list_input = input().strip()
            
            if work_list_input:
                try:
                    work_list_coords = [int(x) for x in work_list_input.split(",")]
                    work_list_region = tuple(work_list_coords)
                except:
                    print("输入格式错误，使用默认值")
                    work_list_region = (
                        int(x1 + width * 0.05),
                        int(y1 + height * 0.2),
                        int(x1 + width * 0.45),
                        int(y1 + height * 0.8)
                    )
            else:
                work_list_region = (
                    int(x1 + width * 0.05),
                    int(y1 + height * 0.2),
                    int(x1 + width * 0.45),
                    int(y1 + height * 0.8)
                )
            
            # 提示用户输入操作列表区域坐标
            print("请输入操作列表区域坐标 (格式: x1,y1,x2,y2)，或直接按回车使用默认值:")
            action_list_input = input().strip()
            
            if action_list_input:
                try:
                    action_list_coords = [int(x) for x in action_list_input.split(",")]
                    action_list_region = tuple(action_list_coords)
                except:
                    print("输入格式错误，使用默认值")
                    action_list_region = (
                        int(x1 + width * 0.55),
                        int(y1 + height * 0.2),
                        int(x1 + width * 0.95),
                        int(y1 + height * 0.8)
                    )
            else:
                action_list_region = (
                    int(x1 + width * 0.55),
                    int(y1 + height * 0.2),
                    int(x1 + width * 0.95),
                    int(y1 + height * 0.8)
                )
            
            regions = {
                "work_list": work_list_region,
                "action_list": action_list_region
            }
            
            logger.info(f"手动选择的区域: {regions}")
            return regions
        
        except Exception as e:
            logger.error(f"手动区域选择失败: {e}")
            
            # 获取浏览器窗口尺寸
            x1, y1, x2, y2 = browser_window
            width = x2 - x1
            height = y2 - y1
            
            # 使用默认区域
            regions = {
                "work_list": (
                    int(x1 + width * 0.05),
                    int(y1 + height * 0.2),
                    int(x1 + width * 0.45),
                    int(y1 + height * 0.8)
                ),
                "action_list": (
                    int(x1 + width * 0.55),
                    int(y1 + height * 0.2),
                    int(x1 + width * 0.95),
                    int(y1 + height * 0.8)
                )
            }
            
            logger.info(f"使用默认区域: {regions}")
            return regions


class MacVisualCalibrator(VisualCalibrator):
    """Mac专用视觉校准器类"""
    
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
        if self.simple_mode:
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
        if self.simple_mode:
            logger.info("使用简化模式，返回默认URL")
            return "https://manus.im/"
        
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
            if self.simple_mode:
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
            
            # 复制到输出目录
            output_grid_path = os.path.join(
                self.config.get("log_dir", os.path.expanduser("~/mcp_logs")),
                f"grid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            img = Image.open(grid_path)
            img.save(output_grid_path)
            
            # 提示用户查看网格图像
            print("\n" + "="*80)
            print("请查看网格图像，并记下工作列表和操作列表区域的坐标")
            print(f"网格图像已保存到: {output_grid_path}")
            print("="*80 + "\n")
            
            # 获取浏览器窗口尺寸
            x1, y1, x2, y2 = browser_window
            width = x2 - x1
            height = y2 - y1
            
            # 提示用户输入工作列表区域坐标
            print("请输入工作列表区域坐标 (格式: x1,y1,x2,y2)，或直接按回车使用默认值:")
            work_list_input = input().strip()
            
            if work_list_input:
                try:
                    work_list_coords = [int(x) for x in work_list_input.split(",")]
                    work_list_region = tuple(work_list_coords)
                except:
                    print("输入格式错误，使用默认值")
                    work_list_region = (
                        int(x1 + width * 0.05),
                        int(y1 + height * 0.2),
                        int(x1 + width * 0.45),
                        int(y1 + height * 0.8)
                    )
            else:
                work_list_region = (
                    int(x1 + width * 0.05),
                    int(y1 + height * 0.2),
                    int(x1 + width * 0.45),
                    int(y1 + height * 0.8)
                )
            
            # 提示用户输入操作列表区域坐标
            print("请输入操作列表区域坐标 (格式: x1,y1,x2,y2)，或直接按回车使用默认值:")
            action_list_input = input().strip()
            
            if action_list_input:
                try:
                    action_list_coords = [int(x) for x in action_list_input.split(",")]
                    action_list_region = tuple(action_list_coords)
                except:
                    print("输入格式错误，使用默认值")
                    action_list_region = (
                        int(x1 + width * 0.55),
                        int(y1 + height * 0.2),
                        int(x1 + width * 0.95),
                        int(y1 + height * 0.8)
                    )
            else:
                action_list_region = (
                    int(x1 + width * 0.55),
                    int(y1 + height * 0.2),
                    int(x1 + width * 0.95),
                    int(y1 + height * 0.8)
                )
            
            regions = {
                "work_list": work_list_region,
                "action_list": action_list_region
            }
            
            logger.info(f"手动选择的区域: {regions}")
            return regions
        
        except Exception as e:
            logger.error(f"手动区域选择失败: {e}")
            
            # 获取浏览器窗口尺寸
            x1, y1, x2, y2 = browser_window
            width = x2 - x1
            height = y2 - y1
            
            # 使用默认区域
            regions = {
                "work_list": (
                    int(x1 + width * 0.05),
                    int(y1 + height * 0.2),
                    int(x1 + width * 0.45),
                    int(y1 + height * 0.8)
                ),
                "action_list": (
                    int(x1 + width * 0.55),
                    int(y1 + height * 0.2),
                    int(x1 + width * 0.95),
                    int(y1 + height * 0.8)
                )
            }
            
            logger.info(f"使用默认区域: {regions}")
            return regions


def get_calibrator(config_file=None, output_dir=None, simple_mode=False, manual_regions=False) -> VisualCalibrator:
    """
    获取适合当前平台的视觉校准器实例
    
    Args:
        config_file: 配置文件路径，可选
        output_dir: 输出目录路径，可选
        simple_mode: 是否使用简化模式，可选
        manual_regions: 是否使用手动区域标定模式，可选
    
    Returns:
        VisualCalibrator: 视觉校准器实例
    """
    if PLATFORM == 'windows':
        return WindowsVisualCalibrator(config_file, output_dir, simple_mode, manual_regions)
    elif PLATFORM == 'darwin':
        return MacVisualCalibrator(config_file, output_dir, simple_mode, manual_regions)
    else:
        logger.warning(f"不支持的平台: {PLATFORM}，使用基础校准器")
        return VisualCalibrator(config_file, output_dir, simple_mode, manual_regions)


def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='跨平台视觉校准工具')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--output_dir', help='输出目录路径')
    parser.add_argument('--simple_mode', action='store_true', help='使用简化模式')
    parser.add_argument('--manual_regions', action='store_true', help='使用手动区域标定模式')
    args = parser.parse_args()
    
    # 创建校准器
    calibrator = get_calibrator(args.config, args.output_dir, args.simple_mode, args.manual_regions)
    
    # 运行校准
    result = calibrator.run_calibration()
    
    # 输出结果
    if result["success"]:
        print("\n校准成功!")
        print(f"校准网格: {result['grid_path']}")
        print(f"检测区域: {result['marked_path']}")
        print("区域图像:")
        for name, path in result["region_images"].items():
            print(f"  - {name}: {path}")
        
        # 复制结果到剪贴板
        try:
            regions_str = json.dumps(result["regions"], indent=2)
            if PLATFORM == 'windows':
                import pyperclip
                pyperclip.copy(regions_str)
            elif PLATFORM == 'darwin':
                subprocess.run(["pbcopy"], input=regions_str.encode(), check=True)
            print("\n区域坐标已复制到剪贴板，可直接粘贴使用")
        except Exception as e:
            print(f"复制到剪贴板失败: {e}")
    else:
        print(f"\n校准失败: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()
