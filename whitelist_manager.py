# coding: utf-8

from __future__ import absolute_import

from volcenginesdkcore.configuration import Configuration
from volcenginesdkcore.rest import ApiException
from configs.api_config import api_config
from configs.whitelist_config import whitelist_config
import logging

logger = logging.getLogger(__name__)

class WhitelistBaseManager:
    """白名单管理基类，提供通用的白名单处理逻辑

    这个基类实现了白名单管理的基本功能，包括：
    - 客户端初始化
    - 白名单创建
    - 白名单绑定
    - 白名单查询
    - 白名单配置加载
    
    子类需要实现具体的API调用方法。
    """

    def __init__(self):
        self._init_client()
        self.api = None  # 子类需要设置具体的API实例
        self.client_api = None 
        self.whitelist_config = whitelist_config  # 从配置文件加载白名单配置

    def get_whitelist_config(self):
        """获取白名单配置

        :return: dict 白名单配置信息
        """
        return self.whitelist_config

        
    def _init_client(self):
        """初始化API客户端配置"""
        configuration = Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        Configuration.set_default(configuration)

    def create_whitelist(self, whitelist_config):
        """创建白名单

        :param whitelist_config: 白名单配置信息，可以是字典或字符串
        :return: (bool, str) 元组，包含创建结果和白名单ID（如果创建成功）
        """
        try:
            # 先检查是否已存在同名白名单
            list_request = self.api.DescribeAllowListsRequest(
                region_id=api_config['region']
            )
            list_response = self.client_api.describe_allow_lists(list_request)
            
            whitelist_name = whitelist_config['name'] if isinstance(whitelist_config, dict) else whitelist_config
            
            if hasattr(list_response, 'allow_lists'):
                for allow_list in list_response.allow_lists:
                    if allow_list.allow_list_name == whitelist_name:
                        logger.info(f"白名单 {whitelist_name} 已存在，白名单ID: {allow_list.allow_list_id}")
                        return True, allow_list.allow_list_id

            # 如果不存在，则创建新的白名单
            create_request = self.api.CreateAllowListRequest(
                allow_list_desc=whitelist_config.get('description', '') if isinstance(whitelist_config, dict) else '',
                allow_list_name=whitelist_name,
                allow_list=','.join(whitelist_config.get('ip_list', [])) if isinstance(whitelist_config, dict) else ''
            )
            create_response = self.client_api.create_allow_list(create_request)
            whitelist_id = create_response.allow_list_id
            
            logger.info(f"白名单 {whitelist_name} 创建成功")
            logger.info(f"白名单详细信息：")
            logger.info(f"  - ID: {whitelist_id}")
            logger.info(f"  - 名称: {whitelist_name}")
            if isinstance(whitelist_config, dict):
                logger.info(f"  - 描述: {whitelist_config.get('description', '')}")
                logger.info(f"  - IP列表: {', '.join(whitelist_config.get('ip_list', []))}")
            
            return True, whitelist_id
        except ApiException as e:
            return self._handle_api_exception(e, "创建白名单")

    def bind_whitelists_to_instance(self, instance_id):
        """
        将白名单绑定到指定的实例
        :param instance_id: 数据库实例ID
        :return: bool 是否成功
        """
        try:
            # 获取实例当前的白名单列表
            current_whitelists = self.get_instance_whitelists(instance_id)
            if not current_whitelists:
                logger.info(f"实例 {instance_id} 当前没有绑定的白名单")
            else:
                logger.info(f"实例 {instance_id} 当前已绑定的白名单: {', '.join(current_whitelists)}")

            # 等待实例状态就绪
            if not self.wait_for_instance_ready(instance_id):
                logger.error("等待实例就绪超时，无法绑定白名单")
                return False
            # 创建并绑定白名单
            try:
                # 从配置文件创建所有白名单
                whitelist_ids = []
                for whitelist_item in self.whitelist_config['whitelists']:
                    success, whitelist_id = self.create_whitelist(whitelist_item)
                    if success and whitelist_id:
                        # 检查白名单是否已经绑定到实例
                        if whitelist_id in current_whitelists:
                            logger.info(f"白名单 {whitelist_item['name']} (ID: {whitelist_id}) 已绑定到实例 {instance_id}，跳过绑定")
                            continue
                        whitelist_ids.append(whitelist_id)
                    else:
                        logger.error(f"创建白名单 {whitelist_item['name']} 失败")
                        return False
                
                if not whitelist_ids:
                    logger.info("所有白名单已经绑定到实例，无需重复绑定")
                    return True

                # 只绑定未绑定的白名单到实例
                associate_request = self.api.AssociateAllowListRequest(
                    allow_list_ids=whitelist_ids,
                    instance_ids=[instance_id]
                )
                self.client_api.associate_allow_list(associate_request)
                logger.info(f"成功将 {len(whitelist_ids)} 个新白名单绑定到实例 {instance_id}")
                return True

            except ApiException as e:
                logger.error(f"绑定白名单时发生异常: {e}")
                return False

        except ApiException as e:
            logger.error(f"创建或绑定白名单时发生异常: {e}")
            return False
            
    def get_instance_whitelists(self, instance_id):
        """获取实例的白名单列表

        :param instance_id: 实例ID
        :return: list 白名单ID列表
        """
        try:
            describe_request = self.api.DescribeAllowListsRequest(
                instance_id=instance_id,
                region_id=api_config['region']
            )
            describe_response = self.client_api.describe_allow_lists(describe_request)
            
            whitelist_ids = []
            if hasattr(describe_response, 'allow_lists'):
                for allow_list in describe_response.allow_lists:
                    whitelist_ids.append(allow_list.allow_list_id)
                    
            return whitelist_ids

        except ApiException as e:
            logger.error(f"获取实例白名单列表时发生异常: {e}")
            return []

    def wait_for_instance_ready(self, instance_id, timeout=1800, interval=30, max_retries=3):
        """等待实例准备就绪，带重试机制

        :param instance_id: 实例ID
        :param timeout: 超时时间（秒）
        :param interval: 检查间隔（秒）
        :param max_retries: 最大重试次数
        :return: bool 是否成功
        """
        import time
        start_time = time.time()
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 检查是否超时
                if time.time() - start_time > timeout:
                    logger.error(f"等待实例 {instance_id} 就绪超时")
                    return False

                # 查询实例状态
                status_request = self.api.DescribeDBInstancesRequest()
                status_response = self.client_api.describe_db_instances(status_request)
                
                # 获取实例列表，兼容不同的返回字段名
                instances = []
                if hasattr(status_response, 'instances'):
                    instances = status_response.instances
                elif hasattr(status_response, 'db_instances'):
                    instances = status_response.db_instances
                
                for instance in instances:
                    if instance.instance_id == instance_id:
                        # 兼容不同API返回的状态字段名称
                        instance_status = getattr(instance, 'status', None) or getattr(instance, 'instance_status', None)
                        if instance_status == "Running":
                            logger.info(f"实例 {instance_id} 状态正常")
                            return True
                        else:
                            logger.info(f"实例 {instance_id} 当前状态: {instance_status}，等待 {interval} 秒后重试")
                            time.sleep(interval)
                            break
                else:
                    logger.warning(f"未找到实例 {instance_id}，重试第 {retry_count + 1} 次")
                    retry_count += 1
                    time.sleep(interval)
                    continue

            except ApiException as e:
                logger.warning(f"检查实例状态时发生异常: {e}，重试第 {retry_count + 1} 次")
                retry_count += 1
                time.sleep(interval)
        logger.error(f"实例 {instance_id} 状态检查失败，已达到最大重试次数")
        return False

    def _handle_api_exception(self, e, operation):
        """统一处理API异常

        :param e: API异常
        :param operation: 操作描述
        :return: bool 操作是否成功
        """
        logger.error(f"{operation}时发生异常: {e}")
        return False, None

    def unbind_whitelists_from_instance(self, instance_id, whitelist_ids=None):
        """
        从指定实例解绑白名单

        :param instance_id: 数据库实例ID
        :param whitelist_ids: 要解绑的白名单ID列表，如果为None则解绑所有白名单
        :return: bool 是否成功
        """
        try:
            # 获取实例当前的白名单列表
            current_whitelists = self.get_instance_whitelists(instance_id)
            if not current_whitelists:
                logger.info(f"实例 {instance_id} 当前没有绑定的白名单，无需解绑")
                return True

            # 如果没有指定要解绑的白名单ID，则解绑所有白名单
            if whitelist_ids is None:
                whitelist_ids = current_whitelists
            else:
                # 验证指定的白名单是否已绑定到实例
                for whitelist_id in whitelist_ids:
                    if whitelist_id not in current_whitelists:
                        logger.warning(f"白名单 {whitelist_id} 未绑定到实例 {instance_id}，跳过解绑")
                        whitelist_ids.remove(whitelist_id)

            if not whitelist_ids:
                logger.info("没有需要解绑的白名单")
                return True

            # 等待实例状态就绪
            if not self.wait_for_instance_ready(instance_id):
                logger.error("等待实例就绪超时，无法解绑白名单")
                return False

            try:
                # 解绑白名单
                disassociate_request = self.api.DisassociateAllowListRequest(
                    allow_list_ids=whitelist_ids,
                    instance_ids=[instance_id]
                )
                self.client_api.disassociate_allow_list(disassociate_request)
                logger.info(f"成功从实例 {instance_id} 解绑 {len(whitelist_ids)} 个白名单")
                return True

            except ApiException as e:
                logger.error(f"解绑白名单时发生异常: {e}")
                return False

        except ApiException as e:
            logger.error(f"解绑白名单时发生异常: {e}")
            return False

import volcenginesdkredis
class RedisWhitelistManager(WhitelistBaseManager):
    """Redis服务的白名单管理类

    继承自WhitelistBaseManager，实现Redis服务特定的白名单操作。
    """

    def __init__(self):
        super().__init__()
        self.api = volcenginesdkredis
        self.client_api = self.api.REDISApi()


import volcenginesdkrdspostgresql
class PostgreSQLWhitelistManager(WhitelistBaseManager):
    """PostgreSQL白名单管理类
    这个类继承自WhitelistBaseManager，提供了PostgreSQL数据库的白名单管理功能。
    """

    def __init__(self):
        super().__init__()
        self.api = volcenginesdkrdspostgresql
        self.client_api = self.api.RDSPOSTGRESQLApi()

import volcenginesdkmongodb
class MongoDBWhitelistManager(WhitelistBaseManager):
    """PostgreSQL白名单管理类
    这个类继承自WhitelistBaseManager，提供了PostgreSQL数据库的白名单管理功能。
    """

    def __init__(self):
        super().__init__()
        self.api = volcenginesdkmongodb
        self.client_api = self.api.MONGODBApi()

import volcenginesdkkafka
class KafkaWhitelistManager(WhitelistBaseManager):
    """Kafka白名单管理类
    这个类继承自WhitelistBaseManager，提供了Kafka服务的白名单管理功能。
    """

    def __init__(self):
        super().__init__()
        self.api = volcenginesdkkafka
        self.client_api = self.api.KAFKAApi()

    def bind_whitelists_to_instance(self, instance_id):
        """
        将白名单绑定到指定的实例
        :param instance_id: 数据库实例ID
        :return: bool 是否成功
        """
        try:
            # 获取实例当前的白名单列表
            current_whitelists = self.get_instance_whitelists(instance_id)
            if not current_whitelists:
                logger.info(f"实例 {instance_id} 当前没有绑定的白名单")
            else:
                logger.info(f"实例 {instance_id} 当前已绑定的白名单: {', '.join(current_whitelists)}")

            # # 等待实例状态就绪
            # if not self.wait_for_instance_ready(instance_id):
            #     logger.error("等待实例就绪超时，无法绑定白名单")
            #     return False
            # # 创建并绑定白名单
            try:
                # 从配置文件创建所有白名单
                whitelist_ids = []
                for whitelist_item in self.whitelist_config['whitelists']:
                    success, whitelist_id = self.create_whitelist(whitelist_item)
                    if success and whitelist_id:
                        # 检查白名单是否已经绑定到实例
                        if whitelist_id in current_whitelists:
                            logger.info(f"白名单 {whitelist_item['name']} (ID: {whitelist_id}) 已绑定到实例 {instance_id}，跳过绑定")
                            continue
                        whitelist_ids.append(whitelist_id)
                    else:
                        logger.error(f"创建白名单 {whitelist_item['name']} 失败")
                        return False
                
                if not whitelist_ids:
                    logger.info("所有白名单已经绑定到实例，无需重复绑定")
                    return True

                # 只绑定未绑定的白名单到实例
                associate_request = self.api.AssociateAllowListRequest(
                    allow_list_ids=whitelist_ids,
                    instance_ids=[instance_id]
                )
                self.client_api.associate_allow_list(associate_request)
                logger.info(f"成功将 {len(whitelist_ids)} 个新白名单绑定到实例 {instance_id}")
                return True

            except ApiException as e:
                logger.error(f"绑定白名单时发生异常: {e}")
                return False

        except ApiException as e:
            logger.error(f"创建或绑定白名单时发生异常: {e}")
            return False
   