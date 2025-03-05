import volcenginesdkcore
import volcenginesdkvpc
from volcenginesdkcore.rest import ApiException
import time
import logging
import os
from configs.api_config import api_config

# 确保logs目录存在
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(log_dir, 'eip_resources.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class EIPResourceManager:
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

    def list_eips(self):
        """列出所有EIP详细信息"""
        try:
            request = volcenginesdkvpc.DescribeEipAddressesRequest()
            response = self.vpc_api.describe_eip_addresses(request)
            if not hasattr(response, 'eip_addresses'):
                logger.info("未找到任何EIP资源")
                return []
            
            eip_list = []
            for eip in response.eip_addresses:
                eip_info = {
                    'release_with_instance': eip.release_with_instance,
                    'allocation_id': eip.allocation_id,
                    'allocation_time': eip.allocation_time,
                    'eip_address': eip.eip_address,
                    'status': eip.status,
                    'isp': eip.isp,
                    'bandwidth': eip.bandwidth,
                    'billing_type': eip.billing_type,
                    'name': eip.name if hasattr(eip, 'name') else '',
                    'description': eip.description if hasattr(eip, 'description') else '',
                    'updated_at': eip.updated_at,
                    'expired_time': eip.expired_time if hasattr(eip, 'expired_time') else '',
                    'project_name': eip.project_name if hasattr(eip, 'project_name') else '',
                    'instance_id': eip.instance_id if hasattr(eip, 'instance_id') else '',
                    'instance_type': eip.instance_type if hasattr(eip, 'instance_type') else '',
                    'network_interface_id': eip.network_interface_id if hasattr(eip, 'network_interface_id') else '',
                    'private_ip_address': eip.private_ip_address if hasattr(eip, 'private_ip_address') else '',
                    'tags': eip.tags if hasattr(eip, 'tags') else []
                }
                eip_list.append(eip_info)
            
            return eip_list
            
        except ApiException as e:
            logger.error(f"获取EIP列表时发生异常: {e}")
            return []

    def write_eips_to_file(self):
        """将所有EIP资源信息写入文件"""
        eip_info_path = os.path.join(log_dir, 'eip_resources_info.md')
        
        with open(eip_info_path, 'w', encoding='utf-8') as f:
            # 写入标题和时间戳
            f.write(f"# EIP资源信息记录\n\n")
            f.write(f"## 记录时间\n{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 获取并写入EIP信息
            eips = self.list_eips()
            if not eips:
                f.write("未发现任何EIP资源\n")
                return
            
            f.write(f"## EIP资源列表\n")
            for eip in eips:
                f.write(f"### EIP: {eip['eip_address']}\n")
                f.write(f"- 分配ID: {eip['allocation_id']}\n")
                f.write(f"- 状态: {eip['status']}\n")
                f.write(f"- ISP: {eip['isp']}\n")
                f.write(f"- 带宽: {eip['bandwidth']} Mbps\n")
                f.write(f"- 计费类型: {eip['billing_type']}\n")
                f.write(f"- 随实例删除: {eip['release_with_instance']}\n")
                f.write(f"- 创建时间: {eip['allocation_time']}\n")
                if eip['name']:
                    f.write(f"- 名称: {eip['name']}\n")
                if eip['description']:
                    f.write(f"- 描述: {eip['description']}\n")
                f.write(f"- 更新时间: {eip['updated_at']}\n")
                if eip['expired_time']:
                    f.write(f"- 过期时间: {eip['expired_time']}\n")
                if eip['project_name']:
                    f.write(f"- 项目名称: {eip['project_name']}\n")
                
                # 绑定信息
                if eip['instance_id']:
                    f.write(f"\n#### 绑定信息\n")
                    f.write(f"- 实例ID: {eip['instance_id']}\n")
                    f.write(f"- 实例类型: {eip['instance_type']}\n")
                    if eip['network_interface_id']:
                        f.write(f"- 网卡ID: {eip['network_interface_id']}\n")
                    if eip['private_ip_address']:
                        f.write(f"- 私网IP: {eip['private_ip_address']}\n")
                
                # 标签信息
                if eip['tags']:
                    f.write(f"\n#### 标签信息\n")
                    for tag in eip['tags']:
                        f.write(f"- {tag.key}: {tag.value}\n")
                f.write("\n")
                
            f.write("---\n\n")
            
        logger.info(f"EIP资源信息已写入文件: {eip_info_path}")

def main():
    try:
        manager = EIPResourceManager()
        manager.write_eips_to_file()
        logger.info("成功完成所有EIP资源信息的收集和记录")
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()