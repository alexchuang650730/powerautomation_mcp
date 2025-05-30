"""
统一配置管理模块 - UnifiedConfig

该模块提供统一的配置管理，支持视觉校准工具和CLI功能的配置需求。
采用单例模式确保全局配置一致性，并提供简单的API用于获取和设置配置。

作者: Manus AI
日期: 2025-05-30
"""

import os
import json
import logging
import platform
from typing import Dict, Any, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UnifiedConfig")

# 单例配置管理器
_config_instance = None

class UnifiedConfig:
    """统一配置管理类，采用单例模式"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，可选
        """
        # 默认配置文件路径
        self.config_dir = os.path.expanduser("~/.powerautomation_mcp")
        self.config_path = config_path or os.path.join(self.config_dir, "config.json")
        
        # 创建配置目录
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
        logger.info(f"统一配置管理器初始化完成，配置文件: {self.config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        # 默认配置
        default_config = {
            "// 基础配置": "通用配置项",
            "platform": platform.system().lower(),
            "log_dir": os.path.expanduser("~/mcp_logs"),
            
            "// 仓库配置": "用于CLI工具的代码管理",
            "local_repo_path": os.path.expanduser("~/powerassistant/powerautomation"),
            "repo_url": "https://github.com/username/powerautomation.git",
            "mcp_repo_url": "https://github.com/username/powerautomation_mcp.git",
            "ssh_key_path": os.path.expanduser("~/.ssh/id_rsa"),
            "github_token": None,
            "github_repo": "username/powerautomation",
            
            "// 工作流配置": "用于CLI工具的工作流程控制",
            "test_script": "start_and_test.sh",
            "readme_path": "README.md",
            "auto_upload": True,
            "auto_test": True,
            "auto_solve": True,
            "check_interval": 3600.0,
            
            "// 监控配置": "用于视觉校准和自动监控",
            "screenshot_dir": os.path.expanduser("~/powerassistant/powerautomation/screenshots"),
            "manus_url": "https://manus.im/",
            "ocr_engine": "tesseract",
            "capture_interval": 2.0,
            
            "// 监控区域配置": "用于自动监控的区域定义",
            "monitor_regions": {
                "work_list": {"x": 100, "y": 100, "width": 400, "height": 300},
                "action_list": {"x": 100, "y": 400, "width": 400, "height": 300}
            },
            
            "// 视觉校准配置": "用于视觉校准工具",
            "browser_window_title_pattern": ".*manus\\.im.*",
            "calibration_grid_size": 10,
            "detection_confidence_threshold": 0.7,
            "simple_mode": False,
            "manual_regions": False,
            "work_list_pattern": "work[-_\\s]*list|task[-_\\s]*list",
            "action_list_pattern": "action[-_\\s]*list|operation[-_\\s]*list",
            "work_list_css_selector": ".work-list-container",
            "action_list_css_selector": ".action-list-container",
            "default_work_list_region": [0.05, 0.2, 0.45, 0.8],
            "default_action_list_region": [0.55, 0.2, 0.95, 0.8],
            
            "// 版本管理配置": "用于ManusProblemSolver的版本回滚功能",
            "save_points_dir": os.path.expanduser("~/.powerautomation_mcp/save_points"),
            "solutions_dir": os.path.expanduser("~/powerassistant/powerautomation/manus_solutions"),
            "auto_create_save_point": True,
            "max_save_points": 10,
            "save_point_naming_pattern": "save_point_%Y%m%d_%H%M%S"
        }
        
        # 如果配置文件存在，加载它
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                logger.info(f"已加载配置文件: {self.config_path}")
                
                # 合并默认配置和用户配置
                config = {**default_config, **user_config}
                return config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        else:
            logger.info(f"配置文件不存在，使用默认配置: {self.config_path}")
        
        # 保存默认配置
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存默认配置: {self.config_path}")
        except Exception as e:
            logger.error(f"保存默认配置失败: {e}")
        
        return default_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置项键名
            default: 默认值，如果配置项不存在则返回此值
        
        Returns:
            Any: 配置项值
        """
        return self.config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            Dict[str, Any]: 所有配置项
        """
        return self.config.copy()
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key: 配置项键名
            value: 配置项值
        """
        self.config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        批量更新配置
        
        Args:
            config_dict: 配置字典
        """
        self.config.update(config_dict)
    
    def save(self) -> bool:
        """
        保存配置
        
        Returns:
            bool: 是否成功保存
        """
        try:
            # 添加最后更新时间
            self.config["last_updated"] = datetime.now().isoformat()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存配置: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def reset(self) -> bool:
        """
        重置配置为默认值
        
        Returns:
            bool: 是否成功重置
        """
        try:
            # 重新加载默认配置
            self.config = self._load_config()
            return True
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            return False


def get_config(config_path: Optional[str] = None) -> UnifiedConfig:
    """
    获取配置管理器实例
    
    Args:
        config_path: 配置文件路径，可选
    
    Returns:
        UnifiedConfig: 配置管理器实例
    """
    global _config_instance
    
    # 如果实例不存在或指定了新的配置路径，创建新实例
    if _config_instance is None or (config_path is not None and config_path != _config_instance.config_path):
        _config_instance = UnifiedConfig(config_path)
    
    return _config_instance


def merge_configs(cli_config_path: str, visual_config_path: str, output_path: str) -> bool:
    """
    合并CLI配置和视觉校准配置
    
    Args:
        cli_config_path: CLI配置文件路径
        visual_config_path: 视觉校准配置文件路径
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功合并
    """
    try:
        # 加载CLI配置
        with open(cli_config_path, 'r', encoding='utf-8') as f:
            cli_config = json.load(f)
        
        # 加载视觉校准配置
        with open(visual_config_path, 'r', encoding='utf-8') as f:
            visual_config = json.load(f)
        
        # 合并配置
        merged_config = {**cli_config, **visual_config}
        
        # 保存合并后的配置
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已合并配置: {output_path}")
        return True
    except Exception as e:
        logger.error(f"合并配置失败: {e}")
        return False


if __name__ == "__main__":
    # 测试配置管理器
    config = get_config()
    print("配置文件路径:", config.config_path)
    print("平台:", config.get("platform"))
    print("日志目录:", config.get("log_dir"))
    
    # 修改配置
    config.set("test_key", "test_value")
    config.save()
    
    # 重新加载配置
    config = get_config()
    print("测试键:", config.get("test_key"))
