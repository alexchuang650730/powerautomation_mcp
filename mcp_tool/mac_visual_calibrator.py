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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MacVisualCalibrator")

class MacVisualCalibrator:
    """Mac专用视觉校准器类"""
    
    def __init__(self, config_file=None):
        """
        初始化Mac视觉校准器
        
        Args:
            config_file: 配置文件路径，可选
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.temp_dir = tempfile.mkdtemp(prefix="mac_visual_calibration_")
        
        # 创建日志目录
        os.makedirs(self.config.get("log_dir", os.path.expanduser("~/mcp_logs")), exist_ok=True)
        
        logger.info("Mac视觉校准器初始化完成")
        logger.info(f"临时文件目录: {self.temp_dir}")
        logger.info(f"日志目录: {self.config.get('log_dir', os.path.expanduser('~/mcp_logs'))}")
    
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
            "action_list_css_selector": ".action-list-container"  # 操作列表CSS选择器
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
                "mac_visual_calibration.json"
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
            
            # 获取当前URL
            url = self.get_browser_url()
            
            # 检查是否为目标网站
            if url and "manus.im" in url:
                logger.info(f"检测到目标网站: {url}")
                
                # 根据manus.im网站的布局估计区域位置
                # 工作列表通常在左侧
                work_list_x1 = x1 + width * 0.05  # 左边缘偏移5%
                work_list_y1 = y1 + height * 0.2  # 顶部偏移20%
                work_list_x2 = x1 + width * 0.45  # 宽度为40%
                work_list_y2 = y1 + height * 0.8  # 高度为60%
                
                # 操作列表通常在右侧
                action_list_x1 = x1 + width * 0.55  # 左边缘偏移55%
                action_list_y1 = y1 + height * 0.2  # 顶部偏移20%
                action_list_x2 = x1 + width * 0.95  # 宽度为40%
                action_list_y2 = y1 + height * 0.8  # 高度为60%
                
                regions = {
                    "work_list": (int(work_list_x1), int(work_list_y1), int(work_list_x2), int(work_list_y2)),
                    "action_list": (int(action_list_x1), int(action_list_y1), int(action_list_x2), int(action_list_y2))
                }
            else:
                logger.warning(f"未检测到目标网站，当前URL: {url}")
                
                # 使用默认区域
                work_list_region = (x1 + width // 10, y1 + height // 4, x1 + width // 2 - width // 10, y2 - height // 4)
                action_list_region = (x1 + width // 2 + width // 10, y1 + height // 4, x2 - width // 10, y2 - height // 4)
                
                regions = {
                    "work_list": work_list_region,
                    "action_list": action_list_region
                }
            
            logger.info(f"检测到内容区域: {regions}")
            return regions
        
        except Exception as e:
            logger.error(f"检测内容区域失败: {e}")
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
            auto_monitor_config["platform"] = "mac"
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
            
            # 返回结果
            result = {
                "success": True,
                "screenshot_path": screenshot_path,
                "grid_path": grid_path,
                "marked_path": marked_path,
                "regions": regions,
                "region_images": region_images
            }
            
            logger.info("校准完成")
            return result
        
        except Exception as e:
            logger.error(f"校准失败: {e}")
            return {"success": False, "error": str(e)}

def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='Mac专用视觉校准工具')
    parser.add_argument('--config', help='配置文件路径')
    args = parser.parse_args()
    
    # 创建校准器
    calibrator = MacVisualCalibrator(args.config)
    
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
            subprocess.run(["pbcopy"], input=regions_str.encode(), check=True)
            print("\n区域坐标已复制到剪贴板，可直接粘贴使用")
        except Exception as e:
            print(f"复制到剪贴板失败: {e}")
    else:
        print(f"\n校准失败: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    main()
