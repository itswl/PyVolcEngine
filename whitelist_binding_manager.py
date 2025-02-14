import time
from volcenginesdkcore.rest import ApiException
from volcenginesdkrdspostgresql import RDSPOSTGRESQLApi
import volcenginesdkrdspostgresql
from whitelist_manager import WhitelistManager
from configs.api_config import api_config
import logging

logger = logging.getLogger(__name__)

class WhitelistBindingManager:
    def __init__(self):
        self.pg_api = RDSPOSTGRESQLApi()

    def bind_whitelists_to_instance(self, instance_id):
        """
        将白名单绑定到指定的实例
        :param instance_id: 数据库实例ID
        :return: bool 是否成功
        """
        try:
            # 创建白名单管理器
            whitelist_manager = WhitelistManager()
            whitelist_ids = whitelist_manager.create_all_whitelists()
            
            # 检查每个白名单的详细信息，查看是否已绑定到当前实例
            bound_whitelist_ids = set()
            for whitelist_id in whitelist_ids.values():
                try:
                    detail_request = volcenginesdkrdspostgresql.DescribeAllowListDetailRequest(
                        allow_list_id=whitelist_id
                    )
                    detail_response = self.pg_api.describe_allow_list_detail(detail_request)
                    
                    # 检查白名单是否已绑定到当前实例
                    if hasattr(detail_response, 'associated_instances'):
                        for instance in detail_response.associated_instances:
                            if instance.instance_id == instance_id:
                                bound_whitelist_ids.add(whitelist_id)
                                logger.info(f"白名单 {whitelist_id} 已绑定到实例 {instance_id}")
                                break
                except ApiException as e:
                    logger.warning(f"获取白名单 {whitelist_id} 详细信息时发生异常: {e}")
                    continue
                    
            # 过滤出未绑定的白名单ID
            unbound_whitelist_ids = {wid for wid in whitelist_ids.values() if wid not in bound_whitelist_ids}
            
            if not unbound_whitelist_ids:
                logger.info("所有白名单已经绑定到实例，无需重复绑定")
                return True
            
            # 等待实例状态就绪
            max_retries = 10
            retry_interval = 30
            for retry in range(max_retries):
                describe_request = volcenginesdkrdspostgresql.DescribeDBInstancesRequest()
                describe_response = self.pg_api.describe_db_instances(describe_request)
                
                instance_ready = False
                for instance in describe_response.instances:
                    if instance.instance_id == instance_id:
                        logger.info(f"当前实例状态: {instance.instance_status}")
                        if instance.instance_status == "Running":
                            instance_ready = True
                            break
                        elif instance.instance_status == "AllowListMaintaining":
                            logger.info("实例正在进行白名单维护，等待...")
                            break
                
                if instance_ready:
                    # 绑定所有创建的白名单
                    for whitelist_id in whitelist_ids.values():
                        # 每次绑定前再次检查实例状态
                        status_request = volcenginesdkrdspostgresql.DescribeDBInstancesRequest()
                        status_response = self.pg_api.describe_db_instances(status_request)
                        
                        instance_status = None
                        for instance in status_response.instances:
                            if instance.instance_id == instance_id:
                                instance_status = instance.instance_status
                                break
                        
                        if instance_status != "Running":
                            logger.warning(f"实例状态不是Running（当前状态: {instance_status}），等待30秒后重试...")
                            time.sleep(30)
                            continue
                            
                        associate_request = volcenginesdkrdspostgresql.AssociateAllowListRequest(
                            allow_list_ids=[whitelist_id],
                            instance_ids=[instance_id]
                        )
                        self.pg_api.associate_allow_list(associate_request)
                        logger.info(f"白名单 ID: {whitelist_id} 绑定成功")
                        
                        # 每次绑定后等待10秒，让实例有时间处理
                        time.sleep(10)
                    return True
                    
                if retry < max_retries - 1:
                    logger.info(f"等待{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                else:
                    logger.error("等待实例就绪超时，无法绑定白名单")
                    return False
            
            return True
            
        except ApiException as e:
            logger.error(f"创建或绑定白名单时发生异常: {e}")
            return False