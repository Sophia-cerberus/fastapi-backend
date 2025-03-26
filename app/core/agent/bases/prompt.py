from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import json

@dataclass
class Message:
    """单条消息数据结构"""
    role: str  # system/user/assistant
    content: str
    name: Optional[str] = None  # 可选的消息发送者名称
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return asdict(self)

class Prompt:
    """
    Prompt 基础类,提供构建和管理对话prompt的核心功能
    
    特性：
    - 支持多轮对话管理
    - 支持系统指令设置
    - 支持角色扮演设置
    - 支持prompt模板化
    """
    
    def __init__(self):
        self.messages: List[Message] = []
        self._templates: Dict[str, str] = {}
        
        # 默认系统指令
        self.system_instruction = "你是一个有帮助的AI助手。"
    
    def add_message(self, role: str, content: str, name: Optional[str] = None) -> None:
        """添加一条消息到对话历史"""
        self.messages.append(Message(role=role, content=content, name=name))
    
    def add_user_message(self, content: str, name: Optional[str] = None) -> None:
        """添加用户消息"""
        self.add_message(role="user", content=content, name=name)
    
    def add_assistant_message(self, content: str, name: Optional[str] = None) -> None:
        """添加助手消息"""
        self.add_message(role="assistant", content=content, name=name)
    
    def set_system_instruction(self, instruction: str) -> None:
        """设置系统指令"""
        self.system_instruction = instruction
    
    def register_template(self, name: str, template: str) -> None:
        """注册一个prompt模板"""
        self._templates[name] = template
    
    def apply_template(self, template_name: str, **kwargs) -> str:
        """
        应用已注册的模板
        
        参数:
            template_name: 模板名称
            **kwargs: 模板变量
            
        返回:
            渲染后的prompt字符串
        """
        if template_name not in self._templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        return self._templates[template_name].format(**kwargs)
    
    def clear_conversation(self) -> None:
        """清空对话历史（保留系统指令）"""
        self.messages = []
    
    def build_prompt(
        self,
        include_system=True,
        max_tokens=None,
        reverse=False,
        include_names=True,
        json_format=False,
        **kwargs,
    ) -> Union[List[Dict], str]:
        
                
        prompt_messages = []
        
        # 添加系统指令（如果启用）
        if include_system and hasattr(self,"system_instruction") and getattr (self,"system_instruction"):
            prompt_messages.append({
                "role": "system",
                "content":self.system_instruction})
        
        #添加对话历史记录 
        for msg in reversed (self.messages )if reverse else (self.messages):
            message_dict={"role": msg.role, "content": msg.content}
            if include_names and msg.name :
                message_dict["name"]=msg.name 
            prompt_messages.append(message_dict )
        
        if json_format :
            return json.dumps(prompt_messages, ensure_ascii=False)
        return prompt_messages 