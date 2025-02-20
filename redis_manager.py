import time
import logging
from volcenginesdkcore import Configuration
from volcenginesdkcore.rest import ApiException
import volcenginesdkredis
import volcenginesdkvpc
from configs.api_config import api_config
from configs.redis_config import redis_configs
from vpc_manager import VPCManager
from whitelist_manager import RedisWhitelistManager


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
file_handler = logging.FileHandler(os.path.join(log_dir, 'redis_manager.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class RedisManager:
    def __init__(self):
        self._init_client()
        self.api = volcenginesdkredis
        self.client_api = self.api.REDISApi()
        self.vpc_api = volcenginesdkvpc.VPCApi()
        self.vpc_manager = VPCManager()
        self.whitelist_manager = RedisWhitelistManager()
        self.current_config = None
        self.status_checker = None  # 实例状态检查器，由子类初始化

    def _init_client(self):
        configuration = Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        Configuration.set_default(configuration)

    def create_redis_instance(self, redis_config, vpc_id=None, subnet_id=None):
        self.current_config = redis_config
        try:
        #    检查是否已存在同名实例
            list_request = self.api.DescribeDBInstancesRequest()
            list_response = self.client_api.describe_db_instances(list_request)

            for instance in list_response.instances:
                if instance.instance_name == redis_config['instance']['name']:
                    logger.info(f"实例已存在，实例ID: {instance.instance_id}")
                    return instance.instance_id

            # 检查网络参数
            if not vpc_id or not subnet_id:
                logger.error("创建Redis实例需要提供有效的VPC ID和子网ID")
                return None

            # 创建新实例
            # 配置节点信息
            req_configure_nodes = []
            for node_config in redis_config['instance']['configure_nodes']:
                node = self.api.ConfigureNodeForCreateDBInstanceInput(
                    az=node_config['az']
                )
                req_configure_nodes.append(node)

            request = self.api.CreateDBInstanceRequest(
                configure_nodes=req_configure_nodes,
                instance_name=redis_config['instance']['name'],
                engine_version=redis_config['instance']['engine_version'],
                node_number=redis_config['instance']['node_number'],
                shard_capacity=redis_config['instance']['shard_capacity'],
                vpc_id=vpc_id,
                subnet_id=subnet_id,
                multi_az=redis_config['instance']['multi_az'],
                region_id=redis_config['instance']['region_id'],
                project_name=redis_config['instance']['project_name'],
                auto_renew=redis_config['instance']['charge_info']['auto_renew'],
                charge_type=redis_config['instance']['charge_info']['charge_type'],
                purchase_months=redis_config['instance']['charge_info']['period'],
                port=redis_config['instance']['port'],
                password=redis_config['instance']['password'],
                sharded_cluster=redis_config['instance']['sharded_cluster']
            )
            
            response = self.client_api.create_db_instance(request)
            logger.info(f"Redis实例创建成功: {response}")
            return response.instance_id
            
        except ApiException as e:
            logger.error(f"创建Redis实例时发生异常: {e}")
            return None

    def wait_for_instance_ready(self, instance_id, timeout=1800, interval=30):
        start_time = time.time()
        while True:
            try:
                # 查询实例状态
                status_request = self.api.DescribeDBInstancesRequest()
                status_response = self.client_api.describe_db_instances(status_request)
                
                instance_status = None
                for instance in status_response.instances:
                    if instance.instance_id == instance_id:
                        instance_status = instance.status
                        break
                
                if instance_status == "Running":
                    logger.info(f"实例 {instance_id} 已就绪")
                    return True
                    
                logger.info(f"实例 {instance_id} 当前状态: {instance_status}，等待 {interval} 秒后重试...")
                
                if time.time() - start_time > timeout:
                    logger.error(f"等待实例 {instance_id} 状态超时，已等待 {timeout} 秒")
                    return False
                    
                time.sleep(interval)
                
            except ApiException as e:
                logger.error(f"检查实例 {instance_id} 状态时发生错误: {e}")
                return False

    def create_whitelist(self, instance_id):
        try:
            # 使用白名单绑定管理器
            success = self.whitelist_manager.bind_whitelists_to_instance(instance_id)
            return success
            
        except Exception as e:
            print(f"创建或绑定白名单时发生异常: {e}")
            return False

    def delete_whitelist(self, instance_id):
        try:
            # 使用白名单绑定管理器
            success = self.whitelist_manager.unbind_whitelists_from_instance(instance_id)
            return success
            
        except Exception as e:
            print(f"创建或绑定白名单时发生异常: {e}")
            return False


    def allocate_eip(self):
        from eip_manager import EIPManager
        eip_manager = EIPManager()
        return eip_manager.allocate_eip(self.current_config['eip'])

    def create_public_endpoint(self, instance_id, eip_id):
        try:
            # 检查是否已存在公网访问端点
            describe_request = self.api.DescribeDBInstanceDetailRequest(
                instance_id=instance_id
            )
            describe_response = self.client_api.describe_db_instance_detail(describe_request)
            
            # 检查实例的visit_addrs中是否已有公网连接点
            if hasattr(describe_response, 'visit_addrs'):
                for addr in describe_response.visit_addrs:
                    if addr.addr_type == 'Public':
                        logger.info(f"公网访问端点已存在:")
                        logger.info(f"  - 域名: {addr.address}")
                        logger.info(f"  - 端口: {addr.port}")
                        return addr.address, addr.port

            # 创建新的公网访问端点
            request = self.api.CreateDBEndpointPublicAddressRequest(
                instance_id=instance_id,
                eip_id=eip_id
            )
            
            response = self.client_api.create_db_endpoint_public_address(request)
            logger.info("正在创建公网访问地址...")
            
            # 等待公网访问端点创建完成
            max_retries = 10
            retry_interval = 30
            for retry in range(max_retries):
                describe_request = self.api.DescribeDBInstanceDetailRequest(
                    instance_id=instance_id
                )
                describe_response = self.client_api.describe_db_instance_detail(describe_request)
                
                if hasattr(describe_response, 'visit_addrs'):
                    for addr in describe_response.visit_addrs:
                        if addr.addr_type == 'Public':
                            logger.info(f"公网访问端点创建成功:")
                            logger.info(f"  - 域名: {addr.address}")
                            logger.info(f"  - 端口: {addr.port}")
                            return addr.address, addr.port
                
                if retry < max_retries - 1:
                    logger.info(f"等待{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                else:
                    logger.error("等待公网访问端点创建超时")
                    return None, None
            
            return None, None
            
        except ApiException as e:
            logger.error(f"创建公网访问地址时发生异常: {e}")
            return None, None

    def get_private_endpoint(self, instance_id):
        try:
            # 查询实例详情获取内网访问信息
            describe_request = self.api.DescribeDBInstanceDetailRequest(
                instance_id=instance_id
            )
            describe_response = self.client_api.describe_db_instance_detail(describe_request)
            
            # 检查实例的visit_addrs中是否有内网连接点
            if hasattr(describe_response, 'visit_addrs'):
                for addr in describe_response.visit_addrs:
                    if addr.addr_type == 'Private':
                        logger.info(f"内网访问端点信息:")
                        logger.info(f"  - 域名: {addr.address}")
                        logger.info(f"  - 端口: {addr.port}")
                        logger.info(f"  - 完整连接地址: {addr.address}:{addr.port}")
                        return addr.address, addr.port
            
            logger.info("未找到内网访问端点信息")
            return None, None
            
        except ApiException as e:
            logger.error(f"获取内网访问信息时发生异常: {e}")
            return None, None

    def modify_instance_params(self, instance_id, param_name, param_value):
        """修改Redis实例的参数配置

        Args:
            instance_id (str): Redis实例ID
            param_name (str): 参数名称
            param_value (str): 参数值

        Returns:
            bool: 修改是否成功
        """
        max_retries = 5
        retry_interval = 30
        
        for retry in range(max_retries):
            try:
                # 检查实例状态
                status_request = self.api.DescribeDBInstancesRequest()
                status_response = self.client_api.describe_db_instances(status_request)
                
                instance_status = None
                for instance in status_response.instances:
                    if instance.instance_id == instance_id:
                        instance_status = instance.status
                        break
                
                if instance_status == "Running":
                    req_param_values = self.api.ParamValueForModifyDBInstanceParamsInput(
                        name=param_name,
                        value=param_value
                    )
                    modify_request = self.api.ModifyDBInstanceParamsRequest(
                        instance_id=instance_id,
                        param_values=[req_param_values]
                    )
                    
                    self.client_api.modify_db_instance_params(modify_request)
                    logger.info(f"成功修改Redis实例 {instance_id} 的参数配置: {param_name}={param_value}")
                    return True
                else:
                    logger.info(f"实例状态为 {instance_status}，等待{retry_interval}秒后重试...")
                    if retry < max_retries - 1:
                        time.sleep(retry_interval)
                    else:
                        logger.error(f"等待实例状态就绪超时，无法修改参数")
                        return False
                    
            except ApiException as e:
                logger.error(f"修改Redis实例参数时发生异常: {e}")
                if retry < max_retries - 1:
                    logger.info(f"等待{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                else:
                    return False
        
        return False

def main():
    redis_manager = RedisManager()
    vpc_manager = VPCManager()
    subnet_id = None

    # 遍历所有Redis实例配置
    for redis_config in redis_configs:
        logger.info(f"\n开始创建实例: {redis_config['instance']['name']}")

        # 1. 检查配置中是否已指定VPC和子网
        if 'vpc_id' in redis_config['instance'] and 'subnet_id' in redis_config['instance']:
            vpc_id = redis_config['instance']['vpc_id']
            subnet_id = redis_config['instance']['subnet_id']
            logger.info(f"使用配置中指定的VPC ID: {vpc_id} 和子网 ID: {subnet_id}")
            instance_subnet_id = subnet_id
        else:
            # 创建VPC
            vpc_id = vpc_manager.create_vpc(
                vpc_name=redis_config['instance']['vpc']['name'],
                cidr_block=redis_config['instance']['vpc']['cidr_block'],
                description=redis_config['instance']['vpc']['description'],
                tags=redis_config['instance']['vpc']['tags']
            )
            if not vpc_id:
                logger.error("创建VPC失败")
                continue

            # 等待VPC就绪
            if not vpc_manager.wait_for_vpc_available(vpc_id):
                logger.error("VPC创建超时或失败")
                continue

            # 创建实例专用子网
            subnet_config = redis_config['instance']['subnet']
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
            instance_subnet_id = subnet_id

        if not instance_subnet_id:
            logger.error("在实例指定可用区未找到或创建子网失败")
            continue

        # 3. 创建Redis实例
        instance_id = redis_manager.create_redis_instance(redis_config, vpc_id, subnet_id)
        if not instance_id:
            logger.error("创建Redis实例失败")
            continue

        # 等待实例创建完成
        logger.info("等待实例创建完成...")
        if not redis_manager.wait_for_instance_ready(instance_id):
            logger.error("实例创建超时或失败")
            continue

        # 4. 申请EIP
        eip_id, eip_address, eip_name = redis_manager.allocate_eip()
        if not eip_id:
            logger.error("申请EIP失败")
            continue

        # 5. 创建公网访问端点
        address_domain, address_port = redis_manager.create_public_endpoint(instance_id, eip_id)
        if not address_domain:
            logger.error("创建公网访问端点失败")
            continue
        # 5.1 获取内网访问端点
        private_address_domain, private_address_port = redis_manager.get_private_endpoint(instance_id)
        if not address_domain:
            logger.error("获取内网访问端点失败")
            continue

        # 6. 创建白名单
        if not redis_manager.create_whitelist(instance_id):
            logger.error("创建白名单失败")
            continue

        # if not redis_manager.delete_whitelist(instance_id):
        #     logger.error("删除白名单失败")
        #     continue

        # 7. 修改实例参数配置
        if not redis_manager.modify_instance_params(instance_id,param_name="disabled-commands",param_value="flushall,flushdb"):
            logger.error("修改实例参数配置失败")
            continue

        # 记录实例创建成功的信息
        logger.info(f"\n成功完成实例 {redis_config['instance']['name']} 的所有操作！")
        logger.info(f"Redis实例ID: {instance_id}")
        logger.info(f"VPC ID: {vpc_id}")
        logger.info(f"子网 ID: {subnet_id}")
        logger.info(f"EIP地址: {eip_address}")
        logger.info(f"公网访问: {address_domain}:{address_port}")
        logger.info(f"内网访问: {private_address_domain}:{private_address_port}")

        # 将实例信息写入Markdown文件
        redis_instance_info_path = os.path.join(log_dir, 'redis_instance_info.md')
        with open(redis_instance_info_path, 'a', encoding='utf-8') as f:
            # 添加分隔符和时间戳
            f.write(f"\n{'='*50}\n")
            f.write(f"记录时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"# Redis实例创建记录\n\n")
            f.write(f"## 实例信息\n")
            f.write(f"- 实例ID: {instance_id}\n")
            f.write(f"- 实例名称: {redis_config['instance']['name']}\n")
            f.write(f"- 查询时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- Redis版本: {redis_config['instance']['engine_version']}\n")
            f.write(f"- 节点数量: {redis_config['instance']['node_number']}\n")
            f.write(f"- 分片容量: {redis_config['instance']['shard_capacity']}MB\n\n")

            f.write(f"## 网络配置\n")
            f.write(f"- VPC ID: {vpc_id}\n")
            f.write(f"- 子网 ID: {subnet_id}\n")
            f.write(f"- EIP名称: {redis_config['eip']}\n")
            f.write(f"- EIP地址: {eip_address}\n")
            f.write(f"- 内网访问域名: {private_address_domain}\n")
            f.write(f"- 内网访问端口: {private_address_port}\n")
            f.write(f"- 公网访问域名: {address_domain}\n")
            f.write(f"- 公网访问端口: {address_port}\n\n")

            f.write(f"## 账号信息\n")
            for account in redis_config['accounts']:
                f.write(f"- 账号类型: {account['account_type']}\n")
                f.write(f"- 用户名: {account['username']}\n")
                f.write(f"- 密码: {account['password']}\n\n")

            f.write(f"## 备份策略\n")
            f.write(f"- 备份保留天数: {redis_config['backup']['retention_period']}天\n")
            f.write(f"- 备份时间段: {redis_config['backup']['backup_time']}\n")
            f.write(f"- 备份周期: {', '.join(redis_config['backup']['backup_period'])}\n\n")

if __name__ == "__main__":
    main()