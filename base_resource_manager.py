import os
import logging
import time
from abc import ABC, abstractmethod
from configs.api_config import api_config

class BaseResourceManager(ABC):
    def __init__(self, resource_name):
        self.resource_name = resource_name
        self._setup_logging()
        self._init_client()

    def _setup_logging(self):
        """设置日志配置"""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        self.logger = logging.getLogger(self.resource_name)
        self.logger.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        file_handler = logging.FileHandler(os.path.join(log_dir, f'{self.resource_name.lower()}.log'))
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)

    @abstractmethod
    def _init_client(self):
        """初始化客户端，子类必须实现"""
        pass

    @abstractmethod
    def list_resources(self):
        """列出资源，子类必须实现"""
        pass

    def write_to_markdown(self, resources, title=None):
        """将资源信息写入Markdown文件"""
        if not title:
            title = self.resource_name
            
        resource_info_path = os.path.join(os.path.dirname(__file__), 'logs', f'{self.resource_name.lower()}_info.md')
        
        with open(resource_info_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}资源信息记录\n\n")
            f.write(f"## 记录时间\n{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if not resources:
                f.write("未发现任何资源\n")
                return
                
            f.write(f"## {title}资源列表\n")
            self._write_resources_to_file(f, resources)
            f.write("---\n\n")
            
        self.logger.info(f"{title}资源信息已写入文件: {resource_info_path}")

    @abstractmethod
    def _write_resources_to_file(self, file, resources):
        """将资源信息写入文件，子类必须实现"""
        pass 