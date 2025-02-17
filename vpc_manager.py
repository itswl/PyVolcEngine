from __future__ import print_function
import volcenginesdkcore
import volcenginesdkvpc
from volcenginesdkcore.rest import ApiException
import time
import logging

from configs.api_config import api_config   
from configs.network_config import network_config
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
file_handler = logging.FileHandler(os.path.join(log_dir, 'vpc_manager.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


class VPCManager:
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

    def create_vpc(self, vpc_name, cidr_block, description=None, project_name=None, tags=None):
        try:
            # 先列出所有VPC
            list_request = volcenginesdkvpc.DescribeVpcsRequest()
            list_response = self.vpc_api.describe_vpcs(list_request)
            
            # 检查是否已存在同名VPC
            if hasattr(list_response, 'vpcs'):
                for vpc in list_response.vpcs:
                    if vpc.vpc_name == vpc_name:
                        logger.info(f"VPC {vpc_name} 已存在，VPC ID: {vpc.vpc_id}")
                        return vpc.vpc_id

            # 创建VPC请求
            request = volcenginesdkvpc.CreateVpcRequest(
                vpc_name=vpc_name,
                cidr_block=cidr_block
            )

            # 添加可选参数
            if description:
                request.description = description
            if project_name:
                request.project_name = project_name
            if tags:
                request.tags = tags

            # 发送创建请求
            response = self.vpc_api.create_vpc(request)
            vpc_id = response.vpc_id
            logger.info(f"VPC创建成功，VPC ID: {vpc_id}")
            return vpc_id

        except ApiException as e:
            logger.error(f"创建VPC时发生异常: {e}")
            return None

    def create_subnet(self, vpc_id, subnet_name, cidr_block, zone_id, description=None, tags=None):
        try:
            # 先检查VPC状态
            request = volcenginesdkvpc.DescribeVpcsRequest()
            response = self.vpc_api.describe_vpcs(request)
            vpc_available = False
            
            for vpc in response.vpcs:
                if vpc.vpc_id == vpc_id:
                    if vpc.status == "Available":
                        vpc_available = True
                    else:
                        logger.info(f"VPC {vpc_id} 当前状态为 {vpc.status}，等待其变为可用状态")
                        if not self.wait_for_vpc_available(vpc_id):
                            return None
                        vpc_available = True
                    break
            
            if not vpc_available:
                logger.error(f"未找到VPC {vpc_id} 或VPC状态不正确")
                return None

            # 先列出所有子网
            list_request = volcenginesdkvpc.DescribeSubnetsRequest(
                vpc_id=vpc_id
            )
            list_response = self.vpc_api.describe_subnets(list_request)
            
            # 检查是否已存在同名子网
            if list_response and hasattr(list_response, 'subnets') and list_response.subnets:
                for subnet in list_response.subnets:
                    if subnet.subnet_name == subnet_name:
                        logger.info(f"子网 {subnet_name} 已存在，子网ID: {subnet.subnet_id}")
                        return subnet.subnet_id

            # 创建子网请求
            request = volcenginesdkvpc.CreateSubnetRequest(
                vpc_id=vpc_id,
                subnet_name=subnet_name,
                cidr_block=cidr_block,
                zone_id=zone_id
            )

            # 添加可选参数
            if description:
                request.description = description
            if tags:
                request.tags = tags

            # 发送创建请求
            response = self.vpc_api.create_subnet(request)
            subnet_id = response.subnet_id
            logger.info(f"子网创建成功，子网ID: {subnet_id}")
            return subnet_id

        except ApiException as e:
            logger.error(f"创建子网时发生异常: {e}")
            return None

    def wait_for_vpc_available(self, vpc_id, timeout=300, interval=10):
        """等待VPC变为可用状态"""
        start_time = time.time()
        while True:
            try:
                request = volcenginesdkvpc.DescribeVpcsRequest()
                response = self.vpc_api.describe_vpcs(request)
                
                for vpc in response.vpcs:
                    if vpc.vpc_id == vpc_id:
                        if vpc.status == "Available":
                            logger.info("VPC已准备就绪")
                            return True
                        logger.info(f"当前VPC状态: {vpc.status}")
                        break
                
                if time.time() - start_time > timeout:
                    logger.error("等待VPC就绪超时")
                    return False
                    
                time.sleep(interval)
                
            except ApiException as e:
                logger.error(f"检查VPC状态时发生错误: {e}")
                return False

    def wait_for_subnet_available(self, subnet_id, timeout=300, interval=10):
        """等待子网变为可用状态"""
        start_time = time.time()
        while True:
            try:
                request = volcenginesdkvpc.DescribeSubnetsRequest()
                response = self.vpc_api.describe_subnets(request)
                
                for subnet in response.subnets:
                    if subnet.subnet_id == subnet_id:
                        if subnet.status == "Available":
                            logger.info("子网已准备就绪")
                            return True
                        logger.info(f"当前子网状态: {subnet.status}")
                        break
                
                if time.time() - start_time > timeout:
                    logger.error("等待子网就绪超时")
                    return False
                    
                time.sleep(interval)
                
            except ApiException as e:
                logger.error(f"检查子网状态时发生错误: {e}")
                return False

def main():
    vpc_manager = VPCManager()

    # 创建VPC
    vpc_id = vpc_manager.create_vpc(
        vpc_name=network_config['vpc']['name'],
        cidr_block=network_config['vpc']['cidr_block'],
        description=network_config['vpc']['description'],
        tags=network_config['vpc']['tags']
    )

    if not vpc_id:
        logger.error("创建VPC失败")
        return

    # 等待VPC就绪
    if not vpc_manager.wait_for_vpc_available(vpc_id):
        logger.error("VPC创建超时或失败")
        return

    # 创建多个子网
    subnet_ids = []
    for subnet_config in network_config['subnets']:
        subnet_id = vpc_manager.create_subnet(
            vpc_id=vpc_id,
            subnet_name=subnet_config['name'],
            cidr_block=subnet_config['cidr_block'],
            zone_id=subnet_config['zone_id'],
            description=subnet_config.get('description'),
            tags=subnet_config.get('tags')
        )

        if not subnet_id:
            logger.error(f"创建子网 {subnet_config['name']} 失败")
            continue

        # 等待子网就绪
        if not vpc_manager.wait_for_subnet_available(subnet_id):
            logger.error(f"子网 {subnet_config['name']} 创建超时或失败")
            continue

        subnet_ids.append(subnet_id)
        logger.info(f"子网 {subnet_config['name']} 创建成功，ID: {subnet_id}")

    if not subnet_ids:
        logger.error("所有子网创建均失败")
        return

    # 将VPC和子网信息写入日志文件
    subnet_ids_info = ''
    for subnet_config, subnet_id in zip(network_config['subnets'], subnet_ids):
        subnet_ids_info += f"- 子网ID: {subnet_id}\n  可用区: {subnet_config['zone_id']}\n  名称: {subnet_config['name']}\n"

    vpc_resource_info_path = os.path.join(log_dir, 'vpc_resource_info.md')
    with open(vpc_resource_info_path, 'a', encoding='utf-8') as f:
        f.write(f"# VPC和子网资源记录\n\n")
        f.write(f"## 记录时间\n{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## VPC信息\n- VPC ID: {vpc_id}\n\n")
        f.write(f"## 子网信息\n{subnet_ids_info}\n")
        f.write("---\n\n")

    logger.info(f"成功完成所有操作！")
    logger.info(f"VPC ID: {vpc_id}")
    logger.info(f"成功创建的子网 IDs: {subnet_ids}")

if __name__ == "__main__":
    main()