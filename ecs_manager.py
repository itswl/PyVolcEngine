import time
import os
import logging
from functools import wraps
from volcenginesdkcore.rest import ApiException
import volcenginesdkecs
import volcenginesdkcore
import volcenginesdkvpc
from configs.api_config import api_config
from configs.ecs_config import ecs_configs
from eip_manager import EIPManager
from instance_status_checker import InstanceStatusChecker

# 确保logs目录存在
BASE_DIR = os.path.dirname(__file__)
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# 避免重复添加处理器
if not logger.handlers:
    file_handler = logging.FileHandler(os.path.join(log_dir, 'ecs_manager.log'))
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# 资源信息文件路径
RESOURCE_INFO_FILE = os.path.join(log_dir, 'ecs_resource_info.md')

# 装饰器：异常处理
def handle_api_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            logger.error(f"{func.__name__}执行过程中发生API异常: {e}")
            return None
        except Exception as e:
            logger.error(f"{func.__name__}执行过程中发生未知异常: {e}")
            return None
    return wrapper

class ECSManager:
    def __init__(self):
        self._init_client()
        self.ecs_api = volcenginesdkecs.ECSApi()
        self.vpc_api = volcenginesdkvpc.VPCApi()
        self.eip_manager = EIPManager()

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)

    @handle_api_exception
    def get_existing_instance_by_name(self, instance_name):
        """根据实例名称查找现有ECS实例"""
        list_request = volcenginesdkecs.DescribeInstancesRequest()
        list_response = self.ecs_api.describe_instances(list_request)
        
        if hasattr(list_response, 'Result') and hasattr(list_response.Result, 'Instances'):
            for instance in list_response.Result.Instances:
                if instance.InstanceName == instance_name:
                    logger.info(f"找到已存在的ECS实例: {instance.InstanceId}")
                    return instance.InstanceId, instance.InstanceName
        return None, None

    @handle_api_exception
    def get_instance_by_id(self, instance_id):
        """根据实例ID查找ECS实例"""
        list_request = volcenginesdkecs.DescribeInstancesRequest()
        list_response = self.ecs_api.describe_instances(list_request)
        
        if hasattr(list_response, 'Result') and hasattr(list_response.Result, 'Instances'):
            for instance in list_response.Result.Instances:
                if instance.InstanceId == instance_id:
                    logger.info(f"找到指定的ECS实例ID: {instance_id}")
                    return instance.InstanceId, instance.InstanceName
        logger.error(f"未找到指定的ECS实例ID: {instance_id}")
        return None, None

    @handle_api_exception
    def wait_for_instance_status(self, instance_id, target_status="RUNNING", timeout=600, interval=10):
        """等待ECS实例变为指定状态
        
        Args:
            instance_id: 实例ID
            target_status: 目标状态，默认为"RUNNING"
            timeout: 超时时间（秒）
            interval: 检查间隔（秒）
        """
        def status_check_func(api_client, instance_id):
            list_request = volcenginesdkecs.DescribeInstancesRequest()
            list_response = api_client.describe_instances(list_request)
            
            if hasattr(list_response, 'Result') and hasattr(list_response.Result, 'Instances'):
                for instance in list_response.Result.Instances:
                    if instance.InstanceId == instance_id:
                        return instance.Status
            return None
        
        # 使用通用的实例状态检查器
        return InstanceStatusChecker.wait_for_instance_status(
            self.ecs_api, 
            instance_id, 
            target_status=target_status, 
            timeout=timeout, 
            interval=interval,
            status_check_func=status_check_func
        )

    @handle_api_exception
    def create_instance(self, ecs_config):
        """创建ECS实例
        
        Args:
            ecs_config: 可以是ecs_config.py中定义的ECS配置名称(字符串)，
                       也可以是直接传入的完整ECS配置(字典)
        
        Returns:
            tuple: (instance_id, instance_name, eip_address)
        """
        try:
            if isinstance(ecs_config, str):
                config_name = ecs_config
                
                if config_name not in ecs_configs:
                    logger.error(f"未找到名为 {config_name} 的ECS配置")
                    return None, None, None
                    
                actual_config = ecs_configs[config_name]
            elif isinstance(ecs_config, dict):
                actual_config = ecs_config
            else:
                logger.error(f"不支持的ECS配置类型: {type(ecs_config)}")
                return None, None, None
            
            # 检查现有实例
            instance_id, instance_name = self.get_existing_instance_by_name(actual_config['name'])
            if instance_id:
                logger.info(f"已存在同名ECS实例: {instance_id}")
                return instance_id, instance_name, None
            
            # 创建新的ECS实例
            # 将period_unit从字符串映射为整数值
            period_unit_map = {"Month": 1, "Year": 2}
            period_unit = period_unit_map.get(actual_config['period_unit'], 1)  # 默认使用1（月）
            
            # 构建网络接口配置
            network_interface = volcenginesdkecs.CreateInstanceRequestNetworkInterfacesItem(
                subnet_id=actual_config['subnet_id'],
                security_group_ids=actual_config['security_group_ids']
            )
            
            # 构建创建实例请求
            request = volcenginesdkecs.CreateInstanceRequest(
                instance_name=actual_config['name'],
                hostname=actual_config['hostname'],
                instance_type=actual_config['instance_type'],
                image_id=actual_config['image_id'],
                zone_id=actual_config['zone_id'],
                instance_charge_type=actual_config['instance_charge_type'],
                period=actual_config['period'],
                period_unit=period_unit,
                project_name=actual_config['project_name'],
                description=actual_config['description'],
                network_interfaces=[network_interface]
            )
            
            # 发送创建请求
            response = self.ecs_api.create_instance(request)
            logger.info(f"ECS实例创建请求已发送: {response}")
            
            # 等待实例就绪
            if not self.wait_for_instance_status(response.Result.InstanceId, "RUNNING"):
                logger.error("ECS实例创建后未能及时就绪")
                return None, None, None
            
            # 如果配置了EIP，则绑定EIP
            eip_address = None
            if actual_config.get('eip'):
                # 创建EIP
                eip_id, eip_address, eip_name = self.eip_manager.allocate_eip(actual_config['eip'])
                if eip_id:
                    # 绑定EIP到ECS实例
                    self._associate_eip_to_instance(eip_id, response.Result.InstanceId)
                    logger.info(f"已将EIP {eip_address} 绑定到ECS实例 {response.Result.InstanceId}")
                else:
                    logger.error("EIP创建失败，无法绑定到ECS实例")
            
            logger.info(f"ECS实例创建成功: {response.Result.InstanceId}")
            return response.Result.InstanceId, actual_config['name'], eip_address
            
        except Exception as e:
            logger.error(f"创建ECS实例时发生异常: {e}")
            return None, None, None

    @handle_api_exception
    def _associate_eip_to_instance(self, allocation_id, instance_id):
        """将EIP绑定到ECS实例
        
        Args:
            allocation_id: EIP分配ID
            instance_id: ECS实例ID
        
        Returns:
            bool: 操作是否成功
        """
        try:
            # 构建绑定EIP请求
            request = volcenginesdkvpc.AssociateEipAddressRequest(
                allocation_id=allocation_id,
                instance_id=instance_id,
                instance_type="EcsInstance"
            )
            
            # 发送绑定请求
            response = self.vpc_api.associate_eip_address(request)
            logger.info(f"EIP绑定成功: {response}")
            return True
        except Exception as e:
            logger.error(f"绑定EIP时发生异常: {e}")
            return False

    @handle_api_exception
    def delete_instance(self, instance_id):
        """删除ECS实例
        
        Args:
            instance_id: ECS实例ID
        
        Returns:
            bool: 操作是否成功
        """
        try:
            # 构建删除实例请求
            request = volcenginesdkecs.DeleteInstanceRequest(
                instance_id=instance_id
            )
            
            # 发送删除请求
            response = self.ecs_api.delete_instance(request)
            logger.info(f"ECS实例删除成功: {response}")
            return True
        except Exception as e:
            logger.error(f"删除ECS实例时发生异常: {e}")
            return False

# 资源信息记录函数
def write_resource_info(resources, operation_type):
    """记录资源信息到文件
    
    Args:
        resources: 资源信息列表
        operation_type: 操作类型（创建/删除）
    """
    try:
        with open(RESOURCE_INFO_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n## {operation_type}ECS实例 - {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("| 实例ID | 实例名称 | EIP地址 |\n")
            f.write("| --- | --- | --- |\n")
            
            for resource in resources:
                instance_id = resource.get('instance_id', 'N/A')
                instance_name = resource.get('instance_name', 'N/A')
                eip_address = resource.get('eip_address', 'N/A')
                f.write(f"| {instance_id} | {instance_name} | {eip_address} |\n")
                
        logger.info(f"已将{operation_type}的ECS实例信息记录到 {RESOURCE_INFO_FILE}")
    except Exception as e:
        logger.error(f"记录资源信息时发生错误: {e}")

@handle_api_exception
def create_instances():
    """创建ECS实例"""
    # 检查ECS配置是否为空
    if not ecs_configs:
        logger.error("ECS配置为空，请检查配置文件")
        return
        
    # 创建ECS管理器实例
    ecs_manager = ECSManager()
    
    # 遍历所有ECS配置
    created_instances = []
    for ecs_name in ecs_configs:
        logger.info(f"准备创建ECS实例: {ecs_name}")
        config = ecs_configs[ecs_name]
        logger.info(f"ECS配置信息:\n" + 
                   f"- 实例类型: {config['instance_type']}\n" + 
                   f"- 镜像ID: {config['image_id']}\n" + 
                   f"- 可用区: {config['zone_id']}\n" + 
                   f"- 名称: {config['name']}\n" + 
                   f"- 主机名: {config['hostname']}\n" + 
                   f"- 计费类型: {config['instance_charge_type']}\n" + 
                   f"- 计费周期: {config['period']} {config['period_unit']}")
        
        # 创建ECS实例
        logger.info(f"开始创建ECS实例 {ecs_name}...")
        instance_id, instance_name, eip_address = ecs_manager.create_instance(config)
        if not instance_id:
            logger.error(f"ECS实例 {ecs_name} 创建失败")
            continue
            
        logger.info(f"成功创建ECS实例 {instance_name}:\n- 实例ID: {instance_id}\n- EIP地址: {eip_address if eip_address else '无'}")
        created_instances.append({
            'instance_id': instance_id,
            'instance_name': instance_name,
            'eip_address': eip_address
        })
    
    # 输出创建结果汇总
    if created_instances:
        logger.info("\n=== ECS实例创建结果汇总 ===")
        for instance in created_instances:
            logger.info(f"ECS实例 {instance['instance_name']}:\n- 实例ID: {instance['instance_id']}\n- EIP地址: {instance['eip_address'] if instance['eip_address'] else '无'}")
        # 记录创建结果
        write_resource_info(created_instances, "创建")
    else:
        logger.warning("没有成功创建任何ECS实例")