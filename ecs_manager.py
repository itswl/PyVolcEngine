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
    def wait_for_instance_status(self, instance_id, target_status="RUNNING", timeout=600, interval=100):
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
            if hasattr(list_response, 'instances'):
                for instance in list_response.instances:
                    if instance.instance_id == instance_id:
                        return instance.status

        
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
            
            # 打印配置信息以便调试
            logger.info(f"使用以下配置创建ECS实例:")
            logger.info(f"实例名称: {actual_config['name']}")
            logger.info(f"镜像ID: {actual_config['image_id']}")
            logger.info(f"实例类型: {actual_config['instance_type_id']}") 
            
            # 创建网络接口对象
            req_network_interfaces = volcenginesdkecs.NetworkInterfaceForRunInstancesInput(
                security_group_ids=actual_config['security_group_ids'],
                subnet_id=actual_config['subnet_id']
            )
            
            # 创建卷对象
            volumes = []
            if 'volumes' in actual_config and actual_config['volumes']:
                for volume in actual_config['volumes']:
                    req_volume = volcenginesdkecs.VolumeForRunInstancesInput(
                        delete_with_instance=str(volume.get('delete_with_instance', True)).lower(),
                        size=volume['size'],
                        volume_type=volume.get('volume_type', 'ESSD_PL0')
                    )
                    volumes.append(req_volume)
            
            # 创建EIP对象
            req_eip_address = None
            if 'eip' in actual_config and actual_config['eip']:
                req_eip_address = volcenginesdkecs.EipAddressForRunInstancesInput(
                    bandwidth_mbps=actual_config['eip'].get('bandwidth', 100),
                    charge_type="PayByTraffic" if actual_config['eip'].get('billing_type') == 3 else "PayByBandwidth",
                    isp=actual_config['eip'].get('isp', 'BGP'),
                    release_with_instance=True
                )
            
            # 准备请求参数
            request_params = {
                'image_id': actual_config['image_id'],
                'instance_type_id': actual_config['instance_type_id'],
                'zone_id': actual_config['zone_id'],
                'count': 1,
                'network_interfaces': [req_network_interfaces]
            }
            
            # 添加EIP参数
            if req_eip_address:
                request_params['eip_address'] = req_eip_address
            
            # 添加其他参数
            if 'name' in actual_config:
                request_params['instance_name'] = actual_config['name']
            if 'hostname' in actual_config:
                request_params['hostname'] = actual_config['hostname']
            if 'instance_charge_type' in actual_config:
                request_params['instance_charge_type'] = actual_config['instance_charge_type']
            if 'period' in actual_config:
                request_params['period'] = actual_config['period']
            if 'period_unit' in actual_config:
                request_params['period_unit'] = actual_config['period_unit']
            if 'description' in actual_config:
                request_params['description'] = actual_config['description']
            
            # 添加密码参数 - 这是必需的
            if 'password' in actual_config:
                request_params['password'] = actual_config['password']
            
            # 添加其他缺失的参数
            if 'auto_renew' in actual_config:
                request_params['auto_renew'] = actual_config['auto_renew']
            if 'auto_renew_period' in actual_config:
                request_params['auto_renew_period'] = actual_config['auto_renew_period']
            if 'user_data' in actual_config:
                request_params['user_data'] = actual_config['user_data']
            if 'install_run_command_agent' in actual_config:
                request_params['install_run_command_agent'] = actual_config['install_run_command_agent']
            if volumes:
                request_params['volumes'] = volumes
            if 'dry_run' in actual_config:
                request_params['dry_run'] = actual_config['dry_run']
            
            # 创建请求对象 - 使用构造函数传参方式
            request = volcenginesdkecs.RunInstancesRequest(**request_params)
            print(request)
            
            # 发送创建请求
            logger.info(f"发送ECS实例创建请求...")
            response = self.ecs_api.run_instances(request)
            logger.info(f"ECS实例创建请求已发送: {response}")
            
            # 检查是否是dry_run模式
            if actual_config.get('dry_run', False):
                logger.info("这是一个dry_run请求，不会实际创建实例")
                return None, None, None
            
            # 处理响应结果 - 适应不同的响应结构
            instance_ids = response.get('instance_ids')
            # print(instance_ids)
        
            if not instance_ids:
                logger.error("响应中没有实例ID信息")
                return None, None, None
                
            # 等待实例就绪
            for instance_id in instance_ids:
                if not self.wait_for_instance_status(instance_id, "RUNNING"):
                    logger.error("ECS实例创建后未能及时就绪")
                    return None, None, None
                
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
                instance_type_id="EcsInstance"
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
                   f"- 实例类型: {config['instance_type_id']}\n" + 
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

@handle_api_exception
def delete_instances(instance_ids=None):
    """删除ECS实例
    
    Args:
        instance_ids: 要删除的ECS实例ID列表，如果为None，则尝试获取所有实例
    
    Returns:
        bool: 操作是否成功
    """
    # 创建ECS管理器实例
    ecs_manager = ECSManager()
    
    # 如果未提供实例ID列表，则尝试获取所有实例
    if not instance_ids:
        try:
            list_request = volcenginesdkecs.DescribeInstancesRequest()
            list_response = ecs_manager.ecs_api.describe_instances(list_request)
            
            instance_ids = []
            if hasattr(list_response, 'Result') and hasattr(list_response.Result, 'Instances'):
                for instance in list_response.Result.Instances:
                    instance_ids.append(instance.InstanceId)
                    
            if not instance_ids:
                logger.warning("未找到任何ECS实例")
                return False
                
            logger.info(f"找到 {len(instance_ids)} 个ECS实例")
        except Exception as e:
            logger.error(f"获取ECS实例列表时发生异常: {e}")
            return False
    
    # 删除实例
    deleted_instances = []
    for instance_id in instance_ids:
        # 获取实例信息
        instance_id, instance_name = ecs_manager.get_instance_by_id(instance_id)
        if not instance_id:
            logger.error(f"未找到ECS实例ID: {instance_id}")
            continue
            
        # 检查是否有关联的EIP
        eip_address = None
        # 这里可以添加获取EIP的逻辑，如果需要的话
        
        # 删除ECS实例
        logger.info(f"开始删除ECS实例 {instance_id}...")
        if ecs_manager.delete_instance(instance_id):
            logger.info(f"成功删除ECS实例: {instance_id}")
            deleted_instances.append({
                'instance_id': instance_id,
                'instance_name': instance_name,
                'eip_address': eip_address
            })
        else:
            logger.error(f"ECS实例 {instance_id} 删除失败")
    
    # 输出删除结果汇总
    if deleted_instances:
        logger.info("\n=== ECS实例删除结果汇总 ===")
        for instance in deleted_instances:
            logger.info(f"已删除ECS实例 {instance['instance_name']}:\n- 实例ID: {instance['instance_id']}")
        # 记录删除结果
        write_resource_info(deleted_instances, "删除")
        return True
    else:
        logger.warning("没有成功删除任何ECS实例")
        return False

# 如果需要，您可以在这里添加一个main函数，用于命令行调用
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python ecs_manager.py [create|delete] [instance_ids...]")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "create":
        create_instances()
    elif command == "delete":
        instance_ids = sys.argv[2:] if len(sys.argv) > 2 else None
        delete_instances(instance_ids)
    else:
        print(f"未知命令: {command}")
        print("用法: python ecs_manager.py [create|delete] [instance_ids...]")
        sys.exit(1)