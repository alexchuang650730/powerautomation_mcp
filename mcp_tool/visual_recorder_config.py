"""
视觉思考记录器配置工具 - VisualRecorderConfig

该模块提供图形化界面，用于配置视觉思考记录器的监控区域、
捕获频率和OCR参数，支持实时预览和测试。

作者: Manus AI
日期: 2025-05-28
"""

import os
import sys
import json
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VisualRecorderConfig")

class VisualRecorderConfigTool:
    """视觉思考记录器配置工具类"""
    
    def __init__(self, recorder=None, config_file=None):
        """
        初始化配置工具
        
        Args:
            recorder: EnhancedThoughtRecorder或VisualThoughtRecorder实例
            config_file: 配置文件路径
        """
        self.recorder = recorder
        self.config_file = config_file
        self.config = self._load_config()
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("视觉思考记录器配置工具")
        self.root.geometry("800x600")
        
        # 创建界面
        self._create_ui()
        
        # 截图预览
        self.preview_image = None
        self.preview_photo = None
        
        # 区域绘制状态
        self.drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_region = None
        
        # 更新区域列表
        self._update_region_list()
    
    def _load_config(self):
        """加载配置"""
        default_config = {
            "monitor_regions": [
                {"name": "思考区域", "bbox": (100, 100, 800, 600), "type": "thought"},
                {"name": "操作区域", "bbox": (100, 650, 800, 900), "type": "action"}
            ],
            "capture_interval": 1.0,
            "ocr_engine": "tesseract",
            "log_dir": os.path.expanduser("~/mcp_logs")
        }
        
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"已加载配置文件: {self.config_file}")
                return config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        
        return default_config
    
    def _save_config(self):
        """保存配置"""
        if not self.config_file:
            self.config_file = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json")],
                title="保存配置文件"
            )
            if not self.config_file:
                return False
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存配置文件: {self.config_file}")
            messagebox.showinfo("保存成功", f"配置已保存到: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            messagebox.showerror("保存失败", f"保存配置文件失败: {e}")
            return False
    
    def _create_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左侧和右侧面板
        left_frame = ttk.Frame(main_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧面板 - 配置选项
        self._create_config_panel(left_frame)
        
        # 右侧面板 - 预览和绘制区域
        self._create_preview_panel(right_frame)
        
        # 底部按钮
        self._create_button_panel(main_frame)
    
    def _create_config_panel(self, parent):
        """创建配置面板"""
        # 区域列表框架
        regions_frame = ttk.LabelFrame(parent, text="监控区域", padding=5)
        regions_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 区域列表
        self.region_listbox = tk.Listbox(regions_frame, height=10)
        self.region_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.region_listbox.bind('<<ListboxSelect>>', self._on_region_select)
        
        # 区域操作按钮
        region_buttons_frame = ttk.Frame(regions_frame)
        region_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(region_buttons_frame, text="添加", command=self._add_region).pack(side=tk.LEFT, padx=2)
        ttk.Button(region_buttons_frame, text="编辑", command=self._edit_region).pack(side=tk.LEFT, padx=2)
        ttk.Button(region_buttons_frame, text="删除", command=self._delete_region).pack(side=tk.LEFT, padx=2)
        
        # 捕获设置框架
        capture_frame = ttk.LabelFrame(parent, text="捕获设置", padding=5)
        capture_frame.pack(fill=tk.X, pady=5)
        
        # 捕获间隔
        ttk.Label(capture_frame, text="捕获间隔 (秒):").pack(anchor=tk.W, pady=2)
        self.interval_var = tk.StringVar(value=str(self.config.get("capture_interval", 1.0)))
        ttk.Entry(capture_frame, textvariable=self.interval_var).pack(fill=tk.X, pady=2)
        
        # OCR引擎
        ttk.Label(capture_frame, text="OCR引擎:").pack(anchor=tk.W, pady=2)
        self.ocr_engine_var = tk.StringVar(value=self.config.get("ocr_engine", "tesseract"))
        ttk.Combobox(capture_frame, textvariable=self.ocr_engine_var, 
                    values=["tesseract", "easyocr"]).pack(fill=tk.X, pady=2)
        
        # 日志目录
        ttk.Label(capture_frame, text="日志目录:").pack(anchor=tk.W, pady=2)
        log_dir_frame = ttk.Frame(capture_frame)
        log_dir_frame.pack(fill=tk.X, pady=2)
        
        self.log_dir_var = tk.StringVar(value=self.config.get("log_dir", os.path.expanduser("~/mcp_logs")))
        ttk.Entry(log_dir_frame, textvariable=self.log_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(log_dir_frame, text="浏览", command=self._browse_log_dir).pack(side=tk.RIGHT)
    
    def _create_preview_panel(self, parent):
        """创建预览面板"""
        # 预览框架
        preview_frame = ttk.LabelFrame(parent, text="屏幕预览", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg="black")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.preview_canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.preview_canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.preview_canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        
        # 预览控制按钮
        preview_buttons_frame = ttk.Frame(parent)
        preview_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(preview_buttons_frame, text="刷新预览", command=self._refresh_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(preview_buttons_frame, text="测试OCR", command=self._test_ocr).pack(side=tk.LEFT, padx=2)
    
    def _create_button_panel(self, parent):
        """创建底部按钮面板"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="应用配置", command=self._apply_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="保存配置", command=self._save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.root.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _update_region_list(self):
        """更新区域列表"""
        self.region_listbox.delete(0, tk.END)
        for region in self.config.get("monitor_regions", []):
            self.region_listbox.insert(tk.END, f"{region['name']} ({region['type']})")
    
    def _on_region_select(self, event):
        """区域选择事件"""
        if not self.preview_image:
            return
        
        # 获取选中的区域
        selection = self.region_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.config.get("monitor_regions", [])):
            region = self.config["monitor_regions"][index]
            
            # 在预览中高亮显示选中的区域
            self._refresh_preview()
            bbox = region["bbox"]
            self.preview_canvas.create_rectangle(
                bbox[0], bbox[1], bbox[2], bbox[3],
                outline="red", width=2
            )
    
    def _add_region(self):
        """添加新区域"""
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("添加监控区域")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 区域名称
        ttk.Label(dialog, text="区域名称:").pack(anchor=tk.W, pady=2, padx=10)
        name_var = tk.StringVar(value="新区域")
        ttk.Entry(dialog, textvariable=name_var).pack(fill=tk.X, pady=2, padx=10)
        
        # 区域类型
        ttk.Label(dialog, text="区域类型:").pack(anchor=tk.W, pady=2, padx=10)
        type_var = tk.StringVar(value="thought")
        ttk.Combobox(dialog, textvariable=type_var, 
                    values=["thought", "action"]).pack(fill=tk.X, pady=2, padx=10)
        
        # 区域坐标
        ttk.Label(dialog, text="坐标 (x1, y1, x2, y2):").pack(anchor=tk.W, pady=2, padx=10)
        coords_frame = ttk.Frame(dialog)
        coords_frame.pack(fill=tk.X, pady=2, padx=10)
        
        x1_var = tk.StringVar(value="100")
        y1_var = tk.StringVar(value="100")
        x2_var = tk.StringVar(value="500")
        y2_var = tk.StringVar(value="300")
        
        ttk.Entry(coords_frame, textvariable=x1_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Entry(coords_frame, textvariable=y1_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Entry(coords_frame, textvariable=x2_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Entry(coords_frame, textvariable=y2_var, width=5).pack(side=tk.LEFT, padx=2)
        
        # 提示
        ttk.Label(dialog, text="提示: 也可以在预览中直接绘制区域").pack(pady=5, padx=10)
        
        # 按钮
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill=tk.X, pady=10, padx=10)
        
        def on_ok():
            try:
                x1 = int(x1_var.get())
                y1 = int(y1_var.get())
                x2 = int(x2_var.get())
                y2 = int(y2_var.get())
                
                # 添加新区域
                new_region = {
                    "name": name_var.get(),
                    "type": type_var.get(),
                    "bbox": (x1, y1, x2, y2)
                }
                
                if "monitor_regions" not in self.config:
                    self.config["monitor_regions"] = []
                
                self.config["monitor_regions"].append(new_region)
                self._update_region_list()
                
                dialog.destroy()
                
                # 刷新预览
                self._refresh_preview()
            except ValueError:
                messagebox.showerror("输入错误", "坐标必须是整数")
        
        ttk.Button(buttons_frame, text="确定", command=on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _edit_region(self):
        """编辑选中的区域"""
        # 获取选中的区域
        selection = self.region_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个区域")
            return
        
        index = selection[0]
        if index >= len(self.config.get("monitor_regions", [])):
            return
        
        region = self.config["monitor_regions"][index]
        
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑监控区域")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 区域名称
        ttk.Label(dialog, text="区域名称:").pack(anchor=tk.W, pady=2, padx=10)
        name_var = tk.StringVar(value=region["name"])
        ttk.Entry(dialog, textvariable=name_var).pack(fill=tk.X, pady=2, padx=10)
        
        # 区域类型
        ttk.Label(dialog, text="区域类型:").pack(anchor=tk.W, pady=2, padx=10)
        type_var = tk.StringVar(value=region["type"])
        ttk.Combobox(dialog, textvariable=type_var, 
                    values=["thought", "action"]).pack(fill=tk.X, pady=2, padx=10)
        
        # 区域坐标
        ttk.Label(dialog, text="坐标 (x1, y1, x2, y2):").pack(anchor=tk.W, pady=2, padx=10)
        coords_frame = ttk.Frame(dialog)
        coords_frame.pack(fill=tk.X, pady=2, padx=10)
        
        bbox = region["bbox"]
        x1_var = tk.StringVar(value=str(bbox[0]))
        y1_var = tk.StringVar(value=str(bbox[1]))
        x2_var = tk.StringVar(value=str(bbox[2]))
        y2_var = tk.StringVar(value=str(bbox[3]))
        
        ttk.Entry(coords_frame, textvariable=x1_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Entry(coords_frame, textvariable=y1_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Entry(coords_frame, textvariable=x2_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Entry(coords_frame, textvariable=y2_var, width=5).pack(side=tk.LEFT, padx=2)
        
        # 提示
        ttk.Label(dialog, text="提示: 也可以在预览中直接绘制区域").pack(pady=5, padx=10)
        
        # 按钮
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill=tk.X, pady=10, padx=10)
        
        def on_ok():
            try:
                x1 = int(x1_var.get())
                y1 = int(y1_var.get())
                x2 = int(x2_var.get())
                y2 = int(y2_var.get())
                
                # 更新区域
                self.config["monitor_regions"][index] = {
                    "name": name_var.get(),
                    "type": type_var.get(),
                    "bbox": (x1, y1, x2, y2)
                }
                
                self._update_region_list()
                
                dialog.destroy()
                
                # 刷新预览
                self._refresh_preview()
            except ValueError:
                messagebox.showerror("输入错误", "坐标必须是整数")
        
        ttk.Button(buttons_frame, text="确定", command=on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _delete_region(self):
        """删除选中的区域"""
        # 获取选中的区域
        selection = self.region_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个区域")
            return
        
        index = selection[0]
        if index >= len(self.config.get("monitor_regions", [])):
            return
        
        # 确认删除
        region = self.config["monitor_regions"][index]
        if not messagebox.askyesno("确认删除", f"确定要删除区域 '{region['name']}' 吗?"):
            return
        
        # 删除区域
        del self.config["monitor_regions"][index]
        self._update_region_list()
        
        # 刷新预览
        self._refresh_preview()
    
    def _browse_log_dir(self):
        """浏览日志目录"""
        directory = filedialog.askdirectory(
            initialdir=self.log_dir_var.get(),
            title="选择日志目录"
        )
        if directory:
            self.log_dir_var.set(directory)
    
    def _refresh_preview(self):
        """刷新预览"""
        try:
            # 截取屏幕
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            
            # 调整大小以适应画布
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # 画布尚未完全初始化，使用默认大小
                canvas_width = 500
                canvas_height = 400
            
            # 计算缩放比例
            scale_width = canvas_width / screenshot.width
            scale_height = canvas_height / screenshot.height
            scale = min(scale_width, scale_height)
            
            # 缩放图像
            new_width = int(screenshot.width * scale)
            new_height = int(screenshot.height * scale)
            resized_image = screenshot.resize((new_width, new_height), Image.LANCZOS)
            
            # 更新预览
            self.preview_image = resized_image
            self.preview_photo = ImageTk.PhotoImage(resized_image)
            
            # 清除画布并显示新图像
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_width // 2, canvas_height // 2,
                image=self.preview_photo,
                anchor=tk.CENTER
            )
            
            # 绘制所有区域
            for region in self.config.get("monitor_regions", []):
                bbox = region["bbox"]
                # 缩放坐标
                x1 = int(bbox[0] * scale)
                y1 = int(bbox[1] * scale)
                x2 = int(bbox[2] * scale)
                y2 = int(bbox[3] * scale)
                
                # 绘制矩形
                color = "red" if region["type"] == "thought" else "blue"
                self.preview_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline=color, width=2
                )
                
                # 绘制标签
                self.preview_canvas.create_text(
                    x1 + 5, y1 + 5,
                    text=region["name"],
                    anchor=tk.NW,
                    fill=color
                )
            
            # 保存缩放比例
            self.scale = scale
            
        except Exception as e:
            logger.error(f"刷新预览失败: {e}")
            messagebox.showerror("刷新失败", f"刷新预览失败: {e}")
    
    def _test_ocr(self):
        """测试OCR"""
        # 获取选中的区域
        selection = self.region_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个区域")
            return
        
        index = selection[0]
        if index >= len(self.config.get("monitor_regions", [])):
            return
        
        region = self.config["monitor_regions"][index]
        
        try:
            # 截取屏幕区域
            from PIL import ImageGrab
            screenshot = ImageGrab.grab(bbox=region["bbox"])
            
            # 执行OCR
            ocr_engine = self.ocr_engine_var.get()
            
            if ocr_engine == "tesseract":
                try:
                    import pytesseract
                    text = pytesseract.image_to_string(screenshot, lang='chi_sim+eng')
                except ImportError:
                    messagebox.showerror("OCR错误", "未安装pytesseract，请先安装: pip install pytesseract")
                    return
            elif ocr_engine == "easyocr":
                try:
                    import easyocr
                    reader = easyocr.Reader(['ch_sim', 'en'])
                    results = reader.readtext(screenshot)
                    text = "\n".join([result[1] for result in results])
                except ImportError:
                    messagebox.showerror("OCR错误", "未安装easyocr，请先安装: pip install easyocr")
                    return
            else:
                messagebox.showerror("OCR错误", f"不支持的OCR引擎: {ocr_engine}")
                return
            
            # 显示结果
            result_dialog = tk.Toplevel(self.root)
            result_dialog.title(f"OCR结果 - {region['name']}")
            result_dialog.geometry("400x300")
            result_dialog.transient(self.root)
            
            # 图像预览
            preview_frame = ttk.LabelFrame(result_dialog, text="截图预览", padding=5)
            preview_frame.pack(fill=tk.X, pady=5, padx=10)
            
            # 调整图像大小
            max_width = 380
            max_height = 100
            
            width, height = screenshot.size
            if width > max_width:
                scale = max_width / width
                width = max_width
                height = int(height * scale)
            
            if height > max_height:
                scale = max_height / height
                height = int(height * scale)
                width = int(width * scale)
            
            resized = screenshot.resize((width, height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized)
            
            preview_label = ttk.Label(preview_frame, image=photo)
            preview_label.image = photo  # 保持引用
            preview_label.pack(pady=5)
            
            # 文本结果
            text_frame = ttk.LabelFrame(result_dialog, text="OCR文本结果", padding=5)
            text_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, pady=5)
            text_widget.insert(tk.END, text)
            
            # 按钮
            ttk.Button(result_dialog, text="关闭", command=result_dialog.destroy).pack(pady=10)
            
        except Exception as e:
            logger.error(f"OCR测试失败: {e}")
            messagebox.showerror("OCR测试失败", f"OCR测试失败: {e}")
    
    def _on_mouse_down(self, event):
        """鼠标按下事件"""
        if not self.preview_image:
            return
        
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
        
        # 创建临时矩形
        self.current_region = self.preview_canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="green", width=2
        )
    
    def _on_mouse_move(self, event):
        """鼠标移动事件"""
        if not self.drawing or not self.current_region:
            return
        
        # 更新临时矩形
        self.preview_canvas.coords(
            self.current_region,
            self.start_x, self.start_y, event.x, event.y
        )
    
    def _on_mouse_up(self, event):
        """鼠标释放事件"""
        if not self.drawing or not self.current_region:
            return
        
        self.drawing = False
        
        # 获取矩形坐标
        x1, y1, x2, y2 = self.start_x, self.start_y, event.x, event.y
        
        # 确保x1 <= x2, y1 <= y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # 如果矩形太小，忽略
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            self.preview_canvas.delete(self.current_region)
            self.current_region = None
            return
        
        # 转换回实际坐标
        real_x1 = int(x1 / self.scale)
        real_y1 = int(y1 / self.scale)
        real_x2 = int(x2 / self.scale)
        real_y2 = int(y2 / self.scale)
        
        # 创建新区域对话框
        self._create_region_from_drawing(real_x1, real_y1, real_x2, real_y2)
        
        # 删除临时矩形
        self.preview_canvas.delete(self.current_region)
        self.current_region = None
    
    def _create_region_from_drawing(self, x1, y1, x2, y2):
        """从绘制创建新区域"""
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("创建新区域")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 区域名称
        ttk.Label(dialog, text="区域名称:").pack(anchor=tk.W, pady=2, padx=10)
        name_var = tk.StringVar(value="新区域")
        ttk.Entry(dialog, textvariable=name_var).pack(fill=tk.X, pady=2, padx=10)
        
        # 区域类型
        ttk.Label(dialog, text="区域类型:").pack(anchor=tk.W, pady=2, padx=10)
        type_var = tk.StringVar(value="thought")
        ttk.Combobox(dialog, textvariable=type_var, 
                    values=["thought", "action"]).pack(fill=tk.X, pady=2, padx=10)
        
        # 按钮
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill=tk.X, pady=10, padx=10)
        
        def on_ok():
            # 添加新区域
            new_region = {
                "name": name_var.get(),
                "type": type_var.get(),
                "bbox": (x1, y1, x2, y2)
            }
            
            if "monitor_regions" not in self.config:
                self.config["monitor_regions"] = []
            
            self.config["monitor_regions"].append(new_region)
            self._update_region_list()
            
            dialog.destroy()
            
            # 刷新预览
            self._refresh_preview()
        
        ttk.Button(buttons_frame, text="确定", command=on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _apply_config(self):
        """应用配置到记录器"""
        try:
            # 更新配置
            self.config["capture_interval"] = float(self.interval_var.get())
            self.config["ocr_engine"] = self.ocr_engine_var.get()
            self.config["log_dir"] = self.log_dir_var.get()
            
            # 如果有记录器实例，应用配置
            if self.recorder:
                # 应用日志目录
                self.recorder.log_dir = self.config["log_dir"]
                
                # 应用监控区域
                if hasattr(self.recorder, 'set_monitor_regions'):
                    self.recorder.set_monitor_regions(self.config["monitor_regions"])
                elif hasattr(self.recorder, 'visual_recorder') and self.recorder.visual_recorder:
                    self.recorder.visual_recorder.set_monitor_regions(self.config["monitor_regions"])
                
                # 应用捕获间隔
                if hasattr(self.recorder, 'set_capture_interval'):
                    self.recorder.set_capture_interval(self.config["capture_interval"])
                elif hasattr(self.recorder, 'visual_recorder') and self.recorder.visual_recorder:
                    self.recorder.visual_recorder.set_capture_interval(self.config["capture_interval"])
                
                messagebox.showinfo("应用成功", "配置已应用到记录器")
            else:
                messagebox.showinfo("配置已更新", "配置已更新，但未应用到记录器（记录器实例未提供）")
        except Exception as e:
            logger.error(f"应用配置失败: {e}")
            messagebox.showerror("应用失败", f"应用配置失败: {e}")
    
    def run(self):
        """运行配置工具"""
        # 刷新预览
        self.root.after(500, self._refresh_preview)
        
        # 启动主循环
        self.root.mainloop()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="视觉思考记录器配置工具")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args()
    
    # 创建配置工具
    config_tool = VisualRecorderConfigTool(config_file=args.config)
    
    # 运行配置工具
    config_tool.run()


if __name__ == "__main__":
    main()
