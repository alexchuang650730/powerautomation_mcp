"""
图形化区域选择工具 - GUI Region Selector

提供类似Mac截图工具的交互式区域选择体验，支持Windows和Mac平台。
用户可以直接在屏幕上拖动选择区域，实时显示坐标和尺寸信息。

作者: Manus AI
日期: 2025-05-30
"""

import os
import sys
import json
import time
import platform
import logging
import argparse
import tempfile
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageGrab

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GUIRegionSelector')

# 确定当前平台
PLATFORM = platform.system().lower()

class GUIRegionSelector:
    """图形化区域选择工具基类"""
    
    def __init__(self, output_dir: str = None, config_file: str = None):
        """
        初始化图形化区域选择工具
        
        Args:
            output_dir: 输出目录路径
            config_file: 配置文件路径
        """
        self.output_dir = output_dir or os.path.join(os.path.expanduser("~"), "mcp_logs")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.config_file = config_file
        self.config = self._load_config()
        
        # 截图和区域信息
        self.screenshot_path = None
        self.regions = {}
        
        # 当前选择的区域名称
        self.current_region_name = None
        self.region_names = ["work_list", "action_list"]
        self.region_index = 0
        
        # GUI相关
        self.root = None
        self.canvas = None
        self.image = None
        self.photo = None
        self.rect_id = None
        self.start_x = 0
        self.start_y = 0
        self.current_x = 0
        self.current_y = 0
        self.is_selecting = False
        
        # 坐标和尺寸标签
        self.coord_label = None
        self.size_label = None
        
        logger.info(f"初始化GUI区域选择工具，平台: {PLATFORM}, 输出目录: {self.output_dir}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        config = {
            "platform": PLATFORM,
            "monitor_regions": [],
            "interval": 60,
            "log_dir": self.output_dir
        }
        
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    config.update(loaded_config)
                logger.info(f"从 {self.config_file} 加载配置成功")
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
        
        return config
    
    def _save_config(self) -> bool:
        """
        保存配置
        
        Returns:
            bool: 是否保存成功
        """
        # 更新配置中的区域信息
        self.config["monitor_regions"] = []
        for name, bbox in self.regions.items():
            self.config["monitor_regions"].append({
                "name": name,
                "bbox": bbox
            })
        
        # 确定配置文件路径
        config_path = self.config_file or os.path.join(self.output_dir, "auto_web_monitor_config.json")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"配置已保存到 {config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def capture_screenshot(self) -> str:
        """
        捕获屏幕截图
        
        Returns:
            str: 截图文件路径
        """
        # 在子类中实现平台特定的截图功能
        raise NotImplementedError("在子类中实现")
    
    def start_gui(self):
        """启动图形界面"""
        # 捕获屏幕截图
        self.screenshot_path = self.capture_screenshot()
        if not self.screenshot_path or not os.path.exists(self.screenshot_path):
            logger.error("截图失败，无法启动GUI")
            return False
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("区域选择工具")
        
        # 加载截图
        self.image = Image.open(self.screenshot_path)
        self.photo = ImageTk.PhotoImage(self.image)
        
        # 创建画布
        self.canvas = tk.Canvas(self.root, width=self.image.width, height=self.image.height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.pack()
        
        # 创建坐标和尺寸标签
        self.coord_label = tk.Label(self.root, text="坐标: (0, 0)")
        self.coord_label.pack(side=tk.LEFT, padx=10)
        
        self.size_label = tk.Label(self.root, text="尺寸: 0 x 0")
        self.size_label.pack(side=tk.LEFT, padx=10)
        
        # 当前区域标签
        self.region_label = tk.Label(self.root, text=f"当前选择: {self.region_names[self.region_index]}")
        self.region_label.pack(side=tk.LEFT, padx=10)
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # 绑定键盘事件
        self.root.bind("<Escape>", self.on_escape)
        self.root.bind("<Return>", self.on_enter)
        
        # 设置当前区域名称
        self.current_region_name = self.region_names[self.region_index]
        
        # 显示说明
        instructions = """
        使用说明:
        1. 拖动鼠标选择区域
        2. 按Enter确认当前区域并继续下一个
        3. 按Esc取消选择
        4. 所有区域选择完成后自动保存
        """
        tk.Label(self.root, text=instructions, justify=tk.LEFT).pack(side=tk.BOTTOM, padx=10, pady=10)
        
        # 启动主循环
        self.root.mainloop()
        
        return True
    
    def on_mouse_down(self, event):
        """鼠标按下事件"""
        self.start_x = event.x
        self.start_y = event.y
        self.is_selecting = True
        
        # 创建矩形
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )
        
        # 更新坐标标签
        self.coord_label.config(text=f"坐标: ({self.start_x}, {self.start_y})")
    
    def on_mouse_move(self, event):
        """鼠标移动事件"""
        if not self.is_selecting:
            return
        
        self.current_x = event.x
        self.current_y = event.y
        
        # 更新矩形
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, self.current_x, self.current_y)
        
        # 更新坐标和尺寸标签
        width = abs(self.current_x - self.start_x)
        height = abs(self.current_y - self.start_y)
        self.coord_label.config(text=f"坐标: ({min(self.start_x, self.current_x)}, {min(self.start_y, self.current_y)})")
        self.size_label.config(text=f"尺寸: {width} x {height}")
    
    def on_mouse_up(self, event):
        """鼠标释放事件"""
        if not self.is_selecting:
            return
        
        self.current_x = event.x
        self.current_y = event.y
        self.is_selecting = False
        
        # 确保坐标正确（左上角和右下角）
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)
        
        # 更新矩形
        self.canvas.coords(self.rect_id, x1, y1, x2, y2)
        
        # 保存当前区域坐标
        self.regions[self.current_region_name] = [x1, y1, x2, y2]
        
        # 提示用户按Enter确认
        tk.messagebox.showinfo("区域选择", f"{self.current_region_name} 区域已选择，按Enter确认并继续")
    
    def on_escape(self, event):
        """Esc键事件"""
        # 取消当前选择
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        
        self.is_selecting = False
        self.coord_label.config(text="坐标: (0, 0)")
        self.size_label.config(text="尺寸: 0 x 0")
    
    def on_enter(self, event):
        """Enter键事件"""
        # 确认当前区域并继续下一个
        if self.current_region_name in self.regions:
            self.region_index += 1
            
            # 检查是否所有区域都已选择
            if self.region_index >= len(self.region_names):
                # 保存配置并关闭窗口
                self._save_config()
                self.root.destroy()
                return
            
            # 更新当前区域名称
            self.current_region_name = self.region_names[self.region_index]
            self.region_label.config(text=f"当前选择: {self.current_region_name}")
            
            # 清除当前矩形
            if self.rect_id:
                self.canvas.delete(self.rect_id)
                self.rect_id = None
            
            self.is_selecting = False
            self.coord_label.config(text="坐标: (0, 0)")
            self.size_label.config(text="尺寸: 0 x 0")
    
    def run(self) -> Dict[str, Any]:
        """
        运行图形化区域选择工具
        
        Returns:
            Dict[str, Any]: 结果字典
        """
        result = {
            "success": False,
            "error": None,
            "regions": {},
            "config_path": None
        }
        
        try:
            # 启动GUI
            if not self.start_gui():
                result["error"] = "启动GUI失败"
                return result
            
            # 保存配置
            config_path = self.config_file or os.path.join(self.output_dir, "auto_web_monitor_config.json")
            result["config_path"] = config_path
            result["regions"] = self.regions
            result["success"] = True
            
            logger.info(f"区域选择完成: {self.regions}")
            
        except Exception as e:
            logger.error(f"运行图形化区域选择工具失败: {e}")
            result["error"] = str(e)
        
        return result


class WindowsGUIRegionSelector(GUIRegionSelector):
    """Windows平台图形化区域选择工具"""
    
    def capture_screenshot(self) -> str:
        """
        捕获屏幕截图
        
        Returns:
            str: 截图文件路径
        """
        try:
            # 使用PIL的ImageGrab捕获屏幕
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.output_dir, f"screenshot_{timestamp}.png")
            
            # 捕获全屏
            screenshot = ImageGrab.grab()
            screenshot.save(screenshot_path)
            
            logger.info(f"截图已保存: {screenshot_path}")
            return screenshot_path
        
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None


class MacGUIRegionSelector(GUIRegionSelector):
    """Mac平台图形化区域选择工具"""
    
    def capture_screenshot(self) -> str:
        """
        捕获屏幕截图
        
        Returns:
            str: 截图文件路径
        """
        try:
            import subprocess
            
            # 使用screencapture命令捕获屏幕
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.output_dir, f"screenshot_{timestamp}.png")
            
            # 捕获全屏
            subprocess.run(["screencapture", "-x", screenshot_path], check=True)
            
            logger.info(f"截图已保存: {screenshot_path}")
            return screenshot_path
        
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None


def get_gui_selector(output_dir: str = None, config_file: str = None) -> GUIRegionSelector:
    """
    获取适合当前平台的图形化区域选择工具
    
    Args:
        output_dir: 输出目录路径
        config_file: 配置文件路径
    
    Returns:
        GUIRegionSelector: 图形化区域选择工具实例
    """
    if PLATFORM == "windows":
        return WindowsGUIRegionSelector(output_dir, config_file)
    elif PLATFORM == "darwin":
        return MacGUIRegionSelector(output_dir, config_file)
    else:
        # 默认使用基类
        return GUIRegionSelector(output_dir, config_file)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="图形化区域选择工具")
    parser.add_argument("--output_dir", help="输出目录路径")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    # 获取适合当前平台的图形化区域选择工具
    selector = get_gui_selector(args.output_dir, args.config)
    
    # 运行工具
    result = selector.run()
    
    if result["success"]:
        print("\n区域选择成功!")
        print(f"配置文件: {result['config_path']}")
        print("选择的区域:")
        for name, bbox in result["regions"].items():
            print(f"  - {name}: {bbox}")
    else:
        print(f"\n区域选择失败: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()
