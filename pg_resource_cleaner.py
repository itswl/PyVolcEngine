import time
import logging
import volcenginesdkcore
from volcenginesdkcore.rest import ApiException
import volcenginesdkrdspostgresql
from configs.api_config import api_config
import volcenginesdkvpc

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
file_handler = logging.FileHandler(os.path.join(log_dir, 'pg_resource_cleaner.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


class ResourceCleaner:
    def __init__(self):
        self._init_client()
        self.pg_api = volcenginesdkrdspostgresql.RDSPOSTGRESQLApi()

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)

    def disassociate_whitelist(self, instance_id):
        """
        解绑与指定实例关联的所有白名单
        :param instance_id: 数据库实例ID
        :return: bool 操作是否成功
        """
        try:
            # 先检查实例状态
            describe_request = volcenginesdkrdspostgresql.DescribeDBInstancesRequest()
            describe_response = self.pg_api.describe_db_instances(describe_request)
            
            instance_ready = False
            for instance in describe_response.instances:
                if instance.instance_id == instance_id:
                    if instance.instance_status == "Running":
                        instance_ready = True
                        break
                    else:
                        logger.warning(f"实例 {instance_id} 当前状态为 {instance.instance_status}，不适合执行解绑操作")
                        return False
            
            if not instance_ready:
                logger.error(f"未找到实例 {instance_id} 或实例状态不正确")
                return False

            # 获取实例关联的所有白名单
            list_request = volcenginesdkrdspostgresql.DescribeAllowListsRequest(
                region_id=api_config['region']
            )
            list_response = self.pg_api.describe_allow_lists(list_request)
            
            if not hasattr(list_response, 'allow_lists'):
                logger.info(f"实例 {instance_id} 没有关联的白名单")
                return True

            # 遍历所有白名单，检查是否与实例关联
            for allow_list in list_response.allow_lists:
                try:
                    # 获取白名单详情
                    detail_request = volcenginesdkrdspostgresql.DescribeAllowListDetailRequest(
                        allow_list_id=allow_list.allow_list_id
                    )
                    detail_response = self.pg_api.describe_allow_list_detail(detail_request)
                    
                    # 检查是否与当前实例关联
                    if hasattr(detail_response, 'associated_instances'):
                        is_associated = any(instance.instance_id == instance_id 
                                          for instance in detail_response.associated_instances)
                        
                        if is_associated:
                            # 解绑白名单
                            disassociate_request = volcenginesdkrdspostgresql.DisassociateAllowListRequest(
                                allow_list_ids=[allow_list.allow_list_id],
                                instance_ids=[instance_id]
                            )
                            self.pg_api.disassociate_allow_list(disassociate_request)
                            logger.info(f"已解绑白名单 {allow_list.allow_list_name} (ID: {allow_list.allow_list_id})")
                            
                            # 验证解绑是否成功
                            time.sleep(5)  # 等待解绑操作生效
                            verify_request = volcenginesdkrdspostgresql.DescribeAllowListDetailRequest(
                                allow_list_id=allow_list.allow_list_id
                            )
                            verify_response = self.pg_api.describe_allow_list_detail(verify_request)
                            
                            if hasattr(verify_response, 'associated_instances'):
                                still_associated = any(instance.instance_id == instance_id 
                                                     for instance in verify_response.associated_instances)
                                if still_associated:
                                    logger.error(f"白名单 {allow_list.allow_list_name} 解绑失败，仍然与实例关联")
                                    return False
                            
                except ApiException as e:
                    logger.error(f"处理白名单 {allow_list.allow_list_id} 时发生错误: {e}")
                    continue

            return True

        except ApiException as e:
            logger.error(f"解绑白名单时发生错误: {e}")
            return False

    def release_eip(self, eip_address):
        """
        释放指定的EIP资源
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
                                return False
                        break
            
            if not allocation_id:
                logger.error(f"未找到EIP地址 {eip_address} 对应的allocation_id")
                return False
            
            # 创建释放请求
            release_request = volcenginesdkvpc.ReleaseEipAddressRequest(
                allocation_id=allocation_id
            )
            
            # 执行释放操作
            vpc_api.release_eip_address(release_request)
            logger.info(f"已成功释放EIP: {eip_address}")
            return True
            
        except ApiException as e:
            logger.error(f"释放EIP时发生错误: {e}")
            return False

    def delete_pg_instance(self, instance_id):
        """
        删除PostgreSQL实例
        :param instance_id: 实例ID
        :return: bool 操作是否成功
        """
        try:
            # 删除实例
            delete_request = volcenginesdkrdspostgresql.DeleteDBInstanceRequest(
                instance_id=instance_id
            )
            self.pg_api.delete_db_instance(delete_request)
            logger.info(f"已成功删除数据库实例 {instance_id}")
            return True

        except ApiException as e:
            logger.error(f"删除数据库实例时发生错误: {e}")
            return False

    def clean_all_resources(self, instance_id, eip_address=None):
        """
        清理所有相关资源
        :param instance_id: 数据库实例ID
        :param eip_address: 可选，EIP地址
        :return: bool 所有清理操作是否成功
        """
        success = True

        # 1. 首先解绑白名单
        if not self.disassociate_whitelist(instance_id):
            logger.error("白名单解绑失败")
            success = False

        # 2. 如果提供了EIP地址，释放EIP
        if eip_address and not self.release_eip(eip_address):
            logger.error("EIP释放失败")
            success = False

        # 3. 最后删除数据库实例
        if not self.delete_pg_instance(instance_id):
            logger.error("数据库实例删除失败")
            success = False

        return success

def main():
    try:
        # 创建资源清理器实例
        cleaner = ResourceCleaner()
        
        # 示例：清理特定实例的所有资源
        instance_id = "postgres-bdf6d0a49ef2"  # 替换为实际的实例ID
        eip_address = "14.103.150.142"  # 替换为实际的EIP地址
        
        if cleaner.clean_all_resources(instance_id, eip_address):
            logger.info("所有资源清理完成！")
        else:
            logger.warning("部分资源清理失败，请检查日志获取详细信息")
            
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        return

if __name__ == "__main__":
    main()