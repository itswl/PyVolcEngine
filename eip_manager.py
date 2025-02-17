import time
from volcenginesdkcore.rest import ApiException
import volcenginesdkvpc
from configs.api_config import api_config
from configs.eip_config import eip_configs
import logging
import volcenginesdkcore

import os
# 确保logs目录存在
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
# 添加文件处理器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(log_dir, 'eip_manager.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


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

    def allocate_eip(self, eip_name):
        try:
            # 获取EIP配置
            if eip_name not in eip_configs:
                logger.error(f"未找到名为 {eip_name} 的EIP配置")
                return None, None
                
            eip_config = eip_configs[eip_name]
            
            # 先列出现有的 EIP
            list_request = volcenginesdkvpc.DescribeEipAddressesRequest()
            list_response = self.vpc_api.describe_eip_addresses(list_request)
            # 检查是否已存在名为配置中指定的 EIP
            if hasattr(list_response, 'eip_addresses'):
                for eip in list_response.eip_addresses:
                    if eip.name == eip_config['name']:
                        logger.info(f"找到已存在的EIP: {eip.eip_address}")
                        return eip.allocation_id, eip.eip_address, eip.name

            # 如果不存在，创建新的 EIP
            # 将period_unit从字符串映射为整数值
            period_unit_map = {"Month": 1, "Year": 2}
            period_unit = period_unit_map.get(eip_config['period_unit'], 1)  # 默认使用1（月）
            
            request = volcenginesdkvpc.AllocateEipAddressRequest(
                billing_type=eip_config['billing_type'],
                bandwidth=eip_config['bandwidth'],
                isp=eip_config['isp'],
                name=eip_config['name'],
                description=eip_config['description'],
                project_name=eip_config['project_name'],
                period_unit=period_unit,
                renew_type=eip_config['renew_type'],
                period=eip_config['period']
            )
            
            response = self.vpc_api.allocate_eip_address(request)
            logger.info(f"EIP申请成功: {response}")
            return response.allocation_id, response.eip_address
            
        except ApiException as e:
            logger.error(f"申请EIP时发生异常: {e}")
            return None, None

    def release_eip(self, eip_address):
        """释放指定的EIP资源
        :param eip_address: EIP地址
        :return: bool 操作是否成功
        """
        try:
            # 先获取EIP的allocation_id
            list_request = volcenginesdkvpc.DescribeEipAddressesRequest()
            list_response = self.vpc_api.describe_eip_addresses(list_request)
            
            allocation_id = None
            if hasattr(list_response, 'eip_addresses'):
                for eip in list_response.eip_addresses:
                    if eip.eip_address == eip_address:
                        allocation_id = eip.allocation_id
                        break
            
            if not allocation_id:
                logger.error(f"未找到EIP地址 {eip_address} 对应的allocation_id")
                return False
            
            # 创建释放请求
            release_request = volcenginesdkvpc.ReleaseEipAddressRequest(
                allocation_id=allocation_id
            )
            
            # 执行释放操作
            self.vpc_api.release_eip_address(release_request)
            logger.info(f"已成功释放EIP: {eip_address}")
            return True
            
        except ApiException as e:
            logger.error(f"释放EIP时发生错误: {e}")
            return False

def create_eips():
    """创建EIP资源"""
    try:
        # 创建EIP管理器实例
        eip_manager = EIPManager()
        
        # 检查EIP配置是否为空
        if not eip_configs:
            logger.error("EIP配置为空，请检查配置文件")
            return
            
        # 遍历所有EIP配置
        created_eips = []
        for eip_name in eip_configs:
            logger.info(f"准备创建EIP: {eip_name}")
            logger.info(f"EIP配置信息:\n" + 
                       f"- 计费类型: {eip_configs[eip_name]['billing_type']}\n" + 
                       f"- 带宽: {eip_configs[eip_name]['bandwidth']} Mbps\n" + 
                       f"- ISP: {eip_configs[eip_name]['isp']}\n" + 
                       f"- 名称: {eip_configs[eip_name]['name']}\n" + 
                       f"- 项目: {eip_configs[eip_name]['project_name']}\n" + 
                       f"- 计费周期: {eip_configs[eip_name]['period']} {eip_configs[eip_name]['period_unit']}")
            
            # 创建EIP
            logger.info(f"开始创建EIP {eip_name}...")
            allocation_id, eip_address, eip_name = eip_manager.allocate_eip(eip_name)
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
                
            # 将EIP资源信息写入日志文件，使用追加模式
            with open('eip_resource_info.md', 'a', encoding='utf-8') as f:
                # 添加分隔符和时间戳
                f.write(f"\n{'='*50}\n")
                f.write(f"记录时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"# EIP资源创建记录\n\n")
                
                for eip_name in created_eips:
                    eip_config = eip_configs[eip_name['name']]
                    f.write(f"## EIP: {eip_name['name']}\n")
                    f.write(f"### 基本信息\n")
                    f.write(f"- 分配ID: {eip_name['allocation_id']}\n")
                    f.write(f"- EIP地址: {eip_name['eip_address']}\n")
                    f.write(f"- 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write(f"### 配置信息\n")
                    f.write(f"- 计费类型: {eip_config['billing_type']}\n")
                    f.write(f"- 带宽: {eip_config['bandwidth']} Mbps\n")
                    f.write(f"- ISP: {eip_config['isp']}\n")
                    f.write(f"- 项目名称: {eip_config['project_name']}\n")
                    f.write(f"- 计费周期: {eip_config['period']} {eip_config['period_unit']}\n")
                    f.write(f"- 描述: {eip_config['description']}\n\n")
        else:
            logger.warning("没有成功创建任何EIP")
            
    except Exception as e:
        logger.error(f"创建EIP过程中发生错误: {e}")
        return

def release_eips(target_eip_addresses):
    """释放指定的EIP资源
    :param target_eip_addresses: 单个EIP地址或EIP地址列表
    """
    try:
        # 创建EIP管理器实例
        eip_manager = EIPManager()
        
        # 将单个IP地址转换为列表格式
        if isinstance(target_eip_addresses, str):
            target_eip_addresses = [target_eip_addresses]
            
        if not target_eip_addresses:
            logger.error("未指定要释放的EIP地址")
            return
            
        logger.info("\n=== 开始释放指定的EIP ===")
        released_results = []
        
        for target_eip_address in target_eip_addresses:
            logger.info(f"正在释放EIP: {target_eip_address}")
            if eip_manager.release_eip(target_eip_address):
                logger.info(f"成功释放EIP: {target_eip_address}")
                released_results.append({
                    'eip_address': target_eip_address,
                    'status': 'success'
                })
            else:
                logger.error(f"释放EIP失败: {target_eip_address}")
                released_results.append({
                    'eip_address': target_eip_address,
                    'status': 'failed'
                })
        
        # 记录释放结果
        if released_results:
            eip_resource_info_path = os.path.join(log_dir, 'eip_resource_info.md')
            with open(eip_resource_info_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"记录时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"# EIP资源释放记录\n\n")
                
                for result in released_results:
                    f.write(f"## EIP: {result['eip_address']}\n")
                    f.write(f"- 状态: {'成功' if result['status'] == 'success' else '失败'}\n")
                    f.write(f"- 释放时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    except Exception as e:
        logger.error(f"释放EIP过程中发生错误: {e}")
        return

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
