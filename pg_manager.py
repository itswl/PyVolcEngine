from __future__ import print_function
import volcenginesdkcore
import volcenginesdkrdspostgresql
import volcenginesdkvpc
from volcenginesdkcore.rest import ApiException
import time
import logging
from configs.api_config import api_config, timeout_config
from configs.pg_config import pg_configs
from configs.network_config import network_config
from whitelist_manager import WhitelistManager
from vpc_manager import VPCManager
from whitelist_binding_manager import WhitelistBindingManager


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
file_handler = logging.FileHandler(os.path.join(log_dir, 'pg_manager.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class PostgreSQLManager:
    def __init__(self):
        self._init_client()
        self.api = volcenginesdkrdspostgresql
        self.client_api = self.api.RDSPOSTGRESQLApi()
        self.vpc_api = volcenginesdkvpc.VPCApi()
        self.vpc_manager = VPCManager()
        self.current_config = None  # 当前正在处理的配置

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)

    def create_pg_instance(self, pg_config, vpc_id=None, subnet_id=None):
        self.current_config = pg_config  # 设置当前配置
        try:
            # 先列出所有实例
            list_request = self.api.DescribeDBInstancesRequest()
            list_response = self.client_api.describe_db_instances(list_request)
            
            # 检查是否已存在名为配置中指定的实例
            for instance in list_response.instances:
                if instance.instance_name == pg_config['instance']['name']:
                    print("实例已存在，实例ID: %s" % instance.instance_id)
                    return instance.instance_id

            # 检查是否提供了必要的网络参数
            if not vpc_id or not subnet_id:
                logger.error("创建PostgreSQL实例需要提供有效的VPC ID和子网ID")
                return None

            # 如果不存在，则创建新实例
            request = self.api.CreateDBInstanceRequest(
                instance_name=pg_config['instance']['name'],
                db_engine_version=pg_config['instance']['engine_version'],
                storage_type=pg_config['instance']['storage_type'],
                storage_space=pg_config['instance']['storage_space'],
                vpc_id=vpc_id,
                subnet_id=subnet_id,
                node_info=[
                    {
                        "NodeType": "Primary",
                        "NodeSpec": pg_config['instance']['node_spec'],
                        "ZoneId": pg_config['instance']['zone_id']
                    },
                    {
                        "NodeType": "Secondary",
                        "NodeSpec": pg_config['instance']['node_spec'],
                        "ZoneId": pg_config['instance']['zone_id']
                    }
                ],
                charge_info={                       
                    "ChargeType": pg_config['instance']['charge_info']['charge_type'],
                    "PeriodUnit": pg_config['instance']['charge_info']['period_unit'],
                    "Period": pg_config['instance']['charge_info']['period'],
                    "AutoRenew": pg_config['instance']['charge_info']['auto_renew']
                }
            )
            
            response = self.client_api.create_db_instance(request)
            print("PostgreSQL实例创建成功: %s" % response)
            return response.instance_id
            
        except ApiException as e:
            print("操作PostgreSQL实例时发生异常: %s\n" % e)
            return None

    def allocate_eip(self):
        from eip_manager import EIPManager
        eip_manager = EIPManager()
        return eip_manager.allocate_eip(self.current_config['eip'])

    def get_private_endpoint(self, instance_id):
        try:
            # 查询实例详情获取内网访问信息
            describe_request = self.api.DescribeDBInstanceDetailRequest(
                instance_id=instance_id
            )
            describe_response = self.client_api.describe_db_instance_detail(describe_request)
            
            # 遍历endpoints查找内网连接点
            if hasattr(describe_response, 'endpoints'):
                for endpoint in describe_response.endpoints:
                    for address in endpoint.address:
                        if address.network_type == 'Private':
                            print(f"内网访问端点信息:")
                            print(f"  - 域名: {address.domain}")
                            print(f"  - IP地址: {address.ip_address}")
                            print(f"  - 端口: {address.port}")
                            print(f"  - 完整连接地址: {address.domain}:{address.port}")
                            return address.domain, address.port
            
            print("未找到内网访问端点信息")
            return None, None
            
        except ApiException as e:
            print("获取内网访问信息时发生异常: %s\n" % e)
            return None, None

    def create_public_endpoint(self, instance_id, eip_id):
        try:
            # 先检查是否已存在公网访问端点
            describe_request = self.api.DescribeDBInstanceDetailRequest(
                instance_id=instance_id
            )
            describe_response = self.client_api.describe_db_instance_detail(describe_request)
            
            # 检查实例的 endpoints 中是否已有公网连接点
            if hasattr(describe_response, 'endpoints'):
                for endpoint in describe_response.endpoints:
                    for address in endpoint.address:
                        if address.network_type == 'Public':
                            print(f"公网访问端点已存在:")
                            print(f"  - 域名: {address.domain}")
                            print(f"  - 端口: {address.port}")
                            print(f"  - 完整连接地址: {address.domain}:{address.port}")
                            return address.domain, address.port

            # 如果不存在，则创建新的公网访问端点
            request = self.api.CreateDBEndpointPublicAddressRequest(
                instance_id=instance_id,
                eip_id=eip_id
            )
            
            response = self.client_api.create_db_endpoint_public_address(request)
            print("正在创建公网访问地址...")
            
            # 等待公网访问端点创建完成
            max_retries = 10
            retry_interval = 30
            for retry in range(max_retries):
                describe_request = self.api.DescribeDBInstanceDetailRequest(
                    instance_id=instance_id
                )
                describe_response = self.client_api.describe_db_instance_detail(describe_request)
                
                if hasattr(describe_response, 'endpoints'):
                    for endpoint in describe_response.endpoints:
                        for address in endpoint.address:
                            if address.network_type == 'Public':
                                print(f"公网访问端点创建成功:")
                                print(f"  - 域名: {address.domain}")
                                print(f"  - 端口: {address.port}")
                                print(f"  - 完整连接地址: {address.domain}:{address.port}")
                                return address.domain, address.port
                                return True
                
                if retry < max_retries - 1:
                    print(f"等待{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                else:
                    print("等待公网访问端点创建超时")
                    return False
            
            return False
            
        except ApiException as e:
            print("创建公网访问地址时发生异常: %s\n" % e)
            return False

    def wait_for_instance_ready(self, instance_id, timeout=1800, interval=30):
        """
        等待实例准备就绪
        :param api_instance: API实例
        :param instance_id: 数据库实例ID
        :param timeout: 超时时间（秒）
        :param interval: 检查间隔（秒）
        :return: bool 是否成功
        """
        start_time = time.time()
        while True:
            try:
                request = self.api.DescribeDBInstancesRequest()
                response = self.client_api.describe_db_instances(request)
                
                for instance in response.instances:
                    if instance.instance_id == instance_id:
                        if instance.instance_status == "Running":
                            print("实例已准备就绪")
                            return True
                        print(f"实例状态: {instance.instance_status}")
                        break
                
                if time.time() - start_time > timeout:
                    print("等待实例就绪超时")
                    return False
                    
                time.sleep(interval)
                
            except ApiException as e:
                print(f"检查实例状态时发生错误: {e}")
                return False

    def create_whitelist(self, instance_id):
        try:
            # 使用白名单绑定管理器
            binding_manager = WhitelistBindingManager()
            success = binding_manager.bind_whitelists_to_instance(instance_id)
            return success
            
        except Exception as e:
            print(f"创建或绑定白名单时发生异常: {e}")
            return False

    def create_database(self, instance_id):
        try:
            # 先获取已存在的数据库列表
            describe_request = self.api.DescribeDatabasesRequest(
                instance_id=instance_id
            )
            describe_response = self.client_api.describe_databases(describe_request)
            existing_databases = []
            
            # 添加空值检查
            if hasattr(describe_response, 'databases') and describe_response.databases is not None:
                existing_databases = [db.db_name for db in describe_response.databases]
                logger.info(f"获取到现有数据库列表: {existing_databases}")
            else:
                logger.info("当前实例没有已存在的数据库")
            
            # 遍历配置中的所有数据库
            for db_config in self.current_config['databases']:
                if db_config['name'] in existing_databases:
                    logger.info(f"数据库 {db_config['name']} 已存在，无需重复创建")
                    continue
                
                # 创建数据库
                request = self.api.CreateDatabaseRequest(
                    instance_id=instance_id,
                    db_name=db_config['name'],
                    owner=db_config['owner']
                )
                self.client_api.create_database(request)
                logger.info(f"数据库 {db_config['name']} 创建成功")
            
            return True
        except ApiException as e:
            logger.error(f"创建数据库时发生异常: {e}")
            return False

    def create_account(self, instance_id):
        try:
            # 等待实例状态就绪
            max_retries = 10
            retry_interval = 30
            for retry in range(max_retries):
                describe_request = self.api.DescribeDBInstancesRequest()
                describe_response = self.client_api.describe_db_instances(describe_request)
                
                instance_ready = False
                for instance in describe_response.instances:
                    if instance.instance_id == instance_id:
                        print(f"当前实例状态: {instance.instance_status}")
                        if instance.instance_status == "Running":
                            instance_ready = True
                            break
                        elif instance.instance_status == "AllowListMaintaining":
                            print("实例正在进行白名单维护，等待...")
                            break
                
                if instance_ready:
                    break
                    
                if retry < max_retries - 1:
                    print(f"等待{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                else:
                    print("等待实例就绪超时，无法创建账号")
                    return False

            # 检查并创建所有账号
            list_request = self.api.DescribeDBAccountsRequest(
                instance_id=instance_id
            )
            list_response = self.client_api.describe_db_accounts(list_request)
            
            # 遍历配置中的所有账号
            for account_config in self.current_config['accounts']:
                account_exists = False
                
                # 检查账号是否已存在
                if hasattr(list_response, 'accounts'):
                    for account in list_response.accounts:
                        if account.account_name == account_config['username']:
                            print(f"账号 {account_config['username']} 已存在，无需重复创建")
                            account_exists = True
                            break
                
                if not account_exists:
                    # 创建新账号
                    request = self.api.CreateDBAccountRequest(
                        instance_id=instance_id,
                        account_name=account_config['username'],
                        account_password=account_config['password'],
                        account_type=account_config['account_type']
                    )
                    
                    self.client_api.create_db_account(request)
                    print(f"账号 {account_config['username']} 创建成功")
            
            return True
            
        except ApiException as e:
            print(f"创建账号时发生异常: {e}")
            return False

    def create_schema(self, instance_id):
        try:
            # 遍历配置中的所有数据库和Schema
            for db_config in self.current_config['databases']:
                print(f"\n数据库: {db_config['name']}")
                print("Schema列表:")
                
                # 获取当前数据库的Schema列表
                describe_request = self.api.DescribeSchemasRequest(
                    instance_id=instance_id,
                    db_name=db_config['name']
                )
                describe_response = self.client_api.describe_schemas(describe_request)
                
                # 获取现有的Schema列表
                existing_schemas = []
                if hasattr(describe_response, 'schemas'):
                    existing_schemas = [schema.schema_name for schema in describe_response.schemas]
                    for schema_name in existing_schemas:
                        print(f"  - {schema_name} (已存在)")
                
                # 遍历配置中的Schema
                for schema_config in db_config['schemas']:
                    if schema_config['name'] not in existing_schemas:
                        # 创建新Schema
                        request = self.api.CreateSchemaRequest(
                            instance_id=instance_id,
                            db_name=db_config['name'],
                            schema_name=schema_config['name'],
                            owner=schema_config['owner']
                        )
                        self.client_api.create_schema(request)
                        print(f"  - {schema_config['name']} (新创建)")

            return True
        except ApiException as e:
            print(f"创建Schema时发生异常: {e}")
            return False

    def modify_backup_policy(self, instance_id):
        try:
            request = self.api.ModifyBackupPolicyRequest(
                instance_id=instance_id,
                backup_retention_period=self.current_config['backup']['retention_period'],
                full_backup_period=self.current_config['backup']['full_backup_period'],
                full_backup_time=self.current_config['backup']['full_backup_time'],
                increment_backup_frequency=self.current_config['backup']['increment_backup_frequency']
            )
            
            self.client_api.modify_backup_policy(request)
            logger.info("备份策略修改成功")
            return True
            
        except ApiException as e:
            logger.error(f"修改备份策略时发生异常: {e}")
            return False

def main():
    pg_manager = PostgreSQLManager()
    vpc_manager = VPCManager()
    subnet_id = None  # 初始化subnet_id变量

    # 遍历所有PostgreSQL实例配置
    for pg_config in pg_configs:
        logger.info(f"\n开始创建实例: {pg_config['instance']['name']}")

        # 1. 检查配置中是否已指定VPC和子网
        if 'vpc_id' in pg_config['instance'] and 'subnet_id' in pg_config['instance']:
            vpc_id = pg_config['instance']['vpc_id']
            subnet_id = pg_config['instance']['subnet_id']
            logger.info(f"使用配置中指定的VPC ID: {vpc_id} 和子网 ID: {subnet_id}")
            instance_subnet_id = subnet_id
        else:
            # 创建VPC
            vpc_id = vpc_manager.create_vpc(
                vpc_name=pg_config['instance']['vpc']['name'],
                cidr_block=pg_config['instance']['vpc']['cidr_block'],
                description=pg_config['instance']['vpc']['description'],
                tags=pg_config['instance']['vpc']['tags']
            )
            if not vpc_id:
                logger.error("创建VPC失败")
                continue

            # 等待VPC就绪
            if not vpc_manager.wait_for_vpc_available(vpc_id):
                logger.error("VPC创建超时或失败")
                continue

            # 创建实例专用子网
            subnet_config = pg_config['instance']['subnet']
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

        # 3. 创建PostgreSQL实例
        instance_id = pg_manager.create_pg_instance(pg_config, vpc_id, subnet_id)
        if not instance_id:
            logger.error("创建PostgreSQL实例失败")
            continue

        # 等待实例创建完成
        logger.info("等待实例创建完成...")
        if not pg_manager.wait_for_instance_ready(instance_id):
            logger.error("实例创建超时或失败")
            continue

        # 4. 申请EIP
        eip_id, eip_address, eip_name = pg_manager.allocate_eip()
        if not eip_id:
            logger.error("申请EIP失败")
            continue

        # 5. 创建公网访问端点
        address_domain, address_port = pg_manager.create_public_endpoint(instance_id, eip_id)
        if not address_domain:
            logger.error("创建公网访问端点失败")
            continue
        # 5.1.  获取内网访问端点
        private_address_domain, private_address_port = pg_manager.get_private_endpoint(instance_id)
        if not address_domain:
            logger.error("创建公网访问端点失败")
            continue
        # 6. 创建白名单
        if not pg_manager.create_whitelist(instance_id):
            logger.error("创建白名单失败")
            continue

        # 7. 创建账号
        if not pg_manager.create_account(instance_id):
            logger.error("创建账号失败")
            continue

        # 8. 创建数据库
        if not pg_manager.create_database(instance_id):
            logger.error("创建数据库失败")
            continue

        # 9. 创建Schema
        if not pg_manager.create_schema(instance_id):
            logger.error("创建Schema失败")
            continue

        # 10. 修改备份策略
        if not pg_manager.modify_backup_policy(instance_id):
            logger.error("修改备份策略失败")
            continue

        logger.info(f"成功完成实例 {pg_config['instance']['name']} 的所有操作！")
        
        # 将实例信息写入日志文件，使用追加模式
        pg_instance_info_path = os.path.join(log_dir, 'pg_instance_info.md')
        with open(pg_instance_info_path, 'a', encoding='utf-8') as f:
            # 添加分隔符和时间戳
            f.write(f"\n{'='*50}\n")
            f.write(f"记录时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"# PostgreSQL实例创建记录\n\n")
            f.write(f"## 实例信息\n")
            f.write(f"- 实例ID: {instance_id}\n")
            f.write(f"- 实例名称: {pg_config['instance']['name']}\n")
            f.write(f"- 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"## 网络配置\n")
            f.write(f"- VPC ID: {vpc_id}\n")
            f.write(f"- 子网 ID: {subnet_id}\n")
            f.write(f"- EIP名称: {eip_name}\n")
            f.write(f"- EIP地址: {eip_address}\n")
            f.write(f"- EIP ID: {eip_id}\n")
            f.write(f"- 内网访问域名: {private_address_domain}\n")
            f.write(f"- 内网访问端口: {private_address_port}\n")
            f.write(f"- 公网访问域名: {address_domain}\n")
            f.write(f"- 公网访问端口: {address_port}\n")


            f.write(f"## 数据库配置\n")
            f.write(f"- 数据库列表: {', '.join([db['name'] for db in pg_config['databases']])}\n\n")
            
            f.write(f"## 账号信息\n")
            f.write(f"- 超级用户名: {pg_config['accounts'][0]['username']}\n")
            f.write(f"- 超级用户密码: {pg_config['accounts'][0]['password']}\n")
            f.write(f"- 普通用户名: {pg_config['accounts'][1]['username']}\n")
            f.write(f"- 普通用户密码: {pg_config['accounts'][1]['password']}\n\n")
            
            f.write(f"## Schema配置\n")
            for db in pg_config['databases']:
                for schema in db['schemas']:
                    f.write(f"- {db['name']}.{schema['name']}\n")
            f.write("\n")
            
            f.write(f"## 备份策略\n")
            f.write(f"- 备份保留天数: {pg_config['backup']['retention_period']}天\n")
            f.write(f"- 全量备份周期: {pg_config['backup']['full_backup_period']}\n")
            f.write(f"- 全量备份时间: {pg_config['backup']['full_backup_time']}\n")
            f.write(f"- 增量备份频率: {pg_config['backup']['increment_backup_frequency']}\n")
        
        logger.info(f"PostgreSQL实例ID: {instance_id}")
        logger.info(f"VPC ID: {vpc_id}")
        logger.info(f"子网 ID: {subnet_id}")
        logger.info(f"EIP地址: {eip_address}")
        logger.info(f"公网访问: {address_domain}:{address_port}")
        logger.info(f"数据库列表: {', '.join([db['name'] for db in pg_config['databases']])}")
        logger.info(f"超级用户名: {pg_config['accounts'][0]['username']}")
        logger.info(f"超级用户密码: {pg_config['accounts'][0]['password']}")
        logger.info(f"普通用户名: {pg_config['accounts'][1]['username']}")
        logger.info(f"普通用户密码: {pg_config['accounts'][1]['password']}")
        logger.info(f"Schema列表: {', '.join([f"{db['name']}.{schema['name']}" for db in pg_config['databases'] for schema in db['schemas']])}")

if __name__ == '__main__':
    main()