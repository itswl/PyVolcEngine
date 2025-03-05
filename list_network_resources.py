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
file_handler = logging.FileHandler(os.path.join(log_dir, 'network_resources.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class NetworkResourceManager:
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

    def list_vpcs(self):
        """列出所有VPC信息"""
        try:
            request = volcenginesdkvpc.DescribeVpcsRequest()
            response = self.vpc_api.describe_vpcs(request)
            
            if not hasattr(response, 'vpcs'):
                logger.info("未找到任何VPC")
                return []
            
            vpc_list = []
            for vpc in response.vpcs:
                vpc_info = {
                    'vpc_id': vpc.vpc_id,
                    'vpc_name': vpc.vpc_name,
                    'cidr_block': vpc.cidr_block,
                    'status': vpc.status,
                    'creation_time': vpc.creation_time,
                    'tags': vpc.tags if hasattr(vpc, 'tags') else []
                }
                vpc_list.append(vpc_info)
            
            return vpc_list
            
        except ApiException as e:
            logger.error(f"获取VPC列表时发生异常: {e}")
            return []

    def list_subnets(self, vpc_id=None):
        """列出所有子网信息"""
        try:
            request = volcenginesdkvpc.DescribeSubnetsRequest()
            if vpc_id:
                request.vpc_id = vpc_id
            response = self.vpc_api.describe_subnets(request)
            
            if not hasattr(response, 'subnets'):
                logger.info("未找到任何子网")
                return []
            
            subnet_list = []
            for subnet in response.subnets:
                subnet_info = {
                    'subnet_id': subnet.subnet_id,
                    'subnet_name': subnet.subnet_name,
                    'vpc_id': subnet.vpc_id,
                    'cidr_block': subnet.cidr_block,
                    'zone_id': subnet.zone_id,
                    'status': subnet.status,
                    'creation_time': subnet.creation_time,
                    'tags': subnet.tags if hasattr(subnet, 'tags') else []
                }
                subnet_list.append(subnet_info)
            
            return subnet_list
            
        except ApiException as e:
            logger.error(f"获取子网列表时发生异常: {e}")
            return []

    def get_security_group_details(self, security_group_id):
        """获取安全组的详细属性信息，包括安全组规则"""
        try:
            request = volcenginesdkvpc.DescribeSecurityGroupAttributesRequest(
                security_group_id=security_group_id,
            )
            response = self.vpc_api.describe_security_group_attributes(request)
            
            if not hasattr(response, 'security_group_id'):
                logger.warning(f"未找到安全组 {security_group_id} 的详细信息")
                return None
            
            sg = response
            sg_details = {
                'security_group_id': sg.security_group_id,
                'security_group_name': sg.security_group_name,
                'vpc_id': sg.vpc_id,
                'description': sg.description if hasattr(sg, 'description') else '',
                'creation_time': sg.creation_time,
                'tags': sg.tags if hasattr(sg, 'tags') else [],
                'ingress_rules': [],
                'egress_rules': []
            }
            
            if hasattr(sg, 'permissions') and sg.permissions:
                for rule in sg.permissions:
                    rule_info = {
                        'policy': rule.policy,
                        'protocol': rule.protocol,
                        'port_range': '-1/-1' if rule.port_start == -1 and rule.port_end == -1 else f'{rule.port_start}/{rule.port_end}',
                        'cidr_ip': rule.cidr_ip if rule.cidr_ip else '',
                        'source_group_id': rule.source_group_id if hasattr(rule, 'source_group_id') and rule.source_group_id else '',
                        'prefix_list_cidrs': rule.prefix_list_cidrs if hasattr(rule, 'prefix_list_cidrs') and rule.prefix_list_cidrs else [],
                        'description': rule.description if hasattr(rule, 'description') else '',
                        'priority': rule.priority if hasattr(rule, 'priority') else 100
                    }
                    
                    if rule.direction == 'ingress':
                        sg_details['ingress_rules'].append(rule_info)
                    elif rule.direction == 'egress':
                        sg_details['egress_rules'].append(rule_info)
            
            return sg_details
            
        except ApiException as e:
            logger.error(f"获取安全组 {security_group_id} 详细信息时发生异常: {e}")
            return None

    def list_security_groups(self, vpc_id=None):
        """列出所有安全组信息"""
        try:
            request = volcenginesdkvpc.DescribeSecurityGroupsRequest()
            if vpc_id:
                request.vpc_id = vpc_id
            response = self.vpc_api.describe_security_groups(request)
            
            if not hasattr(response, 'security_groups'):
                logger.info("未找到任何安全组")
                return []
            
            sg_list = []
            for sg in response.security_groups:
                sg_info = {
                    'security_group_id': sg.security_group_id,
                    'security_group_name': sg.security_group_name,
                    'vpc_id': sg.vpc_id,
                    'description': sg.description if hasattr(sg, 'description') else '',
                    'creation_time': sg.creation_time,
                    'tags': sg.tags if hasattr(sg, 'tags') else []
                }
                # 获取安全组详细规则信息
                sg_details = self.get_security_group_details(sg.security_group_id)
                if sg_details:
                    sg_info['ingress_rules'] = sg_details['ingress_rules']
                    sg_info['egress_rules'] = sg_details['egress_rules']
                sg_list.append(sg_info)
            
            return sg_list
            
        except ApiException as e:
            logger.error(f"获取安全组列表时发生异常: {e}")
            return []

    def write_resources_to_file(self):
        """将所有资源信息写入文件"""
        resource_info_path = os.path.join(log_dir, 'network_resources_info.md')
        
        with open(resource_info_path, 'w', encoding='utf-8') as f:
            # 写入标题和时间戳
            f.write(f"# 网络资源信息记录\n\n")
            f.write(f"## 记录时间\n{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 获取并写入VPC信息
            vpcs = self.list_vpcs()
            f.write(f"## VPC信息\n")
            for vpc in vpcs:
                f.write(f"### VPC: {vpc['vpc_name']}\n")
                f.write(f"- VPC ID: {vpc['vpc_id']}\n")
                f.write(f"- CIDR: {vpc['cidr_block']}\n")
                f.write(f"- 状态: {vpc['status']}\n")
                f.write(f"- 创建时间: {vpc['creation_time']}\n")
                if vpc['tags']:
                    f.write("- 标签:\n")
                    for tag in vpc['tags']:
                        f.write(f"  - {tag.key}: {tag.value}\n")
                f.write("\n")
                
                # 获取并写入该VPC下的子网信息
                subnets = self.list_subnets(vpc['vpc_id'])
                if subnets:
                    f.write(f"#### 子网列表\n")
                    for subnet in subnets:
                        f.write(f"##### 子网: {subnet['subnet_name']}\n")
                        f.write(f"- 子网 ID: {subnet['subnet_id']}\n")
                        f.write(f"- CIDR: {subnet['cidr_block']}\n")
                        f.write(f"- 可用区: {subnet['zone_id']}\n")
                        f.write(f"- 状态: {subnet['status']}\n")
                        f.write(f"- 创建时间: {subnet['creation_time']}\n")
                        if subnet['tags']:
                            f.write("- 标签:\n")
                            for tag in subnet['tags']:
                                f.write(f"  - {tag.key}: {tag.value}\n")
                        f.write("\n")
                
                # 获取并写入该VPC下的安全组信息
                security_groups = self.list_security_groups(vpc['vpc_id'])
                if security_groups:
                    f.write(f"#### 安全组列表\n")
                    for sg in security_groups:
                        f.write(f"##### 安全组: {sg['security_group_name']}\n")
                        f.write(f"- 安全组 ID: {sg['security_group_id']}\n")
                        f.write(f"- 描述: {sg['description']}\n")
                        f.write(f"- 创建时间: {sg['creation_time']}\n")
                        if sg['tags']:
                            f.write("- 标签:\n")
                            for tag in sg['tags']:
                                f.write(f"  - {tag.key}: {tag.value}\n")
                        
                        # 写入安全组规则信息
                        if 'ingress_rules' in sg and sg['ingress_rules']:
                            f.write("- 入站规则:\n")
                            for rule in sg['ingress_rules']:
                                f.write(f"  - 协议: {rule['protocol']}\n")
                                if rule['port_range'] == '-1/-1':
                                    f.write(f"    端口范围: 全部\n")
                                else:
                                    f.write(f"    端口范围: {rule['port_range']}\n")
                                if rule['cidr_ip']:
                                    f.write(f"    源IP: {rule['cidr_ip']}\n")
                                if rule['source_group_id']:
                                    f.write(f"    源安全组: {rule['source_group_id']}\n")
                                if rule['prefix_list_cidrs']:
                                    f.write(f"    前缀列表: {', '.join(rule['prefix_list_cidrs'])}\n")
                                f.write(f"    策略: {rule['policy']}\n")
                                f.write(f"    优先级: {rule['priority']}\n")
                                if rule['description']:
                                    f.write(f"    描述: {rule['description']}\n")
                        
                        if 'egress_rules' in sg and sg['egress_rules']:
                            f.write("- 出站规则:\n")
                            for rule in sg['egress_rules']:
                                f.write(f"  - 协议: {rule['protocol']}\n")
                                if rule['port_range'] == '-1/-1':
                                    f.write(f"    端口范围: 全部\n")
                                else:
                                    f.write(f"    端口范围: {rule['port_range']}\n")
                                if rule['cidr_ip']:
                                    f.write(f"    目标IP: {rule['cidr_ip']}\n")
                                if rule['source_group_id']:
                                    f.write(f"    目标安全组: {rule['source_group_id']}\n")
                                if rule['prefix_list_cidrs']:
                                    f.write(f"    前缀列表: {', '.join(rule['prefix_list_cidrs'])}\n")
                                f.write(f"    策略: {rule['policy']}\n")
                                f.write(f"    优先级: {rule['priority']}\n")
                                if rule['description']:
                                    f.write(f"    描述: {rule['description']}\n")
                        f.write("\n")
                
            f.write("---\n\n")
            
        logger.info(f"网络资源信息已写入文件: {resource_info_path}")

def main():
    try:
        manager = NetworkResourceManager()
        manager.write_resources_to_file()
        logger.info("成功完成所有网络资源信息的收集和记录")
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()