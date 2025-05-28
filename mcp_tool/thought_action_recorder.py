"""
思考与操作记录器模块 - ThoughtActionRecorder

该模块用于记录Manus的思考过程和执行的操作，提供结构化的日志存储和查询功能。
主要功能：
1. 实时捕获Manus的思考过程
2. 记录所有API调用和操作
3. 记录操作结果和状态变化
4. 提供结构化的日志存储和查询
5. 支持日志压缩和归档

作者: Manus AI
日期: 2025-05-28
"""

import os
import json
import time
import datetime
import shutil
import logging
from typing import Dict, List, Any, Optional, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ThoughtActionRecorder")

class ThoughtActionRecorder:
    """
    思考与操作记录器类，用于记录Manus的思考过程和执行的操作
    """
    
    def __init__(self, log_dir: str = None):
        """
        初始化思考与操作记录器
        
        Args:
            log_dir: 日志存储目录，默认为当前工作目录下的logs目录
        """
        self.log_dir = log_dir or os.path.join(os.getcwd(), "logs")
        self.current_session = None
        self.thought_log = None
        self.action_log = None
        self.setup_logging()
        logger.info(f"ThoughtActionRecorder initialized with log directory: {self.log_dir}")
    
    def setup_logging(self) -> None:
        """
        设置日志记录环境，创建必要的目录和文件
        """
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 创建新的会话ID，格式为session_时间戳
        self.current_session = f"session_{int(time.time())}"
        session_dir = os.path.join(self.log_dir, self.current_session)
        os.makedirs(session_dir, exist_ok=True)
        
        # 设置思考日志文件路径
        self.thought_log = os.path.join(session_dir, "thoughts.jsonl")
        
        # 设置操作日志文件路径
        self.action_log = os.path.join(session_dir, "actions.jsonl")
        
        logger.info(f"Logging session {self.current_session} initialized")
        logger.info(f"Thought log: {self.thought_log}")
        logger.info(f"Action log: {self.action_log}")
    
    def record_thought(self, thought: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        记录Manus的思考过程
        
        Args:
            thought: 思考内容
            context: 思考上下文，可选
            
        Returns:
            记录的思考条目
        """
        if not thought:
            logger.warning("Attempted to record empty thought, skipping")
            return {}
            
        entry = {
            "timestamp": time.time(),
            "datetime": datetime.datetime.now().isoformat(),
            "type": "thought",
            "content": thought,
            "context": context or {}
        }
        
        self._append_to_log(self.thought_log, entry)
        logger.debug(f"Recorded thought: {thought[:50]}...")
        
        return entry
    
    def record_action(self, action_type: str, action_params: Dict[str, Any], 
                     result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        记录Manus的操作
        
        Args:
            action_type: 操作类型
            action_params: 操作参数
            result: 操作结果，可选
            
        Returns:
            记录的操作条目
        """
        if not action_type:
            logger.warning("Attempted to record action with empty type, skipping")
            return {}
            
        entry = {
            "timestamp": time.time(),
            "datetime": datetime.datetime.now().isoformat(),
            "type": "action",
            "action_type": action_type,
            "action_params": action_params,
            "result": result
        }
        
        self._append_to_log(self.action_log, entry)
        logger.debug(f"Recorded action: {action_type}")
        
        return entry
    
    def _append_to_log(self, log_file: str, entry: Dict[str, Any]) -> None:
        """
        将条目追加到日志文件
        
        Args:
            log_file: 日志文件路径
            entry: 要追加的条目
        """
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Error appending to log file {log_file}: {e}")
            # 尝试创建目录
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            # 重试一次
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception as e2:
                logger.error(f"Second attempt failed: {e2}")
    
    def get_session_logs(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定会话的所有日志
        
        Args:
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            包含会话ID、思考日志和操作日志的字典
        """
        session_id = session_id or self.current_session
        session_dir = os.path.join(self.log_dir, session_id)
        
        thoughts = []
        actions = []
        
        # 读取思考日志
        thought_log = os.path.join(session_dir, "thoughts.jsonl")
        if os.path.exists(thought_log):
            try:
                with open(thought_log, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            thoughts.append(json.loads(line))
            except Exception as e:
                logger.error(f"Error reading thought log {thought_log}: {e}")
        
        # 读取操作日志
        action_log = os.path.join(session_dir, "actions.jsonl")
        if os.path.exists(action_log):
            try:
                with open(action_log, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            actions.append(json.loads(line))
            except Exception as e:
                logger.error(f"Error reading action log {action_log}: {e}")
        
        logger.info(f"Retrieved logs for session {session_id}: {len(thoughts)} thoughts, {len(actions)} actions")
        
        return {
            "session_id": session_id,
            "thoughts": thoughts,
            "actions": actions
        }
    
    def get_all_sessions(self) -> List[str]:
        """
        获取所有会话ID
        
        Returns:
            所有会话ID的列表
        """
        try:
            # 获取logs目录下的所有子目录
            sessions = [d for d in os.listdir(self.log_dir) 
                      if os.path.isdir(os.path.join(self.log_dir, d)) and d.startswith("session_")]
            sessions.sort(reverse=True)  # 按时间戳降序排序
            return sessions
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            return []
    
    def get_latest_thoughts(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取最新的思考记录
        
        Args:
            count: 要获取的记录数量
            
        Returns:
            最新的思考记录列表
        """
        logs = self.get_session_logs()
        thoughts = logs.get("thoughts", [])
        # 按时间戳降序排序
        thoughts.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return thoughts[:count]
    
    def get_latest_actions(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取最新的操作记录
        
        Args:
            count: 要获取的记录数量
            
        Returns:
            最新的操作记录列表
        """
        logs = self.get_session_logs()
        actions = logs.get("actions", [])
        # 按时间戳降序排序
        actions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return actions[:count]
    
    def search_logs(self, keyword: str, session_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        搜索日志
        
        Args:
            keyword: 搜索关键词
            session_id: 会话ID，如果为None则使用当前会话
            
        Returns:
            包含匹配的思考和操作记录的字典
        """
        logs = self.get_session_logs(session_id)
        
        matched_thoughts = []
        matched_actions = []
        
        # 搜索思考记录
        for thought in logs.get("thoughts", []):
            content = thought.get("content", "").lower()
            if keyword.lower() in content:
                matched_thoughts.append(thought)
        
        # 搜索操作记录
        for action in logs.get("actions", []):
            # 搜索操作类型
            action_type = action.get("action_type", "").lower()
            if keyword.lower() in action_type:
                matched_actions.append(action)
                continue
                
            # 搜索操作参数
            params_str = json.dumps(action.get("action_params", {}), ensure_ascii=False).lower()
            if keyword.lower() in params_str:
                matched_actions.append(action)
                continue
                
            # 搜索操作结果
            result_str = json.dumps(action.get("result", {}), ensure_ascii=False).lower()
            if keyword.lower() in result_str:
                matched_actions.append(action)
        
        logger.info(f"Search for '{keyword}' found {len(matched_thoughts)} thoughts and {len(matched_actions)} actions")
        
        return {
            "thoughts": matched_thoughts,
            "actions": matched_actions
        }
    
    def archive_logs(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """
        归档旧日志
        
        Args:
            days_to_keep: 保留的天数
            
        Returns:
            归档结果
        """
        now = time.time()
        cutoff_time = now - (days_to_keep * 24 * 60 * 60)
        
        archived_sessions = []
        failed_sessions = []
        
        # 创建归档目录
        archive_dir = os.path.join(self.log_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)
        
        # 获取所有会话
        sessions = self.get_all_sessions()
        
        for session in sessions:
            try:
                # 从会话ID中提取时间戳
                if session.startswith("session_"):
                    timestamp = int(session.split("_")[1])
                    
                    # 如果会话早于截止时间，则归档
                    if timestamp < cutoff_time:
                        session_dir = os.path.join(self.log_dir, session)
                        archive_session_dir = os.path.join(archive_dir, session)
                        
                        # 移动会话目录到归档目录
                        shutil.move(session_dir, archive_session_dir)
                        archived_sessions.append(session)
                        logger.info(f"Archived session {session}")
            except Exception as e:
                logger.error(f"Error archiving session {session}: {e}")
                failed_sessions.append({"session": session, "error": str(e)})
        
        result = {
            "archived_sessions": archived_sessions,
            "failed_sessions": failed_sessions,
            "archive_dir": archive_dir
        }
        
        logger.info(f"Archived {len(archived_sessions)} sessions, {len(failed_sessions)} failed")
        
        return result
    
    def export_session(self, session_id: Optional[str] = None, 
                      format: str = "json") -> Dict[str, Any]:
        """
        导出会话日志
        
        Args:
            session_id: 会话ID，如果为None则使用当前会话
            format: 导出格式，支持json和csv
            
        Returns:
            导出结果
        """
        session_id = session_id or self.current_session
        logs = self.get_session_logs(session_id)
        
        export_dir = os.path.join(self.log_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "json":
            export_file = os.path.join(export_dir, f"{session_id}_{timestamp}.json")
            try:
                with open(export_file, "w", encoding="utf-8") as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
                logger.info(f"Exported session {session_id} to {export_file}")
                return {"success": True, "file": export_file}
            except Exception as e:
                logger.error(f"Error exporting session {session_id} to JSON: {e}")
                return {"success": False, "error": str(e)}
        
        elif format.lower() == "csv":
            # 导出思考日志
            thoughts_file = os.path.join(export_dir, f"{session_id}_thoughts_{timestamp}.csv")
            actions_file = os.path.join(export_dir, f"{session_id}_actions_{timestamp}.csv")
            
            try:
                # 导出思考日志
                with open(thoughts_file, "w", encoding="utf-8") as f:
                    f.write("timestamp,datetime,content,context\n")
                    for thought in logs.get("thoughts", []):
                        timestamp = thought.get("timestamp", "")
                        datetime_str = thought.get("datetime", "")
                        content = thought.get("content", "").replace(",", ";").replace("\n", " ")
                        context = json.dumps(thought.get("context", {}), ensure_ascii=False).replace(",", ";").replace("\n", " ")
                        f.write(f"{timestamp},{datetime_str},{content},{context}\n")
                
                # 导出操作日志
                with open(actions_file, "w", encoding="utf-8") as f:
                    f.write("timestamp,datetime,action_type,action_params,result\n")
                    for action in logs.get("actions", []):
                        timestamp = action.get("timestamp", "")
                        datetime_str = action.get("datetime", "")
                        action_type = action.get("action_type", "").replace(",", ";")
                        action_params = json.dumps(action.get("action_params", {}), ensure_ascii=False).replace(",", ";").replace("\n", " ")
                        result = json.dumps(action.get("result", {}), ensure_ascii=False).replace(",", ";").replace("\n", " ")
                        f.write(f"{timestamp},{datetime_str},{action_type},{action_params},{result}\n")
                
                logger.info(f"Exported session {session_id} to {thoughts_file} and {actions_file}")
                return {"success": True, "thoughts_file": thoughts_file, "actions_file": actions_file}
            except Exception as e:
                logger.error(f"Error exporting session {session_id} to CSV: {e}")
                return {"success": False, "error": str(e)}
        
        else:
            logger.error(f"Unsupported export format: {format}")
            return {"success": False, "error": f"Unsupported export format: {format}"}
    
    def clear_current_session(self) -> Dict[str, Any]:
        """
        清除当前会话的日志
        
        Returns:
            清除结果
        """
        try:
            # 备份当前日志
            backup_dir = os.path.join(self.log_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_session_dir = os.path.join(backup_dir, f"{self.current_session}_{timestamp}")
            
            session_dir = os.path.join(self.log_dir, self.current_session)
            
            if os.path.exists(session_dir):
                shutil.copytree(session_dir, backup_session_dir)
                
                # 清除当前日志文件
                if os.path.exists(self.thought_log):
                    os.remove(self.thought_log)
                
                if os.path.exists(self.action_log):
                    os.remove(self.action_log)
                
                logger.info(f"Cleared current session {self.current_session}, backup at {backup_session_dir}")
                return {"success": True, "backup": backup_session_dir}
            else:
                logger.warning(f"Session directory {session_dir} does not exist")
                return {"success": False, "error": f"Session directory {session_dir} does not exist"}
        except Exception as e:
            logger.error(f"Error clearing current session: {e}")
            return {"success": False, "error": str(e)}
