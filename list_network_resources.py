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
file_handler = logging.FileHandler(os.path.join(log_dir, 'network_resources.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class NetworkResourceManager(BaseResourceManager):
    def __init__(self):
        super().__init__("Network")
        self.vpc_api = volcenginesdkvpc.VPCApi()

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)

    def list_resources(self):
        """列出所有网络资源"""
        vpcs = self._list_vpcs()
        for vpc in vpcs:
            vpc['subnets'] = self._list_subnets(vpc['vpc_id'])
            vpc['security_groups'] = self._list_security_groups(vpc['vpc_id'])
        return vpcs

    def _list_vpcs(self):
        """列出所有VPC信息"""
        try:
            request = volcenginesdkvpc.DescribeVpcsRequest()
            response = self.vpc_api.describe_vpcs(request)
            
            if not hasattr(response, 'vpcs'):
                self.logger.info("未找到任何VPC")
                return []
            
            return [self._format_vpc_info(vpc) for vpc in response.vpcs]
            
        except ApiException as e:
            self.logger.error(f"获取VPC列表时发生异常: {e}")
            return []

    def _list_subnets(self, vpc_id):
        """列出指定VPC的所有子网信息"""
        try:
            request = volcenginesdkvpc.DescribeSubnetsRequest()
            request.vpc_id = vpc_id
            response = self.vpc_api.describe_subnets(request)
            
            if not hasattr(response, 'subnets'):
                self.logger.info(f"未找到VPC {vpc_id} 的任何子网")
                return []
            
            return [self._format_subnet_info(subnet) for subnet in response.subnets]
            
        except ApiException as e:
            self.logger.error(f"获取子网列表时发生异常: {e}")
            return []

    def _list_security_groups(self, vpc_id):
        """列出指定VPC的所有安全组信息"""
        try:
            request = volcenginesdkvpc.DescribeSecurityGroupsRequest()
            request.vpc_id = vpc_id
            response = self.vpc_api.describe_security_groups(request)
            
            if not hasattr(response, 'security_groups'):
                self.logger.info(f"未找到VPC {vpc_id} 的任何安全组")
                return []
            
            return [self._format_security_group_info(sg) for sg in response.security_groups]
            
        except ApiException as e:
            self.logger.error(f"获取安全组列表时发生异常: {e}")
            return []

    def _format_vpc_info(self, vpc):
        """格式化VPC信息"""
        return {
            'vpc_id': vpc.vpc_id,
            'vpc_name': vpc.vpc_name,
            'cidr_block': vpc.cidr_block,
            'status': vpc.status,
            'creation_time': vpc.creation_time,
            'tags': getattr(vpc, 'tags', [])
        }

    def _format_subnet_info(self, subnet):
        """格式化子网信息"""
        return {
            'subnet_id': subnet.subnet_id,
            'subnet_name': subnet.subnet_name,
            'vpc_id': subnet.vpc_id,
            'cidr_block': subnet.cidr_block,
            'zone_id': subnet.zone_id,
            'status': subnet.status,
            'creation_time': subnet.creation_time,
            'tags': getattr(subnet, 'tags', [])
        }

    def _format_security_group_info(self, sg):
        """格式化安全组信息"""
        sg_info = {
            'security_group_id': sg.security_group_id,
            'security_group_name': sg.security_group_name,
            'vpc_id': sg.vpc_id,
            'description': getattr(sg, 'description', ''),
            'creation_time': sg.creation_time,
            'tags': getattr(sg, 'tags', [])
        }
        
        # 获取安全组规则
        try:
            request = volcenginesdkvpc.DescribeSecurityGroupAttributesRequest(
                security_group_id=sg.security_group_id,
            )
            response = self.vpc_api.describe_security_group_attributes(request)
            
            if hasattr(response, 'permissions') and response.permissions:
                sg_info['ingress_rules'] = []
                sg_info['egress_rules'] = []
                
                for rule in response.permissions:
                    rule_info = {
                        'policy': rule.policy,
                        'protocol': rule.protocol,
                        'port_range': '-1/-1' if rule.port_start == -1 and rule.port_end == -1 else f'{rule.port_start}/{rule.port_end}',
                        'cidr_ip': rule.cidr_ip if rule.cidr_ip else '',
                        'source_group_id': getattr(rule, 'source_group_id', ''),
                        'prefix_list_cidrs': getattr(rule, 'prefix_list_cidrs', []),
                        'description': getattr(rule, 'description', ''),
                        'priority': getattr(rule, 'priority', 100)
                    }
                    
                    if rule.direction == 'ingress':
                        sg_info['ingress_rules'].append(rule_info)
                    elif rule.direction == 'egress':
                        sg_info['egress_rules'].append(rule_info)
        except ApiException as e:
            self.logger.error(f"获取安全组 {sg.security_group_id} 规则时发生异常: {e}")
            
        return sg_info

    def _write_resources_to_file(self, file, vpcs):
        """将网络资源信息写入文件"""
        # 写入VPC基本信息表格
        file.write("### VPC资源信息\n")
        file.write("| VPC名称 | VPC ID | CIDR | 状态 | 创建时间 | 标签 |\n")
        file.write("|---------|---------|------|------|----------|------|\n")
        for vpc in vpcs:
            # 处理标签信息
            tags_str = ""
            if vpc['tags']:
                tags_str = "; ".join([f"{tag.key}: {tag.value}" for tag in vpc['tags']])
            file.write(f"| {vpc['vpc_name']} | {vpc['vpc_id']} | {vpc['cidr_block']} | {vpc['status']} | {vpc['creation_time']} | {tags_str} |\n")
        file.write("\n")

        # 写入子网信息表格
        file.write("### 子网资源信息\n")
        file.write("| VPC名称 | 子网名称 | 子网ID | CIDR | 可用区 | 状态 | 创建时间 | 标签 |\n")
        file.write("|---------|----------|---------|------|--------|------|----------|------|\n")
        for vpc in vpcs:
            for subnet in vpc['subnets']:
                # 处理标签信息
                tags_str = ""
                if subnet['tags']:
                    tags_str = "; ".join([f"{tag.key}: {tag.value}" for tag in subnet['tags']])
                file.write(f"| {vpc['vpc_name']} | {subnet['subnet_name']} | {subnet['subnet_id']} | {subnet['cidr_block']} | {subnet['zone_id']} | {subnet['status']} | {subnet['creation_time']} | {tags_str} |\n")
        file.write("\n")

        # 写入安全组信息表格
        file.write("### 安全组资源信息\n")
        file.write("| VPC名称 | 安全组名称 | 安全组ID | 描述 | 创建时间 | 标签 |\n")
        file.write("|---------|------------|------------|------|----------|------|\n")
        for vpc in vpcs:
            for sg in vpc['security_groups']:
                # 处理标签信息
                tags_str = ""
                if sg['tags']:
                    tags_str = "; ".join([f"{tag.key}: {tag.value}" for tag in sg['tags']])
                file.write(f"| {vpc['vpc_name']} | {sg['security_group_name']} | {sg['security_group_id']} | {sg['description']} | {sg['creation_time']} | {tags_str} |\n")
        file.write("\n")

        # 写入安全组规则信息表格
        file.write("### 安全组规则信息\n")
        file.write("| VPC名称 | 安全组名称 | 规则类型 | 协议 | 端口范围 | 源/目标IP | 源/目标安全组 | 策略 | 优先级 | 描述 |\n")
        file.write("|---------|------------|----------|------|----------|------------|--------------|------|--------|------|\n")
        for vpc in vpcs:
            for sg in vpc['security_groups']:
                # 写入入站规则
                if 'ingress_rules' in sg and sg['ingress_rules']:
                    for rule in sg['ingress_rules']:
                        file.write(f"| {vpc['vpc_name']} | {sg['security_group_name']} | 入站 | {rule['protocol']} | {rule['port_range']} | {rule['cidr_ip']} | {rule['source_group_id']} | {rule['policy']} | {rule['priority']} | {rule['description']} |\n")
                
                # 写入出站规则
                if 'egress_rules' in sg and sg['egress_rules']:
                    for rule in sg['egress_rules']:
                        file.write(f"| {vpc['vpc_name']} | {sg['security_group_name']} | 出站 | {rule['protocol']} | {rule['port_range']} | {rule['cidr_ip']} | {rule['source_group_id']} | {rule['policy']} | {rule['priority']} | {rule['description']} |\n")
        file.write("\n")

def main():
    try:
        manager = NetworkResourceManager()
        resources = manager.list_resources()
        manager.write_to_markdown(resources)
        print("成功完成所有网络资源信息的收集和记录")
    except Exception as e:
        print(f"执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()