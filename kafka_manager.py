import time
import logging
from volcenginesdkcore import Configuration
from volcenginesdkcore.rest import ApiException
import volcenginesdkkafka
import volcenginesdkvpc
from configs.api_config import api_config
from configs.kafka_configs import instance_configs
from vpc_manager import VPCManager
from whitelist_manager import KafkaWhitelistManager


# 配置日志
import os

# 确保logs目录存在
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(log_dir, 'kafka_manager.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class KafkaManager:
    def __init__(self):
        self._init_client()
        self.api = volcenginesdkkafka
        self.client_api = self.api.KAFKAApi()
        self.vpc_api = volcenginesdkvpc.VPCApi()
        self.vpc_manager = VPCManager()
        self.whitelist_manager = KafkaWhitelistManager()
        self.current_config = None

    def _init_client(self):
        configuration = Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        Configuration.set_default(configuration)

    def create_instance(self, instance_config, vpc_id=None, subnet_id=None):
        """
        创建Kafka实例
        :param instance_config: Kafka实例配置
        :param vpc_id: VPC ID
        :param subnet_id: 子网ID
        :return: 实例ID或None（如果创建失败）
        """
        self.current_config = instance_config
        try:
            # 检查是否已存在同名实例
            api_instance = volcenginesdkkafka.KAFKAApi()
            list_request = self.api.DescribeInstancesRequest(
                page_number=1,
                page_size=100,
            )

            list_response = self.client_api.describe_instances(list_request)
            
            # print(list_response)
            
            for instance in list_response.instances_info:
                if instance.instance_name == instance_config['instance']['name']:
                    logger.info(f"实例已存在，实例ID: {instance.instance_id}")
                    return instance.instance_id

            # 检查网络参数
            if not vpc_id or not subnet_id:
                logger.error("创建Kafka实例需要提供有效的VPC ID和子网ID")
                return None

            # 创建计费信息对象
            req_charge_info = self.api.ChargeInfoForCreateInstanceInput(
                auto_renew=instance_config['instance']['charge_info']['auto_renew'],
                charge_type=instance_config['instance']['charge_info']['charge_type'],
                period=instance_config['instance']['charge_info']['period'],
                period_unit=instance_config['instance']['charge_info']['period_unit']
            )

            # 创建新实例
            request = self.api.CreateInstanceRequest(
                instance_name=instance_config['instance']['name'],
                charge_info=req_charge_info,
                compute_spec=instance_config['instance']['compute_spec'],
                vpc_id=vpc_id,
                subnet_id=subnet_id,
                zone_id=instance_config['instance']['zone_id'],
                storage_space=instance_config['instance']['storage_size'],
                partition_number=instance_config['instance']['partition_num'],
                storage_type=instance_config['instance']['storage_type'],
                version=instance_config['instance']['version'],
                project_name=instance_config['instance'].get('project_name', 'default'),
                instance_description=instance_config['instance'].get('description', ''),
                parameters=instance_config['instance'].get('parameters', '{}')
            )
            
            response = self.client_api.create_instance(request)
            logger.info(f"Kafka实例创建成功: {response}")
            return response.instance_id
            
        except ApiException as e:
            logger.error(f"创建Kafka实例时发生异常: {e}")
            return None

    def wait_for_instance_ready(self, instance_id, timeout=1800, interval=30):
        """
        等待实例准备就绪
        :param instance_id: Kafka实例ID
        :param timeout: 超时时间（秒）
        :param interval: 检查间隔（秒）
        :return: bool 是否成功
        """
        start_time = time.time()
        while True:
            try:
                request = self.api.DescribeInstanceDetailRequest(instance_id=instance_id)
                response = self.client_api.describe_instance_detail(request)
                # print(response)
                if response.basic_instance_info.instance_status == "Running":
                    logger.info("实例已准备就绪")
                    return True
                logger.info(f"实例状态: {response.basic_instance_info.instance_status}")
                
                if time.time() - start_time > timeout:
                    logger.error("等待实例就绪超时")
                    return False
                    
                time.sleep(interval)
                
            except ApiException as e:
                if "OperationDenied.InvalidInstanceStatus" in str(e):
                    logger.info("实例状态暂时不可用，等待后重试...")
                    time.sleep(interval)
                    continue
                logger.error(f"检查实例状态时发生错误: {e}")
                return False

    def create_whitelist(self, instance_id):
        """
        为Kafka实例创建并绑定白名单
        :param instance_id: Kafka实例ID
        :return: bool 是否成功
        """
        try:
            # 使用白名单管理器绑定白名单
            success = self.whitelist_manager.bind_whitelists_to_instance(instance_id)
            return success
            
        except Exception as e:
            logger.error(f"创建或绑定白名单时发生异常: {e}")
            return False

    def create_acl(self, instance_id):
        """
        为Kafka实例创建ACL策略
        :param instance_id: Kafka实例ID
        :return: bool 是否成功
        """
        try:
            # 检查实例是否已准备就绪
            if not self.wait_for_instance_ready(instance_id):
                logger.error("实例未就绪，无法创建ACL策略")
                return False

            # 遍历配置中的所有ACL策略
            for acl_config in self.current_config['acls']:
                # 创建ACL策略
                request = self.api.CreateAclRequest(
                    instance_id=instance_id,
                    user_name=acl_config['username'],
                    access_policy=acl_config['permission'],
                    resource_type=acl_config['resource_type'],
                    resource=acl_config['resource_name'],
                    pattern_type=acl_config['pattern_type'],
                    ip=acl_config['host']
                )
                
                self.client_api.create_acl(request)
                logger.info(f"ACL策略创建成功: {acl_config['resource_name']}")
            
            return True
            
        except ApiException as e:
            logger.error(f"创建ACL策略时发生异常: {e}")
            return False

    def allocate_eip(self):
        """
        为Kafka实例分配EIP
        :return: (eip_id, eip_address, eip_name) 元组
        """
        from eip_manager import EIPManager
        eip_manager = EIPManager()
        return eip_manager.allocate_eip(self.current_config['eip'])

    def create_public_endpoint(self, instance_id, eip_id):
        """
        为Kafka实例创建公网访问端点
        :param instance_id: Kafka实例ID
        :param eip_id: EIP ID
        :return: bool 是否成功
        """
        try:
            # 创建公网访问端点
            request = self.api.CreatePublicNetworkRequest(
                instance_id=instance_id,
                eip_id=eip_id
            )
            
            self.client_api.create_public_network(request)
            logger.info("正在创建公网访问端点...")
            
            # 等待公网访问端点创建完成
            max_retries = 10
            retry_interval = 30
            for retry in range(max_retries):
                detail_request = self.api.GetInstanceDetailRequest(instance_id=instance_id)
                detail_response = self.client_api.get_instance_detail(detail_request)
                
                if hasattr(detail_response, 'public_endpoint') and detail_response.public_endpoint:
                    logger.info(f"公网访问端点创建成功: {detail_response.public_endpoint}")
                    return True
                
                if retry < max_retries - 1:
                    logger.info(f"等待{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                else:
                    logger.error("等待公网访问端点创建超时")
                    return False
            
            return False
            
        except ApiException as e:
            logger.error(f"创建公网访问端点时发生异常: {e}")
            return False

def main():
    kafka_manager = KafkaManager()
    vpc_manager = VPCManager()

    # 遍历所有Kafka实例配置
    for instance_config in instance_configs:
        logger.info(f"\n开始创建实例: {instance_config['instance']['name']}")

        # 1. 检查配置中是否已指定VPC和子网
        if 'vpc_id' in instance_config['instance'] and 'subnet_id' in instance_config['instance']:
            vpc_id = instance_config['instance']['vpc_id']
            subnet_id = instance_config['instance']['subnet_id']
            logger.info(f"使用配置中指定的VPC ID: {vpc_id} 和子网 ID: {subnet_id}")
        else:
            # 创建VPC
            vpc_id = vpc_manager.create_vpc(
                vpc_name=instance_config['instance']['vpc']['name'],
                cidr_block=instance_config['instance']['vpc']['cidr_block'],
                description=instance_config['instance']['vpc']['description'],
                tags=instance_config['instance']['vpc']['tags']
            )
            if not vpc_id:
                logger.error("创建VPC失败")
                continue

            # 等待VPC就绪
            if not vpc_manager.wait_for_vpc_available(vpc_id):
                logger.error("VPC创建超时或失败")
                continue

            # 创建实例专用子网
            subnet_config = instance_config['instance']['subnet']
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

            logger.info(f"子网 {subnet_config['name']} 创建成功，ID: {subnet_id}")

        # 2. 创建Kafka实例
        instance_id = kafka_manager.create_instance(instance_config, vpc_id, subnet_id)
        if not instance_id:
            logger.error("创建Kafka实例失败")
            continue

        # 等待实例创建完成
        logger.info("等待实例创建完成...")
        if not kafka_manager.wait_for_instance_ready(instance_id):
            logger.error("实例创建超时或失败")
            continue

        # 3. 申请EIP
        # eip_id, eip_address, eip_name = kafka_manager.allocate_eip()
        # if not eip_id:
        #     logger.error("申请EIP失败")
        #     continue

        # 4. 创建公网访问端点
        # if not kafka_manager.create_public_endpoint(instance_id, eip_id):
        #     logger.error("创建公网访问端点失败")
        #     continue

        # 5. 创建白名单
        if not kafka_manager.create_whitelist(instance_id):
            logger.error("创建白名单失败")
            continue

        # 6. 创建ACL策略
        if not kafka_manager.create_acl(instance_id):
            logger.error("创建ACL策略失败")
            continue

        logger.info(f"Kafka实例 {instance_config['instance']['name']} 创建完成！")

if __name__ == "__main__":
    main()