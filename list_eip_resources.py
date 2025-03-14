import volcenginesdkcore
import volcenginesdkvpc
from volcenginesdkcore.rest import ApiException
import time
import logging
import os
from configs.api_config import api_config
from base_resource_manager import BaseResourceManager

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

class EIPResourceManager(BaseResourceManager):
    def __init__(self):
        super().__init__("EIP")
        self.vpc_api = volcenginesdkvpc.VPCApi()

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)

    def list_resources(self):
        """列出所有EIP详细信息"""
        try:
            request = volcenginesdkvpc.DescribeEipAddressesRequest()
            response = self.vpc_api.describe_eip_addresses(request)
            if not hasattr(response, 'eip_addresses'):
                self.logger.info("未找到任何EIP资源")
                return []
            
            return [self._format_eip_info(eip) for eip in response.eip_addresses]
            
        except ApiException as e:
            self.logger.error(f"获取EIP列表时发生异常: {e}")
            return []

    def _format_eip_info(self, eip):
        """格式化EIP信息"""
        return {
            'release_with_instance': eip.release_with_instance,
            'allocation_id': eip.allocation_id,
            'allocation_time': eip.allocation_time,
            'eip_address': eip.eip_address,
            'status': eip.status,
            'isp': eip.isp,
            'bandwidth': eip.bandwidth,
            'billing_type': eip.billing_type,
            'name': getattr(eip, 'name', ''),
            'description': getattr(eip, 'description', ''),
            'updated_at': eip.updated_at,
            'expired_time': getattr(eip, 'expired_time', ''),
            'project_name': getattr(eip, 'project_name', ''),
            'instance_id': getattr(eip, 'instance_id', ''),
            'instance_type': getattr(eip, 'instance_type', ''),
            'network_interface_id': getattr(eip, 'network_interface_id', ''),
            'private_ip_address': getattr(eip, 'private_ip_address', ''),
            'tags': getattr(eip, 'tags', [])
        }

    def _write_resources_to_file(self, file, eips):
        """将EIP信息写入文件"""
        # 写入EIP信息表格
        file.write("### EIP资源信息\n")
        file.write("| EIP地址 | 分配ID | 状态 | ISP | 带宽(Mbps) | 计费类型 | 随实例删除 | 创建时间 | 名称 | 描述 | 更新时间 | 过期时间 | 项目名称 | 实例ID | 实例类型 | 网卡ID | 私网IP | 标签 |\n")
        file.write("|---------|---------|------|-----|------------|----------|------------|----------|------|------|----------|----------|----------|----------|----------|--------|--------|------|\n")
        for eip in eips:
            # 处理标签信息
            tags_str = ""
            if eip['tags']:
                tags_str = "; ".join([f"{tag.key}: {tag.value}" for tag in eip['tags']])
            
            file.write(f"| {eip['eip_address']} | {eip['allocation_id']} | {eip['status']} | {eip['isp']} | {eip['bandwidth']} | {eip['billing_type']} | {eip['release_with_instance']} | {eip['allocation_time']} | {eip['name']} | {eip['description']} | {eip['updated_at']} | {eip['expired_time']} | {eip['project_name']} | {eip['instance_id']} | {eip['instance_type']} | {eip['network_interface_id']} | {eip['private_ip_address']} | {tags_str} |\n")
        file.write("\n")

def main():
    try:
        manager = EIPResourceManager()
        eips = manager.list_resources()
        manager.write_to_markdown(eips)
        print("成功完成所有EIP资源信息的收集和记录")
    except Exception as e:
        print(f"执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()