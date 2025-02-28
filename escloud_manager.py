# coding: utf-8

import time
import logging
import os
from volcenginesdkcore.rest import ApiException
import volcenginesdkcore
import volcenginesdkescloud
from configs.api_config import api_config
from vpc_manager import VPCManager
from configs.escloud_configs import instance_configs

# 确保logs目录存在
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(log_dir, 'escloud_manager.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class ESCloudManager:
    def __init__(self):
        self._init_client()
        self.api = volcenginesdkescloud
        self.client_api = self.api.ESCLOUDApi()
        self.vpc_manager = VPCManager()
        self.current_config = None
        self.max_retries = 3  # 最大重试次数
        self.retry_interval = 5  # 重试间隔（秒）

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)

    def _validate_instance_config(self, instance_config):
        """验证实例配置的完整性和有效性"""
        required_fields = [
            'instance.name', 'instance.version', 'instance.zone_id',
            'instance.instance_type', 'instance.node_number', 'instance.node_spec',
            'instance.storage_type', 'instance.storage_space_gb', 'instance.project_name',
            'instance.charge_info.charge_type', 'instance.charge_info.period',
            'instance.charge_info.period_unit', 'instance.charge_info.auto_renew'
        ]

        for field in required_fields:
            parts = field.split('.')
            current = instance_config
            print(current)
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    logger.error(f"配置缺少必要字段: {field}")
                    return False
                current = current[part]

        return True

    def create_instance(self, instance_config, vpc_id=None, subnet_id=None):
        self.current_config = instance_config

        # # 验证配置
        # if not self._validate_instance_config(instance_config):
        #     return None

        try:
            # 检查实例是否已存在
            list_request = self.api.DescribeInstancesRequest()
            list_response = self.client_api.describe_instances(list_request)
            for instance in list_response.instances:
                if instance.instance_configuration.instance_name == instance_config['instance']['name']:
                    logger.info(f"实例已存在，实例ID: {instance.instance_id}")
                    return instance.instance_id

            # 检查网络参数
            if not vpc_id or not subnet_id:
                logger.error("创建ESCloud实例需要提供有效的VPC ID和子网ID")
                return None

            # 创建新实例
            request = self.api.CreateInstanceRequest(
                instance_name=instance_config['instance']['name'],
                version=instance_config['instance']['version'],
                zone_id=instance_config['instance']['zone_id'],
                instance_type=instance_config['instance']['instance_type'],
                node_number=instance_config['instance']['node_number'],
                node_spec=instance_config['instance']['node_spec'],
                storage_type=instance_config['instance']['storage_type'],
                storage_space_gb=instance_config['instance']['storage_space_gb'],
                project_name=instance_config['instance']['project_name'],
                vpc_id=vpc_id,
                subnet_id=subnet_id,
                charge_type=instance_config['instance']['charge_info']['charge_type'],
                period=instance_config['instance']['charge_info']['period'],
                period_unit=instance_config['instance']['charge_info']['period_unit'],
                auto_renew=instance_config['instance']['charge_info']['auto_renew']
            )

            response = self.client_api.create_instance(request)
            logger.info(f"ESCloud实例创建成功: {response}")
            return response.instance_id

        except ApiException as e:
            logger.error(f"创建ESCloud实例时发生异常: {e}")
            return None
            
    def create_instance_in_one_step(self, instance_config, vpc_id=None, subnet_id=None):
        """
        一步创建ESCloud实例，支持更丰富的配置选项
        参考Go SDK实现，支持多种节点类型和网络配置
        """
        self.current_config = instance_config
        
        try:
            # 检查实例是否已存在
            list_request = self.api.DescribeInstancesRequest()
            list_response = self.client_api.describe_instances(list_request)
            for instance in list_response.instances:
                if instance.instance_configuration.instance_name == instance_config['instance']['name']:
                    logger.info(f"实例已存在，实例ID: {instance.instance_id}")
                    return instance.instance_id
                    
            # 构建网络规格配置
            network_specs = []
            if 'network_specs' in instance_config['instance']:
                net_spec = (instance_config['instance']['network_specs'])
                print(net_spec)
                network_spec = self.api.NetworkSpecForCreateInstanceInOneStepInput(
                        bandwidth=net_spec.get('bandwidth'),
                        is_open=net_spec.get('is_open'),
                        type=net_spec.get('type')
                    )
                network_specs.append(network_spec)
            # 构建节点规格分配
            node_specs_assigns = []
            
            # 添加Master节点配置
            if instance_config['instance'].get('enable_pure_master') and instance_config['instance'].get('master_node_number'):
                master_node = self.api.NodeSpecsAssignForCreateInstanceInOneStepInput(
                    number=instance_config['instance']['master_node_number'],
                    resource_spec_name=instance_config['instance']['master_node_spec'],
                    storage_size=instance_config['instance']['master_node_storage_size'],
                    storage_spec_name=instance_config['instance']['master_node_storage_type'],
                    type="Master"
                )
                node_specs_assigns.append(master_node)
            print(node_specs_assigns)
            # 添加Kibana节点配置
            if instance_config['instance'].get('kibana_node_number'):
                kibana_node = self.api.NodeSpecsAssignForCreateInstanceInOneStepInput(
                    number=instance_config['instance']['kibana_node_number'],
                    resource_spec_name=instance_config['instance']['kibana_node_spec'],
                    type="Kibana",
                    storage_size=0
                    # Kibana节点不需要存储相关参数
                )
                node_specs_assigns.append(kibana_node)
            print(node_specs_assigns)
            # 添加Hot节点配置
            if instance_config['instance'].get('hot_node_number'):
                hot_node = self.api.NodeSpecsAssignForCreateInstanceInOneStepInput(
                    number=instance_config['instance']['hot_node_number'],
                    resource_spec_name=instance_config['instance']['hot_node_spec'],
                    storage_size=instance_config['instance']['hot_node_storage_size'],
                    storage_spec_name=instance_config['instance']['hot_node_storage_type'],
                    type="Hot"
                )
                node_specs_assigns.append(hot_node)
            print(node_specs_assigns)
            # 构建VPC和子网配置
            vpc_config = None
            subnet_config = None
            
            if vpc_id and subnet_id:
                vpc_config = self.api.VPCForCreateInstanceInOneStepInput(
                    vpc_id=vpc_id,
                    vpc_name=instance_config['instance']['vpc'].get('name') if 'vpc' in instance_config['instance'] else None
                )
                
                subnet_config = self.api.SubnetForCreateInstanceInOneStepInput(
                    subnet_id=subnet_id,
                    subnet_name=instance_config['instance']['subnet'].get('name') if 'subnet' in instance_config['instance'] else None
                )
            
            # 构建实例配置
            instance_configuration = self.api.InstanceConfigurationForCreateInstanceInOneStepInput(
                instance_name=instance_config['instance']['name'],
                version=instance_config['instance']['version'],
                zone_id=instance_config['instance']['zone_id'],
                enable_pure_master=instance_config['instance'].get('enable_pure_master', False),
                enable_https=instance_config['instance'].get('enable_https', True),
                admin_password=instance_config['instance'].get('admin_password', 'Test@1234'),  # 默认密码
                project_name=instance_config['instance'].get('project_name', 'default'),
                region_id=api_config.get('region', 'cn-shanghai'),
                charge_type=instance_config['instance']['charge_info'].get('charge_type', 'PrePaid'),
                period=instance_config['instance']['charge_info'].get('period', 1),
                auto_renew=instance_config['instance']['charge_info'].get('auto_renew', True),
                deletion_protection=instance_config['instance'].get('deletion_protection', False),
                network_specs=network_specs,
                node_specs_assigns=node_specs_assigns,
                vpc=vpc_config,
                subnet=subnet_config
            )
            
            # 构建创建请求
            request = self.api.CreateInstanceInOneStepRequest(
                instance_configuration=instance_configuration
            )
            print(request)
            # 发送请求
            response = self.client_api.create_instance_in_one_step(request)
            logger.info(f"ESCloud实例一步创建成功: {response}")
            # 从响应中提取实例ID
            if hasattr(response, 'instance_id'):
                logger.info(f"创建的实例ID: {response.instance_id}")
                return response.instance_id
            else:
                logger.error("响应中没有实例ID信息")
                return None
            
        except ApiException as e:
            logger.error(f"一步创建ESCloud实例时发生异常: {e}")
            return None

    def get_instance_detail(self, instance_id):
        """获取实例详细信息"""
        try:
            request = self.api.DescribeInstancesRequest()
            request.filter = [{"name": "InstanceId", "values": [instance_id]}]
            response = self.client_api.describe_instances(request)
            return response
        except ApiException as e:
            logger.error(f"获取实例详情时发生异常: {e}")
            return None

    def delete_instance(self, instance_id):
        """删除实例"""
        try:
            request = self.api.DeleteInstanceRequest(
                instance_id=instance_id
            )
            self.client_api.delete_instance(request)
            logger.info(f"实例 {instance_id} 删除请求已发送")
            return True
        except ApiException as e:
            logger.error(f"删除实例时发生异常: {e}")
            return False

    def wait_for_instance_ready(self, instance_id, timeout=1800, interval=30):
        start_time = time.time()
        while True:
            try:
                request = self.api.DescribeInstancesRequest()
                response = self.client_api.describe_instances(request)
                
                for instance in response.instances:
                    if instance.instance_id == instance_id:
                        if instance.status == "Running":
                            logger.info(f"实例 {instance_id} 已准备就绪")
                            return True
                        logger.info(f"实例 {instance_id} 当前状态: {instance.status}，等待 {interval} 秒后重试...")
                        break
                else:
                    logger.warning(f"未找到实例 {instance_id}，可能正在创建中，等待 {interval} 秒后重试...")
                
                if time.time() - start_time > timeout:
                    logger.error(f"等待实例 {instance_id} 就绪超时，已等待 {timeout} 秒")
                    return False
                    
                time.sleep(interval)
                
            except ApiException as e:
                logger.error(f"检查实例 {instance_id} 状态时发生错误: {e}")
                return False


    def create_public_endpoint(self, instance_id, eip_id):
        try:
            request = self.api.CreatePublicEndpointRequest(
                instance_id=instance_id,
                eip_id=eip_id
            )
            
            response = self.client_api.create_public_endpoint(request)
            logger.info("正在创建公网访问地址...")
            
            # 等待公网访问端点创建完成
            max_retries = 10
            retry_interval = 30
            for retry in range(max_retries):
                describe_request = self.api.DescribeInstanceDetailRequest(
                    instance_id=instance_id
                )
                describe_response = self.client_api.describe_instance_detail(describe_request)
                
                if hasattr(describe_response, 'public_endpoint'):
                    logger.info(f"公网访问端点创建成功: {describe_response.public_endpoint}")
                    return describe_response.public_endpoint
                
                if retry < max_retries - 1:
                    logger.info(f"等待{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                else:
                    logger.error("等待公网访问端点创建超时")
                    return None
            
            return None
            
        except ApiException as e:
            logger.error(f"创建公网访问地址时发生异常: {e}")
            return None

    def get_instance_status(self, instance_id):
        """获取实例状态"""
        try:
            request = self.api.DescribeInstancesRequest()
            response = self.client_api.describe_instances(request)
            
            for instance in response.instances:
                if instance.instance_id == instance_id:
                    return instance.status
            
            return None
        except ApiException as e:
            logger.error(f"获取实例状态时发生异常: {e}")
            return None

    def restart_instance(self, instance_id):
        """重启实例"""
        try:
            request = self.api.RestartInstanceRequest(
                instance_id=instance_id
            )
            self.client_api.restart_instance(request)
            logger.info(f"实例 {instance_id} 重启请求已发送")
            return True
        except ApiException as e:
            logger.error(f"重启实例时发生异常: {e}")
            return False

    def deletion_protection(self, instance_id, deletion_protection=True):
        """禁用实例的删除保护"""
        try:
            request = self.api.ModifyDeletionProtectionRequest(
                instance_id=instance_id,
                deletion_protection=deletion_protection
            )
            response = self.client_api.modify_deletion_protection(request)
            logger.info(f"实例 {instance_id} 的删除保护已禁用")
            return True
        except ApiException as e:
            logger.error(f"禁用删除保护时发生异常: {e}")
            return False

    def release_instance(self, instance_id, deletion_protection=False):
        """释放实例（删除实例）"""
        try:
            # 先禁用删除保护
            if not self.deletion_protection(instance_id, deletion_protection=False):
                logger.error(f"无法禁用实例 {instance_id} 的删除保护，无法释放实例")
                return False
                
            # 释放实例
            request = self.api.ReleaseInstanceRequest(
                instance_id=instance_id
            )
            response = self.client_api.release_instance(request)
            logger.info(f"实例 {instance_id} 释放请求已发送")
            return True
        except ApiException as e:
            logger.error(f"释放实例时发生异常: {e}")
            return False


    # 删除重复的wait_for_instance_ready方法

    def create_whitelist(self, instance_id, instance_config):

        ip_list = instance_config['instance']['whitelist_ip']
        print(ip_list)
        try:
            # 直接定义白名单IP列表，不引用外部whitelist_manager
            # 这里可以根据需要设置默认的IP列表或从配置文件中读取
            # 注意：ESCloud不支持CIDR格式(0.0.0.0/0)，需要使用不带CIDR的格式(0.0.0.0)
            ip_list = instance_config['instance']['whitelist_ip']
            print(ip_list)
            
            # 创建ModifyIpWhitelistRequest请求
            request = self.api.ModifyIpWhitelistRequest(
                component="kibana",  # 设置组件为kibana
                instance_id=instance_id,
                ip_list=ip_list,
                type="public"  # 设置类型为公网
            )
            
            # 调用modify_ip_whitelist API
            response = self.client_api.modify_ip_whitelist(request)
            logger.info(f"成功为实例 {instance_id} 设置白名单: {ip_list}")
            return True
            
        except Exception as e:
            logger.error(f"创建或绑定白名单时发生异常: {e}")
            return False

    def get_private_endpoint(self, instance_id):
        try:
            print(f"获取实例 {instance_id} 的内网访问信息")
            describe_response = self.get_instance_detail(instance_id)
            if not describe_response:
                return None, None, None
            
            # 从返回的实例列表中找到匹配ID的实例
            target_instance = None
            if hasattr(describe_response, 'instances'):
                for instance in describe_response.instances:
                    if instance.instance_id == instance_id:
                        target_instance = instance
                        break
            
            if not target_instance:
                logger.info(f"未找到ID为 {instance_id} 的实例")
                return None, None, None
            # print(target_instance)
            # 初始化返回值
            es_private_endpoint = None
            kibana_private_domain = None
            kibana_public_domain = None
            # 获取ES内网端点
            if hasattr(target_instance, 'es_private_endpoint') and target_instance.es_private_endpoint:
                es_private_endpoint = target_instance.es_private_endpoint
                logger.info(f"ES内网访问端点: {es_private_endpoint}")
            
            # 获取Kibana公网域名
            if hasattr(target_instance, 'kibana_public_domain') and target_instance.kibana_public_domain:
                kibana_public_domain = target_instance.kibana_public_domain
                logger.info(f"Kibana公网访问端点: {kibana_public_domain}")
            
            # 获取Kibana内网域名
            if hasattr(target_instance, 'kibana_private_domain') and target_instance.kibana_private_domain:
                kibana_private_domain = target_instance.kibana_private_domain
                logger.info(f"Kibana内网访问端点: {kibana_private_domain}")
            
            return es_private_endpoint, kibana_private_domain, kibana_public_domain
            
        except ApiException as e:
            logger.error(f"获取内网访问信息时发生异常: {e}")
            return None, None, None
            
def main():
    instance_manager = ESCloudManager()
    vpc_manager = VPCManager()
    subnet_id = None  # 初始化subnet_id变量

    # 遍历所有PostgreSQL实例配置
    for instance_config in instance_configs:
        logger.info(f"\n开始创建实例: {instance_config['instance']['name']}")

        # 1. 检查配置中是否已指定VPC和子网
        if 'vpc_id' in instance_config['instance'] and 'subnet_id' in instance_config['instance']:
            vpc_id = instance_config['instance']['vpc_id']
            subnet_id = instance_config['instance']['subnet_id']
            logger.info(f"使用配置中指定的VPC ID: {vpc_id} 和子网 ID: {subnet_id}")
            instance_subnet_id = subnet_id
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
            instance_subnet_id = subnet_id

        if not instance_subnet_id:
            logger.error("在实例指定可用区未找到或创建子网失败")
            continue

        # 3. 创建PostgreSQL实例
        instance_id = instance_manager.create_instance_in_one_step(instance_config, vpc_id, subnet_id)
        if not instance_id:
            logger.error("创建实例失败")
            continue

        # 等待实例创建完成
        logger.info("等待实例创建完成...")
        if not instance_manager.wait_for_instance_ready(instance_id):
            logger.error("实例创建超时或失败")
            continue


        # 5.1.  获取访问端点信息
        es_private_endpoint, kibana_private_domain, kibana_public_domain = instance_manager.get_private_endpoint(instance_id)
        if not es_private_endpoint:
            logger.error("获取访问端点信息失败")
            continue
        
        # 确保即使后续步骤失败，也会显示所有端点信息
        logger.info(f"ES内网访问端点: {es_private_endpoint}")
        if kibana_private_domain:
            logger.info(f"Kibana内网访问端点: {kibana_private_domain}")
        if kibana_public_domain:
            logger.info(f"Kibana公网访问端点: {kibana_public_domain}")
            
        # 6. 创建白名单
        try:
            if not instance_manager.create_whitelist(instance_id, instance_config):
                logger.error("创建白名单失败")
                # 继续执行，不中断流程
        except Exception as e:
            logger.error(f"创建白名单时发生异常: {e}")
            # 继续执行，不中断流程



        logger.info(f"成功完成实例 {instance_config['instance']['name']} 的所有操作！")
        
        # 将实例信息写入日志文件，使用追加模式
        pg_instance_info_path = os.path.join(log_dir, 'escloud_instance_info.md')
        with open(pg_instance_info_path, 'a', encoding='utf-8') as f:
            # 添加分隔符和时间戳
            f.write(f"\n{'='*50}\n")
            f.write(f"记录时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"# PostgreSQL实例创建记录\n\n")
            f.write(f"## 实例信息\n")
            f.write(f"- 实例ID: {instance_id}\n")
            f.write(f"- 实例名称: {instance_config['instance']['name']}\n")
            f.write(f"- 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"## 网络配置\n")
            f.write(f"- VPC ID: {vpc_id}\n")
            f.write(f"- 子网 ID: {subnet_id}\n")
            f.write(f"- ES内网访问信息: {es_private_endpoint}\n")
            f.write(f"- Kibana内网访问信息: {kibana_private_domain}\n")
            f.write(f"- Kibana内网访问信息: {kibana_public_domain}\n")



        #     f.write(f"## 数据库配置\n")
        #     f.write(f"- 数据库列表: {', '.join([db['name'] for db in instance_config['databases']])}\n\n")
            
        #     f.write(f"## 账号信息\n")
        #     f.write(f"- 超级用户名: {instance_config['accounts'][0]['username']}\n")
        #     f.write(f"- 超级用户密码: {instance_config['accounts'][0]['password']}\n")
        #     f.write(f"- 普通用户名: {instance_config['accounts'][1]['username']}\n")
        #     f.write(f"- 普通用户密码: {instance_config['accounts'][1]['password']}\n\n")
            
        #     f.write(f"## Schema配置\n")
        #     for db in instance_config['databases']:
        #         for schema in db['schemas']:
        #             f.write(f"- {db['name']}.{schema['name']}\n")
        #     f.write("\n")
            
        #     f.write(f"## 备份策略\n")
        #     f.write(f"- 备份保留天数: {instance_config['backup']['retention_period']}天\n")
        #     f.write(f"- 全量备份周期: {instance_config['backup']['full_backup_period']}\n")
        #     f.write(f"- 全量备份时间: {instance_config['backup']['full_backup_time']}\n")
        #     f.write(f"- 增量备份频率: {instance_config['backup']['increment_backup_frequency']}\n")
        
        # logger.info(f"PostgreSQL实例ID: {instance_id}")
        # logger.info(f"VPC ID: {vpc_id}")
        # logger.info(f"子网 ID: {subnet_id}")
        # logger.info(f"EIP地址: {eip_address}")
        # logger.info(f"公网访问: {address_domain}:{address_port}")
        # logger.info(f"数据库列表: {', '.join([db['name'] for db in instance_config['databases']])}")
        # logger.info(f"超级用户名: {instance_config['accounts'][0]['username']}")
        # logger.info(f"超级用户密码: {instance_config['accounts'][0]['password']}")
        # logger.info(f"普通用户名: {instance_config['accounts'][1]['username']}")
        # logger.info(f"普通用户密码: {instance_config['accounts'][1]['password']}")
        # logger.info(f"Schema列表: {', '.join([f"{db['name']}.{schema['name']}" for db in instance_config['databases'] for schema in db['schemas']])}")

if __name__ == '__main__':
    main()