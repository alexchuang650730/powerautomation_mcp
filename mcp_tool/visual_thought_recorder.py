"""
视觉思考记录器模块 - VisualThoughtRecorder

该模块通过OCR和屏幕捕获技术，实时监控Manus界面，
自动识别并记录思考过程和操作结果。

主要功能：
1. 屏幕捕获与OCR识别
2. 智能信息分类
3. 实时监控机制
4. 与现有ThoughtActionRecorder集成

作者: Manus AI
日期: 2025-05-28
"""

import os
import time
import json
import logging
import threading
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from queue import Queue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VisualThoughtRecorder")

class VisualThoughtRecorder:
    """
    视觉思考记录器类，通过OCR和屏幕捕获技术，
    实时监控Manus界面，自动识别并记录思考过程和操作结果。
    """
    
    def __init__(self, 
                 log_dir: str,
                 monitor_regions: Optional[List[Dict[str, Any]]] = None,
                 capture_interval: float = 1.0,
                 ocr_engine: str = "tesseract",
                 enable_visual_capture: bool = True,
                 thought_action_recorder = None):
        """
        初始化视觉思考记录器
        
        Args:
            log_dir: 日志存储目录
            monitor_regions: 监控区域列表，每个区域是一个字典，包含区域名称、坐标和类型
                例如：[{"name": "思考区域", "bbox": (100, 100, 800, 600), "type": "thought"}]
            capture_interval: 捕获间隔（秒）
            ocr_engine: OCR引擎，支持"tesseract"和"easyocr"
            enable_visual_capture: 是否启用视觉捕获
            thought_action_recorder: ThoughtActionRecorder实例，用于记录识别到的思考和操作
        """
        self.log_dir = log_dir
        self.capture_interval = capture_interval
        self.ocr_engine_name = ocr_engine
        self.enable_visual_capture = enable_visual_capture
        self.thought_action_recorder = thought_action_recorder
        
        # 设置默认监控区域
        self.monitor_regions = monitor_regions or [
            {"name": "思考区域", "bbox": (100, 100, 800, 600), "type": "thought"},
            {"name": "操作区域", "bbox": (100, 650, 800, 900), "type": "action"}
        ]
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 初始化OCR引擎
        self.ocr_engine = self._init_ocr_engine()
        
        # 初始化屏幕捕获工具
        self.screen_grabber = self._init_screen_grabber()
        
        # 监控线程
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # 处理队列
        self.processing_queue = Queue()
        self.processor_thread = None
        
        # 上次捕获的文本，用于变化检测
        self.last_captured_texts = {}
        
        # 如果启用视觉捕获，启动监控线程
        if enable_visual_capture and self.ocr_engine and self.screen_grabber:
            self._start_monitor()
    
    def _init_ocr_engine(self):
        """初始化OCR引擎"""
        try:
            if self.ocr_engine_name == "tesseract":
                import pytesseract
                logger.info("使用Tesseract OCR引擎")
                return pytesseract
            elif self.ocr_engine_name == "easyocr":
                import easyocr
                logger.info("使用EasyOCR引擎")
                return easyocr.Reader(['ch_sim', 'en'])
            else:
                logger.error(f"不支持的OCR引擎: {self.ocr_engine_name}")
                return None
        except ImportError as e:
            logger.error(f"导入OCR引擎失败: {e}")
            logger.error("请安装所需依赖: pip install pytesseract pillow 或 pip install easyocr")
            return None
    
    def _init_screen_grabber(self):
        """初始化屏幕捕获工具"""
        try:
            from PIL import ImageGrab
            logger.info("使用PIL.ImageGrab进行屏幕捕获")
            return ImageGrab
        except ImportError:
            try:
                import pyscreenshot as ImageGrab
                logger.info("使用pyscreenshot进行屏幕捕获")
                return ImageGrab
            except ImportError:
                logger.error("导入屏幕捕获工具失败")
                logger.error("请安装所需依赖: pip install pillow 或 pip install pyscreenshot")
                return None
    
    def _start_monitor(self):
        """启动监控线程"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("监控线程已在运行")
            return
        
        # 重置停止事件
        self.stop_event.clear()
        
        # 启动处理线程
        self.processor_thread = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self.processor_thread.start()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("视觉监控线程已启动")
    
    def stop_monitor(self):
        """停止监控线程"""
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            logger.warning("监控线程未运行")
            return
        
        # 设置停止事件
        self.stop_event.set()
        
        # 等待线程结束
        self.monitor_thread.join(timeout=5.0)
        if self.processor_thread:
            self.processor_thread.join(timeout=5.0)
        
        logger.info("视觉监控线程已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while not self.stop_event.is_set():
            try:
                # 捕获所有监控区域
                for region in self.monitor_regions:
                    region_name = region["name"]
                    region_bbox = region["bbox"]
                    region_type = region["type"]
                    
                    # 捕获屏幕区域
                    screenshot = self.screen_grabber.grab(bbox=region_bbox)
                    
                    # 将任务添加到处理队列
                    self.processing_queue.put({
                        "screenshot": screenshot,
                        "region_name": region_name,
                        "region_type": region_type,
                        "timestamp": time.time()
                    })
                
                # 等待下一次捕获
                time.sleep(self.capture_interval)
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(self.capture_interval * 2)  # 出错后等待更长时间
    
    def _process_queue(self):
        """处理队列中的截图任务"""
        while not self.stop_event.is_set() or not self.processing_queue.empty():
            try:
                # 获取任务，最多等待1秒
                try:
                    task = self.processing_queue.get(timeout=1.0)
                except:
                    continue
                
                # 处理截图
                screenshot = task["screenshot"]
                region_name = task["region_name"]
                region_type = task["region_type"]
                timestamp = task["timestamp"]
                
                # OCR识别文本
                text = self._perform_ocr(screenshot)
                
                # 如果文本为空，跳过
                if not text or not text.strip():
                    self.processing_queue.task_done()
                    continue
                
                # 检查文本是否有变化
                if region_name in self.last_captured_texts and self.last_captured_texts[region_name] == text:
                    # 文本没有变化，跳过
                    self.processing_queue.task_done()
                    continue
                
                # 更新上次捕获的文本
                self.last_captured_texts[region_name] = text
                
                # 处理识别到的文本
                self._process_recognized_text(text, region_type, region_name, timestamp)
                
                # 标记任务完成
                self.processing_queue.task_done()
            except Exception as e:
                logger.error(f"处理队列异常: {e}")
                time.sleep(0.5)  # 出错后短暂等待
    
    def _perform_ocr(self, image):
        """执行OCR识别"""
        try:
            if self.ocr_engine_name == "tesseract":
                # 使用Tesseract OCR
                text = self.ocr_engine.image_to_string(image, lang='chi_sim+eng')
                return text
            elif self.ocr_engine_name == "easyocr":
                # 使用EasyOCR
                results = self.ocr_engine.readtext(image)
                text = " ".join([result[1] for result in results])
                return text
            else:
                logger.error(f"不支持的OCR引擎: {self.ocr_engine_name}")
                return ""
        except Exception as e:
            logger.error(f"OCR识别异常: {e}")
            return ""
    
    def _process_recognized_text(self, text, region_type, region_name, timestamp):
        """处理识别到的文本"""
        # 清理文本
        cleaned_text = self._clean_text(text)
        
        # 保存原始OCR结果到日志文件
        self._save_ocr_result(cleaned_text, region_name, timestamp)
        
        # 根据区域类型处理文本
        if region_type == "thought":
            # 处理思考文本
            self._process_thought_text(cleaned_text, timestamp)
        elif region_type == "action":
            # 处理操作文本
            self._process_action_text(cleaned_text, timestamp)
        else:
            # 未知类型，作为一般信息处理
            logger.info(f"未知区域类型 '{region_type}' 的文本: {cleaned_text[:50]}...")
    
    def _clean_text(self, text):
        """清理文本"""
        # 移除多余的空白字符
        text = " ".join(text.split())
        # 移除特殊字符
        text = text.replace('\n', ' ').replace('\r', ' ')
        return text
    
    def _save_ocr_result(self, text, region_name, timestamp):
        """保存OCR结果到日志文件"""
        # 创建日志文件名
        date_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d')
        log_file = os.path.join(self.log_dir, f"ocr_{date_str}.log")
        
        # 格式化时间戳
        time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # 写入日志
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{time_str}] [{region_name}] {text}\n")
        except Exception as e:
            logger.error(f"保存OCR结果异常: {e}")
    
    def _process_thought_text(self, text, timestamp):
        """处理思考文本"""
        # 分析文本，提取思考内容
        thought_type, thought_content = self._analyze_thought_text(text)
        
        # 如果有有效的思考内容，记录它
        if thought_content:
            if self.thought_action_recorder:
                # 使用ThoughtActionRecorder记录
                self.thought_action_recorder.record_thought(
                    thought_content,
                    thought_type=thought_type
                )
            else:
                # 直接记录到日志
                logger.info(f"[思考] [{thought_type}] {thought_content}")
                
                # 保存到思考日志文件
                self._save_thought_to_file(thought_content, thought_type, timestamp)
    
    def _analyze_thought_text(self, text):
        """分析思考文本，提取类型和内容"""
        # 默认类型
        thought_type = "general"
        
        # 尝试识别思考类型
        type_indicators = {
            "reasoning": ["推理", "分析", "思考", "考虑", "判断"],
            "decision": ["决定", "决策", "选择", "确定"],
            "planning": ["计划", "规划", "步骤", "方法"]
        }
        
        # 检查文本中是否包含类型指示词
        for t_type, indicators in type_indicators.items():
            if any(indicator in text for indicator in indicators):
                thought_type = t_type
                break
        
        # 提取思考内容
        # 这里可以实现更复杂的内容提取逻辑
        thought_content = text
        
        return thought_type, thought_content
    
    def _save_thought_to_file(self, content, thought_type, timestamp):
        """保存思考到文件"""
        # 创建思考日志文件名
        date_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d')
        thought_file = os.path.join(self.log_dir, f"thoughts_{date_str}.json")
        
        # 格式化时间戳
        time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # 创建思考记录
        thought_record = {
            "timestamp": timestamp,
            "time": time_str,
            "type": thought_type,
            "content": content,
            "source": "ocr"
        }
        
        # 写入日志
        try:
            # 读取现有记录
            thoughts = []
            if os.path.exists(thought_file):
                with open(thought_file, 'r', encoding='utf-8') as f:
                    try:
                        thoughts = json.load(f)
                    except:
                        thoughts = []
            
            # 添加新记录
            thoughts.append(thought_record)
            
            # 写入文件
            with open(thought_file, 'w', encoding='utf-8') as f:
                json.dump(thoughts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存思考记录异常: {e}")
    
    def _process_action_text(self, text, timestamp):
        """处理操作文本"""
        # 分析文本，提取操作信息
        action_info = self._analyze_action_text(text)
        
        # 如果有有效的操作信息，记录它
        if action_info:
            action_name = action_info.get("name", "unknown_action")
            action_params = action_info.get("params", {})
            action_result = action_info.get("result", {})
            
            if self.thought_action_recorder:
                # 使用ThoughtActionRecorder记录
                self.thought_action_recorder.record_action(
                    action_name,
                    action_params,
                    action_result
                )
            else:
                # 直接记录到日志
                logger.info(f"[操作] {action_name} - 参数: {action_params} - 结果: {action_result}")
                
                # 保存到操作日志文件
                self._save_action_to_file(action_name, action_params, action_result, timestamp)
    
    def _analyze_action_text(self, text):
        """分析操作文本，提取操作信息"""
        # 这里需要实现操作文本解析逻辑
        # 根据Manus界面的具体格式实现
        
        # 简单示例：尝试匹配"操作: xxx, 参数: xxx, 结果: xxx"格式
        action_info = {}
        
        # 尝试提取操作名称
        action_match = None
        for pattern in ["操作:", "执行:", "调用:"]:
            if pattern in text:
                parts = text.split(pattern, 1)
                if len(parts) > 1:
                    action_text = parts[1].strip()
                    action_match = action_text
                    break
        
        if not action_match:
            return None
        
        # 尝试提取操作名称、参数和结果
        action_name = "unknown_action"
        action_params = {}
        action_result = {}
        
        # 提取操作名称
        name_parts = action_match.split(",", 1)
        if len(name_parts) > 0:
            action_name = name_parts[0].strip()
        
        # 提取参数
        if "参数:" in text:
            param_parts = text.split("参数:", 1)
            if len(param_parts) > 1:
                param_text = param_parts[1].split("结果:", 1)[0].strip()
                # 简单解析参数
                try:
                    # 尝试解析为JSON
                    action_params = json.loads(param_text)
                except:
                    # 解析失败，使用文本
                    action_params = {"text": param_text}
        
        # 提取结果
        if "结果:" in text:
            result_parts = text.split("结果:", 1)
            if len(result_parts) > 1:
                result_text = result_parts[1].strip()
                # 简单解析结果
                try:
                    # 尝试解析为JSON
                    action_result = json.loads(result_text)
                except:
                    # 解析失败，使用文本
                    action_result = {"text": result_text}
        
        # 构建操作信息
        action_info = {
            "name": action_name,
            "params": action_params,
            "result": action_result
        }
        
        return action_info
    
    def _save_action_to_file(self, action_name, action_params, action_result, timestamp):
        """保存操作到文件"""
        # 创建操作日志文件名
        date_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y%m%d')
        action_file = os.path.join(self.log_dir, f"actions_{date_str}.json")
        
        # 格式化时间戳
        time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # 创建操作记录
        action_record = {
            "timestamp": timestamp,
            "time": time_str,
            "name": action_name,
            "params": action_params,
            "result": action_result,
            "source": "ocr"
        }
        
        # 写入日志
        try:
            # 读取现有记录
            actions = []
            if os.path.exists(action_file):
                with open(action_file, 'r', encoding='utf-8') as f:
                    try:
                        actions = json.load(f)
                    except:
                        actions = []
            
            # 添加新记录
            actions.append(action_record)
            
            # 写入文件
            with open(action_file, 'w', encoding='utf-8') as f:
                json.dump(actions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存操作记录异常: {e}")
    
    def set_monitor_regions(self, regions):
        """设置监控区域"""
        self.monitor_regions = regions
        logger.info(f"已更新监控区域: {len(regions)}个区域")
    
    def add_monitor_region(self, name, bbox, region_type="thought"):
        """添加监控区域"""
        self.monitor_regions.append({
            "name": name,
            "bbox": bbox,
            "type": region_type
        })
        logger.info(f"已添加监控区域: {name}, 类型: {region_type}")
    
    def remove_monitor_region(self, name):
        """移除监控区域"""
        self.monitor_regions = [r for r in self.monitor_regions if r["name"] != name]
        logger.info(f"已移除监控区域: {name}")
    
    def get_monitor_regions(self):
        """获取监控区域"""
        return self.monitor_regions
    
    def set_capture_interval(self, interval):
        """设置捕获间隔"""
        self.capture_interval = interval
        logger.info(f"已更新捕获间隔: {interval}秒")
    
    def get_latest_thoughts(self, limit=10, include_actions=False):
        """获取最近的思考记录"""
        # 如果有ThoughtActionRecorder，使用它的方法
        if self.thought_action_recorder:
            return self.thought_action_recorder.get_latest_thoughts(
                limit=limit,
                include_actions=include_actions
            )
        
        # 否则，从本地文件读取
        thoughts = []
        actions = []
        
        # 获取日志文件列表
        log_files = os.listdir(self.log_dir)
        
        # 读取思考记录
        thought_files = [f for f in log_files if f.startswith("thoughts_") and f.endswith(".json")]
        for file in sorted(thought_files, reverse=True):
            file_path = os.path.join(self.log_dir, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_thoughts = json.load(f)
                    thoughts.extend(file_thoughts)
            except Exception as e:
                logger.error(f"读取思考记录异常: {e}")
        
        # 如果包含操作记录，读取操作记录
        if include_actions:
            action_files = [f for f in log_files if f.startswith("actions_") and f.endswith(".json")]
            for file in sorted(action_files, reverse=True):
                file_path = os.path.join(self.log_dir, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_actions = json.load(f)
                        actions.extend(file_actions)
                except Exception as e:
                    logger.error(f"读取操作记录异常: {e}")
        
        # 合并记录
        all_records = thoughts + actions if include_actions else thoughts
        
        # 按时间戳排序
        all_records.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # 返回指定数量的记录
        return all_records[:limit]
    
    def capture_now(self, region_name=None):
        """立即捕获指定区域"""
        if not self.screen_grabber or not self.ocr_engine:
            logger.error("屏幕捕获或OCR引擎未初始化")
            return None
        
        # 确定要捕获的区域
        regions_to_capture = []
        if region_name:
            # 捕获指定区域
            for region in self.monitor_regions:
                if region["name"] == region_name:
                    regions_to_capture.append(region)
                    break
            if not regions_to_capture:
                logger.error(f"未找到区域: {region_name}")
                return None
        else:
            # 捕获所有区域
            regions_to_capture = self.monitor_regions
        
        results = {}
        
        # 捕获区域
        for region in regions_to_capture:
            region_name = region["name"]
            region_bbox = region["bbox"]
            region_type = region["type"]
            
            # 捕获屏幕区域
            screenshot = self.screen_grabber.grab(bbox=region_bbox)
            
            # OCR识别文本
            text = self._perform_ocr(screenshot)
            
            # 清理文本
            cleaned_text = self._clean_text(text)
            
            # 处理识别到的文本
            timestamp = time.time()
            self._process_recognized_text(cleaned_text, region_type, region_name, timestamp)
            
            # 添加到结果
            results[region_name] = cleaned_text
        
        return results
    
    def take_screenshot(self, region_name=None, save_path=None):
        """截取屏幕并保存"""
        if not self.screen_grabber:
            logger.error("屏幕捕获工具未初始化")
            return None
        
        # 确定要截取的区域
        region_to_capture = None
        if region_name:
            # 截取指定区域
            for region in self.monitor_regions:
                if region["name"] == region_name:
                    region_to_capture = region
                    break
            if not region_to_capture:
                logger.error(f"未找到区域: {region_name}")
                return None
        
        # 截取屏幕
        if region_to_capture:
            screenshot = self.screen_grabber.grab(bbox=region_to_capture["bbox"])
        else:
            screenshot = self.screen_grabber.grab()
        
        # 如果指定了保存路径，保存截图
        if save_path:
            try:
                screenshot.save(save_path)
                logger.info(f"截图已保存到: {save_path}")
            except Exception as e:
                logger.error(f"保存截图异常: {e}")
                return screenshot
        
        return screenshot
