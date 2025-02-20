# coding: utf-8

from __future__ import absolute_import

from volcenginesdkcore.configuration import Configuration
from volcenginesdkcore.rest import ApiException
from whitelist_manager import WhitelistBaseManager
from configs.api_config import api_config
import volcenginesdkrdspostgresql
import volcenginesdkredis
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

class ResourceBaseCleaner:
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

    def release_eip(self, eip_address):
        """释放指定的EIP资源
        :param eip_address: EIP地址
        :return: bool 操作是否成功
        """
        try:
            # 初始化VPC API客户端
            vpc_api = volcenginesdkvpc.VPCApi()
            
            # 先获取EIP的allocation_id
            list_request = volcenginesdkvpc.DescribeEipAddressesRequest()
            list_response = vpc_api.describe_eip_addresses(list_request)
            
            allocation_id = None
            if hasattr(list_response, 'eip_addresses'):
                for eip in list_response.eip_addresses:
                    if eip.eip_address == eip_address:
                        allocation_id = eip.allocation_id
                        # 检查EIP是否已绑定实例
                        if hasattr(eip, 'instance_id') and eip.instance_id:
                            # 如果EIP已绑定实例，先解绑
                            try:
                                disassociate_request = volcenginesdkvpc.DisassociateEipAddressRequest(
                                    allocation_id=allocation_id
                                )
                                vpc_api.disassociate_eip_address(disassociate_request)
                                logger.info(f"已解绑EIP {eip_address} 与实例 {eip.instance_id}")
                                # 等待解绑操作生效
                                time.sleep(5)
                            except ApiException as e:
                                logger.error(f"解绑EIP时发生错误: {e}")
                                return not self.SUCCESS
                        break
            
            if not allocation_id:
                logger.error(f"未找到EIP地址 {eip_address} 对应的allocation_id")
                return not self.SUCCESS
            
            # 创建释放请求
            release_request = volcenginesdkvpc.ReleaseEipAddressRequest(
                allocation_id=allocation_id
            )
            
            # 执行释放操作
            vpc_api.release_eip_address(release_request)
            logger.info(f"已成功释放EIP: {eip_address}")
            return self.SUCCESS
            
        except ApiException as e:
            logger.error(f"释放EIP时发生错误: {e}")
            return not self.SUCCESS

    def delete_instance(self, instance_id):
        """删除PostgreSQL实例
        :param instance_id: 实例ID
        :return: bool 操作是否成功
        """
        try:
            # 删除实例
            delete_request = self.api.DeleteDBInstanceRequest(
                instance_id=instance_id
            )
            self.client_api.delete_db_instance(delete_request)
            logger.info(f"已成功删除数据库实例 {instance_id}")
            return self.SUCCESS

        except ApiException as e:
            logger.error(f"删除数据库实例时发生错误: {e}")
            return not self.SUCCESS

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

class PostgreSQLResourceCleaner(ResourceBaseCleaner):
    def __init__(self):
        super().__init__()
        self.api = volcenginesdkrdspostgresql
        self.client_api = self.api.RDSPOSTGRESQLApi()
        # 确保白名单管理器使用正确的API
        self.whitelist_manager.api = self.api
        self.whitelist_manager.client_api = self.client_api


class RedisResourceCleaner(ResourceBaseCleaner):
    def __init__(self):
        super().__init__()
        self.api = volcenginesdkredis
        self.client_api = self.api.REDISApi()
        self.whitelist_manager.api = self.api
        self.whitelist_manager.client_api = self.client_api

