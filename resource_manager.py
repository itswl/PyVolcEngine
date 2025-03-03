# coding: utf-8

from __future__ import absolute_import

from volcenginesdkcore.configuration import Configuration
from volcenginesdkcore.rest import ApiException
from whitelist_manager import WhitelistBaseManager
from configs.api_config import api_config
import volcenginesdkrdspostgresql
import volcenginesdkredis
import volcenginesdkmongodb
import volcenginesdkvpc

import os
import time

# 确保logs目录存在

import logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(log_dir, 'resource_cleaner.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

class ResourceBase:
    """资源清理基类，提供通用的资源清理逻辑

    这个基类实现了资源清理的基本功能，包括：
    - 客户端初始化
    - 白名单解绑
    - EIP释放
    - 实例删除
    - 资源清理
    
    子类需要实现具体的API调用方法。
    """

    # 定义成功状态常量
    SUCCESS = True

    def __init__(self):
        self._init_client()
        self.api = None  # 子类需要设置具体的API实例
        self.client_api = None
        self.whitelist_manager = WhitelistBaseManager()  # 实例化白名单管理器



    def _init_client(self):
        """初始化API客户端配置"""
        configuration = Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        Configuration.set_default(configuration)

    def disassociate_whitelist(self, instance_id):
        """解绑实例的白名单

        :param instance_id: 实例ID
        :return: bool 操作是否成功
        """
        try:
            if self.whitelist_manager is None:
                logger.error("白名单管理器未初始化")
                return not self.SUCCESS

            success = self.whitelist_manager.unbind_whitelists_from_instance(instance_id)
            return success

        except Exception as e:
            logger.error(f"解绑白名单时发生异常: {e}")
            return not self.SUCCESS

    def release_eip(self, eip_address=None, allocation_id=None):
        """释放指定的EIP资源
        :param eip_address: EIP地址，与allocation_id至少需要提供一个
        :param allocation_id: EIP的分配ID，如果提供则优先使用
        :return: bool 操作是否成功
        """
        try:
            # 初始化VPC API客户端
            vpc_api = volcenginesdkvpc.VPCApi()
            
            # 如果没有提供allocation_id，则通过eip_address查询
            if not allocation_id:
                if not eip_address:
                    logger.error("需要提供eip_address或allocation_id参数")
                    return not self.SUCCESS
                    
                # 通过EIP地址查询allocation_id
                list_request = volcenginesdkvpc.DescribeEipAddressesRequest()
                list_response = vpc_api.describe_eip_addresses(list_request)
                
                eip_info = None
                if hasattr(list_response, 'eip_addresses'):
                    for eip in list_response.eip_addresses:
                        if eip.eip_address == eip_address:
                            allocation_id = eip.allocation_id
                            eip_info = eip
                            break
                
                if not allocation_id:
                    logger.error(f"未找到EIP地址 {eip_address} 对应的allocation_id")
                    return not self.SUCCESS
                    
                # 检查EIP是否已绑定实例
                if eip_info and hasattr(eip_info, 'instance_id') and eip_info.instance_id:
                    # 如果EIP已绑定实例，先解绑
                    try:
                        disassociate_request = volcenginesdkvpc.DisassociateEipAddressRequest(
                            allocation_id=allocation_id
                        )
                        vpc_api.disassociate_eip_address(disassociate_request)
                        logger.info(f"已解绑EIP {eip_address} 与实例 {eip_info.instance_id}")
                        # 等待解绑操作生效
                        time.sleep(5)
                    except ApiException as e:
                        logger.error(f"解绑EIP时发生错误: {e}")
                        return not self.SUCCESS
            
            # 创建释放请求
            release_request = volcenginesdkvpc.ReleaseEipAddressRequest(
                allocation_id=allocation_id
            )
            
            # 执行释放操作
            vpc_api.release_eip_address(release_request)
            # 记录日志时，优先使用eip_address（如果有）
            if eip_address:
                logger.info(f"已成功释放EIP: {eip_address}")
            else:
                logger.info(f"已成功释放EIP，allocation_id: {allocation_id}")
            return self.SUCCESS
            
        except ApiException as e:
            logger.error(f"释放EIP时发生错误: {e}")
            return not self.SUCCESS

    def delete_instance(self, instance_id):
        """删除实例
        :param instance_id: 实例ID
        :return: bool 操作是否成功
        """
        try:
            # 根据API类型选择合适的删除请求
            if hasattr(self.api, 'DeleteDBInstanceRequest'):
                # 数据库类实例（PostgreSQL、Redis等）
                delete_request = self.api.DeleteDBInstanceRequest(
                    instance_id=instance_id
                )
                self.client_api.delete_db_instance(delete_request)
            elif hasattr(self.api, 'DeleteInstanceRequest'):
                # 其他类型实例（Kafka等）
                delete_request = self.api.DeleteInstanceRequest(
                    instance_id=instance_id
                )
                self.client_api.delete_instance(delete_request)
            else:
                logger.error(f"未找到支持的删除实例接口")
                return not self.SUCCESS
                
            logger.info(f"已成功删除实例 {instance_id}")
            return self.SUCCESS

        except ApiException as e:
            logger.error(f"删除数据库实例时发生错误: {e}")
            return not self.SUCCESS

    def get_instance_detail(self, instance_id=None):
        """获取实例详细信息

        :param instance_id: 可选，实例ID。如果不提供，则返回所有实例的详细信息
        :return: 如果提供instance_id，返回单个实例详细信息对象；否则返回所有实例详细信息的列表
        """
        try:
            if instance_id:
                # 获取单个实例的详细信息
                detail_request = self.api.DescribeDBInstanceDetailRequest(
                    instance_id=instance_id
                )
                detail_response = self.client_api.describe_db_instance_detail(detail_request)
                logger.info(f"已成功获取实例 {instance_id} 的详细信息")
                return detail_response
            else:
                # 获取所有实例的详细信息
                list_request = self.api.DescribeDBInstancesRequest()
                list_response = self.client_api.describe_db_instances(list_request)
                
                instances = []
                # 兼容不同API返回的字段名
                if hasattr(list_response, 'instances'):
                    instances = list_response.instances
                elif hasattr(list_response, 'db_instances'):
                    instances = list_response.db_instances
                
                if not instances:
                    logger.info("未找到任何实例")
                    return []
                
                # 获取每个实例的详细信息
                details = []
                for instance in instances:
                    try:
                        instance_id = instance.instance_id
                        detail_request = self.api.DescribeDBInstanceDetailRequest(
                            instance_id=instance_id
                        )
                        detail_response = self.client_api.describe_db_instance_detail(detail_request)
                        details.append(detail_response)
                    except ApiException as e:
                        logger.error(f"获取实例 {instance_id} 详细信息时发生错误: {e}")
                        continue
                
                logger.info(f"已成功获取 {len(details)} 个实例的详细信息")
                return details
            
        except ApiException as e:
            logger.error(f"获取实例详细信息时发生错误: {e}")
            return None if instance_id else []

    def list_instances(self, filters=None,page_number=None, page_size=None):
        """列出实例信息

        :param filters: 可选，过滤条件
        :return: list 实例信息列表
        """
        try:
            if hasattr(self.api, 'DescribeDBInstancesRequest'):
                list_request = self.api.DescribeDBInstancesRequest()
                list_response = self.client_api.describe_db_instances(list_request)
            else:
                list_request = self.api.DescribeInstancesRequest(page_number=page_number,page_size=page_size)
                list_response = self.client_api.describe_instances(list_request)
                # print(list_response)
            
            # print(list_response)
            instances = []
            # 兼容不同API返回的字段名
            if hasattr(list_response, 'instances'):
                instances = list_response.instances
            elif hasattr(list_response, 'db_instances'):
                instances = list_response.db_instances
            elif hasattr(list_response, 'instances_info'):
                instances = list_response.instances_info
            # print(instances)    
            # 格式化实例信息
            result = []
            for instance in instances:
                instance_info = {
                    'instance_id': instance.instance_id,
                    'instance_name': instance.instance_name if hasattr(instance, 'instance_name') else '',
                    'status': getattr(instance, 'status', None) or getattr(instance, 'instance_status', None),
                    'create_time': getattr(instance, 'create_time', None) or getattr(instance, 'created_time', None),
                    
                }

                # 添加可能存在的其他属性
                if hasattr(instance, 'vpc_id'):
                    instance_info['vpc_id'] = instance.vpc_id
                if hasattr(instance, 'subnet_id'):
                    instance_info['subnet_id'] = instance.subnet_id
                if hasattr(instance, 'db_engine_version'):
                    instance_info['db_engine_version'] = instance.db_engine_version
                
                # 检查是否有公网访问点，如果有则添加eip_id和ip_address信息
                if hasattr(instance, 'address_object'):
                    for address in instance.address_object:
                        if hasattr(address, 'network_type') and address.network_type == 'Public':
                            instance_info['eip_id'] = getattr(address, 'eip_id', '')
                            instance_info['public_ip'] = getattr(address, 'ip_address', '')
                            break
                
                # 应用过滤条件
                if filters:
                    match = True
                    for key, value in filters.items():
                        if key in instance_info and instance_info[key] != value:
                            match = False
                            break
                    if match:
                        result.append(instance_info)
                else:
                    result.append(instance_info)
            # print(result)
            return result
            
        except ApiException as e:
            logger.error(f"列出实例时发生错误: {e}")
            return []

    def clean_all_resources(self, instance_ids, eip_addresses=None):
        """清理所有相关资源

        :param instance_ids: 实例ID列表
        :param eip_addresses: 可选，EIP地址列表
        :return: bool 所有清理操作是否成功
        """
        if not isinstance(instance_ids, list):
            instance_ids = [instance_ids]
        
        if eip_addresses and not isinstance(eip_addresses, list):
            eip_addresses = [eip_addresses]
        
        overall_success = True
        eip_index = 0

        for instance_id in instance_ids:
            success = True
            logger.info(f"\n开始清理实例 {instance_id} 的资源")

            # 1. 首先解绑白名单
            if not self.disassociate_whitelist(instance_id):
                logger.error(f"实例 {instance_id} 的白名单解绑失败")
                success = False

            # 2. 如果提供了EIP地址，释放EIP
            if eip_addresses and eip_index < len(eip_addresses):
                eip_address = eip_addresses[eip_index]
                if not self.release_eip(eip_address):
                    logger.error(f"EIP {eip_address} 释放失败")
                    success = False
                eip_index += 1

            # 3. 最后删除实例
            if not self.delete_instance(instance_id):
                logger.error(f"实例 {instance_id} 删除失败")
                success = False

            if success:
                logger.info(f"实例 {instance_id} 的所有资源清理完成")
            else:
                logger.warning(f"实例 {instance_id} 的部分资源清理失败")
                overall_success = False

        return overall_success

    def _handle_api_exception(self, e, operation):
        """统一处理API异常

        :param e: API异常
        :param operation: 操作描述
        :return: bool 操作是否成功
        """
        logger.error(f"{operation}时发生异常: {e}")
        return False

class PostgreSQLResource(ResourceBase):
    def __init__(self):
        super().__init__()
        self.api = volcenginesdkrdspostgresql
        self.client_api = self.api.RDSPOSTGRESQLApi()
        # 确保白名单管理器使用正确的API
        self.whitelist_manager.api = self.api
        self.whitelist_manager.client_api = self.client_api


class RedisResource(ResourceBase):
    def __init__(self):
        super().__init__()
        self.api = volcenginesdkredis
        self.client_api = self.api.REDISApi()
        self.whitelist_manager.api = self.api
        self.whitelist_manager.client_api = self.client_api


class MongoDbResource(ResourceBase):
    def __init__(self):
        super().__init__()
        self.api = volcenginesdkmongodb
        self.client_api = self.api.MONGODBApi()
        self.whitelist_manager.api = self.api
        self.whitelist_manager.client_api = self.client_api


import volcenginesdkkafka
class KafkaResource(ResourceBase):
    def __init__(self):
        super().__init__()
        self.api = volcenginesdkkafka
        self.client_api = self.api.KAFKAApi()
        self.whitelist_manager.api = self.api
        self.whitelist_manager.client_api = self.client_api

import volcenginesdkescloud
class ESCloudResource(ResourceBase):
    def __init__(self):
        super().__init__()
        self.api = volcenginesdkescloud
        self.client_api = self.api.ESCLOUDApi()
        self.whitelist_manager.api = self.api
        self.whitelist_manager.client_api = self.client_api

