import time
import logging
from volcenginesdkcore.rest import ApiException

logger = logging.getLogger(__name__)

class InstanceStatusChecker:
    @staticmethod
    def wait_for_instance_status(api_client, instance_id, target_status="Running", timeout=1800, interval=30,
                                status_check_func=None, instance_id_field="instance_id", status_field="status"):
        """
        通用的实例状态检查函数
        
        Args:
            api_client: API客户端实例
            instance_id (str): 实例ID
            target_status (str): 目标状态，默认为"Running"
            timeout (int): 超时时间（秒），默认1800秒
            interval (int): 检查间隔（秒），默认30秒
            status_check_func: 自定义状态检查函数，用于处理不同服务的状态检查逻辑
            instance_id_field (str): 实例ID字段名，默认为"instance_id"
            status_field (str): 状态字段名，默认为"status"
            
        Returns:
            bool: 是否达到目标状态
        """
        start_time = time.time()
        while True:
            try:
                if status_check_func:
                    # 使用自定义状态检查函数
                    current_status = status_check_func(api_client, instance_id)
                else:
                    # 默认状态检查逻辑
                    body = {
                        "instance_ids": [instance_id]
                    }
                    response = api_client.describe_db_instances(body=body)
                    current_status = None
                    # 直接访问字典结构
                    if isinstance(response, dict):
                        if 'Result' in response and 'Instances' in response['Result']:
                            for instance in response['Result']['Instances']:
                                if instance.get(instance_id_field) == instance_id:
                                    current_status = instance.get(status_field)
                                    break
                        elif 'Instances' in response:
                            for instance in response['Instances']:
                                if instance.get(instance_id_field) == instance_id:
                                    current_status = instance.get(status_field)
                                    break
                
                if current_status == target_status:
                    logger.info(f"实例 {instance_id} 已达到目标状态: {target_status}")
                    return True
                    
                logger.info(f"实例 {instance_id} 当前状态: {current_status}，等待 {interval} 秒后重试...")
                
                if time.time() - start_time > timeout:
                    logger.error(f"等待实例 {instance_id} 状态超时，已等待 {timeout} 秒")
                    return False
                    
                time.sleep(interval)
                
            except ApiException as e:
                logger.error(f"检查实例 {instance_id} 状态时发生错误: {e}")
                return False