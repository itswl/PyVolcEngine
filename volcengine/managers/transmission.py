import time
import logging
import os
from volcenginesdkcore import Configuration
from volcenginesdkcore.rest import ApiException
import volcenginesdkredis
from configs.api_config import api_config
from redis_manager import RedisManager

# 确保logs目录存在
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(log_dir, 'redis_transmission.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class RedisTransmissionManager:
    """Redis实例间数据传输管理器
    
    用于创建和管理Redis实例之间的数据传输任务
    支持全量数据同步和增量数据同步
    """
    
    def __init__(self):
        self._init_client()
        self.api = volcenginesdkredis
        self.client_api = self.api.REDISApi()
        self.redis_manager = RedisManager()
        
    def _init_client(self):
        """初始化API客户端配置"""
        configuration = Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        Configuration.set_default(configuration)
    
    def create_transmission_task(self, task_config):
        """创建Redis实例间数据传输任务
        
        Args:
            task_config (dict): 传输任务配置
            
        Returns:
            str: 传输任务ID，如果创建失败则返回None
        """
        try:
            # 检查源实例和目标实例是否存在
            source_instance_id = task_config['source_instance_id']
            target_instance_id = task_config['target_instance_id']
            
            # 验证源实例
            source_status = self._check_instance_status(source_instance_id)
            if not source_status or source_status != "Running":
                logger.error(f"源Redis实例 {source_instance_id} 状态异常或不存在")
                return None
                
            # 验证目标实例
            target_status = self._check_instance_status(target_instance_id)
            if not target_status or target_status != "Running":
                logger.error(f"目标Redis实例 {target_instance_id} 状态异常或不存在")
                return None
            
            # 创建数据传输任务请求
            request = self.api.CreateTransmissionTaskRequest(
                source_instance_id=source_instance_id,
                target_instance_id=target_instance_id,
                task_name=task_config['task_name'],
                description=task_config.get('description', ''),
                transmission_type=task_config['transmission_type'],  # FullSync(全量同步) 或 IncrementalSync(增量同步)
                database_whitelist=task_config.get('database_whitelist', []),  # 要同步的数据库列表，为空表示全部同步
                database_blacklist=task_config.get('database_blacklist', []),  # 不同步的数据库列表
                key_pattern_whitelist=task_config.get('key_pattern_whitelist', []),  # 要同步的key模式列表
                key_pattern_blacklist=task_config.get('key_pattern_blacklist', []),  # 不同步的key模式列表
                schedule_config=self._create_schedule_config(task_config.get('schedule_config')),  # 调度配置
                conflict_policy=task_config.get('conflict_policy', 'OverwriteTarget')  # 冲突策略: OverwriteTarget(覆盖目标) 或 SkipConflict(跳过冲突)
            )
            
            # 发送请求创建传输任务
            response = self.client_api.create_transmission_task(request)
            logger.info(f"Redis数据传输任务创建成功: {response.task_id}")
            
            # 记录任务详情
            self._log_task_details(task_config, response.task_id)
            
            return response.task_id
            
        except ApiException as e:
            logger.error(f"创建Redis数据传输任务时发生异常: {e}")
            return None
    
    def _create_schedule_config(self, schedule_config):
        """创建调度配置
        
        Args:
            schedule_config (dict): 调度配置信息
            
        Returns:
            ScheduleConfigForCreateTransmissionTaskInput: 调度配置对象
        """
        if not schedule_config:
            return None
            
        return self.api.ScheduleConfigForCreateTransmissionTaskInput(
            start_time=schedule_config.get('start_time'),  # 开始时间，格式: "2023-01-01T00:00:00Z"
            end_time=schedule_config.get('end_time'),  # 结束时间，格式: "2023-01-02T00:00:00Z"
            recurrence=schedule_config.get('recurrence', 'Once'),  # 重复类型: Once(一次性), Daily(每天), Weekly(每周), Monthly(每月)
            recurrence_interval=schedule_config.get('recurrence_interval', 1),  # 重复间隔
            days_of_week=schedule_config.get('days_of_week', []),  # 每周的哪几天，例如: ["Monday", "Wednesday", "Friday"]
            days_of_month=schedule_config.get('days_of_month', [])  # 每月的哪几天，例如: [1, 15, 30]
        )
    
    def _check_instance_status(self, instance_id):
        """检查Redis实例状态
        
        Args:
            instance_id (str): Redis实例ID
            
        Returns:
            str: 实例状态，如果查询失败则返回None
        """
        try:
            status_request = self.api.DescribeDBInstancesRequest()
            status_response = self.client_api.describe_db_instances(status_request)
            
            for instance in status_response.instances:
                if instance.instance_id == instance_id:
                    return instance.status
            
            logger.error(f"未找到Redis实例: {instance_id}")
            return None
            
        except ApiException as e:
            logger.error(f"查询Redis实例状态时发生异常: {e}")
            return None
    
    def get_transmission_task(self, task_id):
        """获取传输任务详情
        
        Args:
            task_id (str): 传输任务ID
            
        Returns:
            dict: 传输任务详情，如果查询失败则返回None
        """
        try:
            request = self.api.DescribeTransmissionTaskRequest(
                task_id=task_id
            )
            
            response = self.client_api.describe_transmission_task(request)
            
            # 将响应转换为字典格式
            task_info = {
                'task_id': response.task_id,
                'task_name': response.task_name,
                'description': response.description,
                'source_instance_id': response.source_instance_id,
                'target_instance_id': response.target_instance_id,
                'transmission_type': response.transmission_type,
                'status': response.status,
                'create_time': response.create_time,
                'update_time': response.update_time,
                'progress': response.progress
            }
            
            return task_info
            
        except ApiException as e:
            logger.error(f"获取传输任务详情时发生异常: {e}")
            return None
    
    def list_transmission_tasks(self, page_number=1, page_size=20):
        """列出所有传输任务
        
        Args:
            page_number (int): 页码
            page_size (int): 每页记录数
            
        Returns:
            list: 传输任务列表
        """
        try:
            request = self.api.ListTransmissionTasksRequest(
                page_number=page_number,
                page_size=page_size
            )
            
            response = self.client_api.list_transmission_tasks(request)
            
            tasks = []
            for task in response.tasks:
                task_info = {
                    'task_id': task.task_id,
                    'task_name': task.task_name,
                    'source_instance_id': task.source_instance_id,
                    'target_instance_id': task.target_instance_id,
                    'transmission_type': task.transmission_type,
                    'status': task.status,
                    'create_time': task.create_time,
                    'progress': task.progress
                }
                tasks.append(task_info)
            
            return tasks
            
        except ApiException as e:
            logger.error(f"列出传输任务时发生异常: {e}")
            return []
    
    def start_transmission_task(self, task_id):
        """启动传输任务
        
        Args:
            task_id (str): 传输任务ID
            
        Returns:
            bool: 是否成功启动
        """
        try:
            request = self.api.StartTransmissionTaskRequest(
                task_id=task_id
            )
            
            self.client_api.start_transmission_task(request)
            logger.info(f"成功启动传输任务: {task_id}")
            return True
            
        except ApiException as e:
            logger.error(f"启动传输任务时发生异常: {e}")
            return False
    
    def stop_transmission_task(self, task_id):
        """停止传输任务
        
        Args:
            task_id (str): 传输任务ID
            
        Returns:
            bool: 是否成功停止
        """
        try:
            request = self.api.StopTransmissionTaskRequest(
                task_id=task_id
            )
            
            self.client_api.stop_transmission_task(request)
            logger.info(f"成功停止传输任务: {task_id}")
            return True
            
        except ApiException as e:
            logger.error(f"停止传输任务时发生异常: {e}")
            return False
    
    def delete_transmission_task(self, task_id):
        """删除传输任务
        
        Args:
            task_id (str): 传输任务ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            request = self.api.DeleteTransmissionTaskRequest(
                task_id=task_id
            )
            
            self.client_api.delete_transmission_task(request)
            logger.info(f"成功删除传输任务: {task_id}")
            return True
            
        except ApiException as e:
            logger.error(f"删除传输任务时发生异常: {e}")
            return False
    
    def _log_task_details(self, task_config, task_id):
        """记录任务详情到日志文件
        
        Args:
            task_config (dict): 任务配置
            task_id (str): 任务ID
        """
        # 将任务信息写入Markdown文件
        task_info_path = os.path.join(log_dir, 'redis_transmission_tasks.md')
        with open(task_info_path, 'a', encoding='utf-8') as f:
            # 添加分隔符和时间戳
            f.write(f"\n{'='*50}\n")
            f.write(f"记录时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"# Redis数据传输任务记录\n\n")
            f.write(f"## 任务信息\n")
            f.write(f"- 任务ID: {task_id}\n")
            f.write(f"- 任务名称: {task_config['task_name']}\n")
            f.write(f"- 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- 传输类型: {task_config['transmission_type']}\n")
            f.write(f"- 描述: {task_config.get('description', '无')}\n\n")

            f.write(f"## 实例信息\n")
            f.write(f"- 源实例ID: {task_config['source_instance_id']}\n")
            f.write(f"- 目标实例ID: {task_config['target_instance_id']}\n\n")

            f.write(f"## 同步配置\n")
            f.write(f"- 数据库白名单: {', '.join(task_config.get('database_whitelist', ['全部']))}\n")
            f.write(f"- 数据库黑名单: {', '.join(task_config.get('database_blacklist', ['无']))}\n")
            f.write(f"- Key模式白名单: {', '.join(task_config.get('key_pattern_whitelist', ['全部']))}\n")
            f.write(f"- Key模式黑名单: {', '.join(task_config.get('key_pattern_blacklist', ['无']))}\n\n")

            # 记录调度配置
            if 'schedule_config' in task_config:
                schedule = task_config['schedule_config']
                f.write(f"## 调度配置\n")
                f.write(f"- 开始时间: {schedule.get('start_time', '未指定')}\n")
                f.write(f"- 结束时间: {schedule.get('end_time', '未指定')}\n")
                f.write(f"- 重复类型: {schedule.get('recurrence', 'Once')}\n")
                f.write(f"- 重复间隔: {schedule.get('recurrence_interval', 1)}\n")
                
                if 'days_of_week' in schedule and schedule['days_of_week']:
                    f.write(f"- 每周执行日: {', '.join(schedule['days_of_week'])}\n")
                    
                if 'days_of_month' in schedule and schedule['days_of_month']:
                    f.write(f"- 每月执行日: {', '.join(map(str, schedule['days_of_month']))}\n")
            
            f.write(f"\n## 冲突策略\n")
            f.write(f"- 策略: {task_config.get('conflict_policy', 'OverwriteTarget')}\n")
            f.write(f"  - OverwriteTarget: 覆盖目标数据\n")
            f.write(f"  - SkipConflict: 跳过冲突数据\n")