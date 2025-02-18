# coding: utf-8

from __future__ import absolute_import

from volcenginesdkcore.configuration import Configuration
from volcenginesdkcore.rest import ApiException
from configs.api_config import api_config
import logging

logger = logging.getLogger(__name__)

class WhitelistBaseManager:
    """白名单管理基类，提供通用的白名单处理逻辑

    这个基类实现了白名单管理的基本功能，包括：
    - 客户端初始化
    - 白名单创建
    - 白名单绑定
    - 白名单查询
    
    子类需要实现具体的API调用方法。
    """

    def __init__(self):
        self._init_client()
        self.api = None  # 子类需要设置具体的API实例
        
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
            create_response = self.api.create_allow_list(create_request)
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

    def bind_whitelist_to_instance(self, instance_id, whitelist_id):
        """将白名单绑定到实例

        :param instance_id: 实例ID
        :param whitelist_id: 白名单ID
        :return: bool 绑定是否成功
        """
        try:
            # 等待实例就绪
            if not self.wait_for_instance_ready(instance_id):
                return False

            # 检查白名单是否已绑定
            current_whitelists = self.get_instance_whitelists(instance_id)
            if whitelist_id in current_whitelists:
                logger.info(f"白名单 {whitelist_id} 已绑定到实例 {instance_id}")
                return True

            # 绑定白名单
            associate_request = self.api.AssociateAllowListRequest(
                allow_list_ids=[whitelist_id],
                instance_ids=[instance_id]
            )
            self.client_api.associate_allow_list(associate_request)
            logger.info(f"白名单 {whitelist_id} 已成功绑定到实例 {instance_id}")
            return True
        except ApiException as e:
            return self._handle_api_exception(e, f"绑定白名单到实例")

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
                
                for instance in status_response.instances:
                    if instance.instance_id == instance_id:
                        if instance.status == "Running":
                            logger.info(f"实例 {instance_id} 状态正常")
                            return True
                        else:
                            logger.info(f"实例 {instance_id} 当前状态: {instance.status}，等待 {interval} 秒后重试")
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