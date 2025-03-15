import time
import os
import logging
from functools import wraps
from volcenginesdkcore.rest import ApiException
import volcenginesdkvpc
import volcenginesdkcore
from configs.api_config import api_config
from configs.eip_config import eip_configs

# 确保logs目录存在
BASE_DIR = os.path.dirname(__file__)
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录（优化日志配置，避免重复配置）
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# 避免重复添加处理器
if not logger.handlers:
    file_handler = logging.FileHandler(os.path.join(log_dir, 'eip_manager.log'))
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# 资源信息文件路径
RESOURCE_INFO_FILE = os.path.join(log_dir, 'eip_resource_info.md')

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

class EIPManager:
    def __init__(self):
        self._init_client()
        self.vpc_api = volcenginesdkvpc.VPCApi()

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)

    @handle_api_exception
    def get_existing_eip_by_name(self, eip_name):
        """根据EIP名称查找现有EIP"""
        list_request = volcenginesdkvpc.DescribeEipAddressesRequest()
        list_response = self.vpc_api.describe_eip_addresses(list_request)
        if hasattr(list_response, 'eip_addresses'):
            for eip in list_response.eip_addresses:
                if eip.name == eip_name:
                    logger.info(f"找到已存在的EIP: {eip.eip_address}")
                    return eip.allocation_id, eip.eip_address, eip.name
        return None, None, None

    @handle_api_exception
    def get_eip_by_id(self, eip_id):
        """根据EIP ID查找EIP"""
        list_request = volcenginesdkvpc.DescribeEipAddressesRequest()
        list_response = self.vpc_api.describe_eip_addresses(list_request)
        if hasattr(list_response, 'eip_addresses'):
            for eip in list_response.eip_addresses:
                if eip.allocation_id == eip_id:
                    logger.info(f"找到指定的EIP ID: {eip_id}")
                    return eip.allocation_id, eip.eip_address, eip.name
        logger.error(f"未找到指定的EIP ID: {eip_id}")
        return None, None, None
    
    @handle_api_exception
    def get_eip_by_address(self, eip_address):
        """根据EIP地址查找EIP"""
        list_request = volcenginesdkvpc.DescribeEipAddressesRequest()
        list_response = self.vpc_api.describe_eip_addresses(list_request)
        if hasattr(list_response, 'eip_addresses'):
            for eip in list_response.eip_addresses:
                if eip.eip_address == eip_address:
                    return eip.allocation_id
        logger.error(f"未找到EIP地址 {eip_address} 对应的allocation_id")
        return None

    @handle_api_exception
    def wait_for_eip_available(self, allocation_id, timeout=60, interval=5):
        """等待EIP变为可用状态
        
        Args:
            allocation_id: EIP的分配ID
            timeout: 超时时间（秒）
            interval: 检查间隔（秒）
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            list_request = volcenginesdkvpc.DescribeEipAddressesRequest()
            list_response = self.vpc_api.describe_eip_addresses(list_request)
            
            if hasattr(list_response, 'eip_addresses'):
                for eip in list_response.eip_addresses:
                    if eip.allocation_id == allocation_id and eip.status == "Available":
                        logger.info(f"EIP {allocation_id} 已经就绪")
                        return True
                    
            logger.info(f"等待EIP {allocation_id} 就绪中...")
            time.sleep(interval)
        
        logger.error(f"等待EIP {allocation_id} 就绪超时")
        return False

    @handle_api_exception
    def allocate_eip(self, eip_config):
        """
        申请EIP
        
        Args:
            eip_config: 可以是eip_config.py中定义的EIP配置名称(字符串)，
                       也可以是直接在redis_configs.py中定义的完整EIP配置(字典)
        
        Returns:
            tuple: (eip_id, eip_address, eip_name)
        """
        try:
            if isinstance(eip_config, str):
                config_name = eip_config
                
                # 修复：正确访问eip_configs字典
                if config_name not in eip_configs:
                    logger.error(f"未找到名为 {config_name} 的EIP配置")
                    return None, None, None
                    
                actual_config = eip_configs[config_name]
                
                # 检查现有EIP
                allocation_id, eip_address, name = self.get_existing_eip_by_name(actual_config['name'])
                if allocation_id:
                    return allocation_id, eip_address, name

                # 创建新的 EIP
                # 将period_unit从字符串映射为整数值
                period_unit_map = {"Month": 1, "Year": 2}
                period_unit = period_unit_map.get(actual_config['period_unit'], 1)  # 默认使用1（月）
                
                request = volcenginesdkvpc.AllocateEipAddressRequest(
                    billing_type=actual_config['billing_type'],
                    bandwidth=actual_config['bandwidth'],
                    isp=actual_config['isp'],
                    name=actual_config['name'],
                    description=actual_config['description'],
                    project_name=actual_config['project_name'],
                    period_unit=period_unit,
                    period=actual_config['period']
                )

                response = self.vpc_api.allocate_eip_address(request)
                logger.info(f"EIP申请成功: {response}")
                
                # 等待EIP就绪
                if not self.wait_for_eip_available(response.allocation_id):
                    logger.error("EIP创建后未能及时就绪")
                    return None, None, None
                    
                return response.allocation_id, response.eip_address, actual_config['name']
                
            elif isinstance(eip_config, dict):
                # 直接使用传入的配置字典
                actual_config = eip_config
                
                # 使用配置字典创建EIP
                # 先检查是否已存在名为配置中指定的 EIP
                allocation_id, eip_address, name = self.get_existing_eip_by_name(actual_config['name'])
                if allocation_id:
                    return allocation_id, eip_address, name

                # 创建新的 EIP
                # 将period_unit从字符串映射为整数值
                period_unit_map = {"Month": 1, "Year": 2}
                period_unit = period_unit_map.get(actual_config['period_unit'], 1)  # 默认使用1（月）
                
                request = volcenginesdkvpc.AllocateEipAddressRequest(
                    billing_type=actual_config['billing_type'],
                    bandwidth=actual_config['bandwidth'],
                    isp=actual_config['isp'],
                    name=actual_config['name'],
                    description=actual_config['description'],
                    project_name=actual_config['project_name'],
                    period_unit=period_unit,
                    period=actual_config['period']
                )

                response = self.vpc_api.allocate_eip_address(request)
                logger.info(f"EIP申请成功: {response}")
                
                # 等待EIP就绪
                if not self.wait_for_eip_available(response.allocation_id):
                    logger.error("EIP创建后未能及时就绪")
                    return None, None, None
                    
                return response.allocation_id, response.eip_address, actual_config['name']
                
            else:
                logger.error(f"不支持的EIP配置类型: {type(eip_config)}")
                return None, None, None
            
        except Exception as e:
            logger.error(f"申请EIP时发生异常: {e}")
            return None, None, None

    @handle_api_exception
    def release_eip(self, eip_address=None, allocation_id=None):
        """释放指定的EIP资源
        :param eip_address: EIP地址
        :param allocation_id: EIP的分配ID
        :return: bool 操作是否成功
        """
        # 参数验证
        if not allocation_id and not eip_address:
            logger.error("需要提供eip_address或allocation_id参数")
            return False
            
        # 如果提供了eip_address但没有allocation_id，需要先查找对应的allocation_id
        if eip_address and not allocation_id:
            allocation_id = self.get_eip_by_address(eip_address)
            if not allocation_id:
                return False
        
        # 释放EIP
        print(f"释放EIP，allocation_id: {allocation_id}")
        release_request = volcenginesdkvpc.ReleaseEipAddressRequest(
            allocation_id=allocation_id
        )
        self.vpc_api.release_eip_address(release_request)
        logger.info(f"已成功释放EIP，allocation_id: {allocation_id}")
        return True

def write_resource_info(records, action_type="创建"):
    """将资源信息写入文件
    :param records: 资源记录列表
    :param action_type: 操作类型("创建"或"释放")
    """
    with open(RESOURCE_INFO_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"记录时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"# EIP资源{action_type}记录\n\n")
        
        for record in records:
            if action_type == "创建":
                eip_config = eip_configs.get(record['name'], {})
                f.write(f"## EIP: {record['name']}\n")
                f.write(f"### 基本信息\n")
                f.write(f"- 分配ID: {record['allocation_id']}\n")
                f.write(f"- EIP地址: {record['eip_address']}\n")
                f.write(f"- 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write(f"### 配置信息\n")
                f.write(f"- 计费类型: {eip_config.get('billing_type', 'N/A')}\n")
                f.write(f"- 带宽: {eip_config.get('bandwidth', 'N/A')} Mbps\n")
                f.write(f"- ISP: {eip_config.get('isp', 'N/A')}\n")
                f.write(f"- 项目名称: {eip_config.get('project_name', 'N/A')}\n")
                f.write(f"- 计费周期: {eip_config.get('period', 'N/A')} {eip_config.get('period_unit', 'N/A')}\n")
                f.write(f"- 描述: {eip_config.get('description', 'N/A')}\n\n")
            else:
                f.write(f"## EIP: {record['eip_identifier']}\n")
                f.write(f"- 状态: {'成功' if record['status'] == 'success' else '失败'}\n")
                f.write(f"- 释放时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

@handle_api_exception
def create_eips():
    """创建EIP资源"""
    # 检查EIP配置是否为空
    if not eip_configs:
        logger.error("EIP配置为空，请检查配置文件")
        return
        
    # 创建EIP管理器实例
    eip_manager = EIPManager()
    
    # 遍历所有EIP配置
    created_eips = []
    for eip_name in eip_configs:
        logger.info(f"准备创建EIP: {eip_name}")
        config = eip_configs[eip_name]
        logger.info(f"EIP配置信息:\n" + 
                   f"- 计费类型: {config['billing_type']}\n" + 
                   f"- 带宽: {config['bandwidth']} Mbps\n" + 
                   f"- ISP: {config['isp']}\n" + 
                   f"- 名称: {config['name']}\n" + 
                   f"- 项目: {config['project_name']}\n" + 
                   f"- 计费周期: {config['period']} {config['period_unit']}")
        
        # 创建EIP
        logger.info(f"开始创建EIP {eip_name}...")
        allocation_id, eip_address, eip_name = eip_manager.allocate_eip(config)
        if not allocation_id:
            logger.error(f"EIP {eip_name} 创建失败")
            continue
            
        logger.info(f"成功创建EIP {eip_name}:\n- 分配ID: {allocation_id}\n- EIP地址: {eip_address}")
        created_eips.append({
            'name': eip_name,
            'allocation_id': allocation_id,
            'eip_address': eip_address
        })
    
    # 输出创建结果汇总
    if created_eips:
        logger.info("\n=== EIP创建结果汇总 ===")
        for eip in created_eips:
            logger.info(f"EIP {eip['name']}:\n- 分配ID: {eip['allocation_id']}\n- EIP地址: {eip['eip_address']}")
        # 记录创建结果
        write_resource_info(created_eips, "创建")
    else:
        logger.warning("没有成功创建任何EIP")

@handle_api_exception
def release_eips(target_eips):
    """释放指定的EIP资源
    :param target_eips: 单个EIP ID/地址或其列表
    """
    # 创建EIP管理器实例
    eip_manager = EIPManager()
    
    # 将单个输入转换为列表格式
    if isinstance(target_eips, str):
        target_eips = [target_eips]
        
    if not target_eips:
        logger.error("未指定要释放的EIP")
        return
        
    logger.info("\n=== 开始释放指定的EIP ===")
    released_results = []
    
    for target_eip in target_eips:
        logger.info(f"正在释放EIP: {target_eip}")
        # 判断是否为EIP ID（假设EIP ID格式为"eip-xxx"）
        is_eip_id = target_eip.startswith('eip-')
        
        if is_eip_id:
            success = eip_manager.release_eip(allocation_id=target_eip)
            eip_identifier = target_eip
        else:
            success = eip_manager.release_eip(eip_address=target_eip)
            eip_identifier = target_eip
            
        if success:
            logger.info(f"成功释放EIP: {eip_identifier}")
            released_results.append({
                'eip_identifier': eip_identifier,
                'status': 'success'
            })
        else:
            logger.error(f"释放EIP失败: {eip_identifier}")
            released_results.append({
                'eip_identifier': eip_identifier,
                'status': 'failed'
            })
    
    # 记录释放结果
    if released_results:
        write_resource_info(released_results, "释放")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='EIP资源管理工具')
    parser.add_argument('action', choices=['create', 'release'], help='执行的操作：create（创建）或 release（释放）')
    parser.add_argument('--eips', nargs='+', help='要释放的EIP地址列表，仅在release操作时需要')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        create_eips()
    elif args.action == 'release':
        if not args.eips:
            logger.error('执行release操作时必须指定--eips参数')
        else:
            release_eips(args.eips)