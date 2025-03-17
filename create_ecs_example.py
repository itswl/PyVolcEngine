#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
火山引擎ECS实例创建示例
此脚本演示如何使用火山引擎SDK创建ECS实例
"""

from __future__ import print_function
import logging
import sys
import volcenginesdkcore
import volcenginesdkecs
from volcenginesdkcore.rest import ApiException
from configs.api_config import api_config
from configs.ecs_config import ecs_configs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_instance_exists(api_instance, instance_name):
    """
    检查指定名称的ECS实例是否存在
    
    Args:
        api_instance: ECS API实例
        instance_name: 实例名称
    
    Returns:
        tuple: (是否存在, 实例ID)
    """
    try:
        # 构建查询请求
        request = volcenginesdkecs.DescribeInstancesRequest(
            instance_name=instance_name
        )
        
        # 发送查询请求
        response = api_instance.describe_instances(request)
        # print(response)
        # 检查响应中的实例列表
        if (response and 
            hasattr(response, 'instances')):
            for instance in response.instances:
                if instance.instance_name == instance_name:
                    logger.info(f"找到已存在的实例: {instance_name} (ID: {instance.instance_id})")
                    # 检查实例状态
                    logger.info(f"实例状态: {instance.status}")
                    return True, instance.instance_id
            
        logger.info(f"未找到名为 {instance_name} 的实例")
        return False, None
        
    except ApiException as e:
        logger.error(f"查询实例时发生API异常: {e}")
        return False, None
    except Exception as e:
        logger.error(f"查询实例时发生未知异常: {e}")
        return False, None

def create_instance(instance_config):
    """
    创建单个ECS实例
    
    Args:
        instance_config: ECS实例配置字典
    """
    try:
        # 初始化SDK配置
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        volcenginesdkcore.Configuration.set_default(configuration)

        # 创建API实例
        api_instance = volcenginesdkecs.ECSApi()
        
        # 检查实例是否已存在
        exists, existing_id = check_instance_exists(api_instance, instance_config['name'])
        if exists:
            logger.info(f"实例 {instance_config['name']} 已存在，跳过创建")
            return existing_id

        # 配置EIP（如果需要）
        eip_config = instance_config.get('eip')
        req_eip_address = None
        if eip_config:
            req_eip_address = volcenginesdkecs.EipAddressForRunInstancesInput(
                bandwidth_mbps=eip_config['bandwidth'],
                charge_type="PayByTraffic",  # 按流量计费
                isp="BGP",  # BGP线路
                release_with_instance=True
            )

        # 配置网络接口
        req_network_interfaces = volcenginesdkecs.NetworkInterfaceForRunInstancesInput(
            security_group_ids=instance_config['security_group_ids'],
            subnet_id=instance_config['subnet_id']
        )

        # 配置系统盘和数据盘
        volumes = []
        for volume_config in instance_config['volumes']:
            volume = volcenginesdkecs.VolumeForRunInstancesInput(
                delete_with_instance=volume_config['delete_with_instance'],
                size=volume_config['size'],
                volume_type=volume_config['volume_type']
            )
            volumes.append(volume)

        # 创建实例请求
        run_instances_request = volcenginesdkecs.RunInstancesRequest(
            dry_run=instance_config['dry_run'],
            install_run_command_agent=instance_config['install_run_command_agent'],
            credit_specification=instance_config['credit_specification'],
            instance_type_id=instance_config['instance_type'],
            image_id=instance_config['image_id'],
            instance_name=instance_config['name'],
            hostname=instance_config['hostname'],
            description=instance_config['description'],
            instance_charge_type=instance_config['instance_charge_type'],
            period=instance_config['period'],
            period_unit=instance_config['period_unit'],
            auto_renew=instance_config['auto_renew'],
            auto_renew_period=instance_config['auto_renew_period'],
            zone_id=instance_config['zone_id'],
            network_interfaces=[req_network_interfaces],
            volumes=volumes,
            password=instance_config['password'],
            user_data=instance_config['user_data'],
            eip_address=req_eip_address,
            count=1,
            min_count=1
        )

        # 发送创建请求
        response = api_instance.run_instances(run_instances_request)
        
        if (response and 
            hasattr(response, 'Result') and 
            hasattr(response.Result, 'InstanceIds')):
            instance_id = response.Result.InstanceIds[0]
            logger.info(f"成功创建ECS实例: {instance_id}")
            return instance_id
        else:
            logger.error("创建ECS实例失败: 响应结果为空")
            return None

    except ApiException as e:
        logger.error(f"创建ECS实例时发生API异常: {e}")
        return None
    except Exception as e:
        logger.error(f"创建ECS实例时发生未知异常: {e}")
        return None

def main():
    """
    主函数：创建ECS实例
    """
    logger.info("开始创建火山引擎ECS实例...")
    
    # 遍历配置文件中的所有实例配置
    for config_name, config in ecs_configs.items():
        logger.info(f"准备处理实例: {config_name}")
        instance_id = create_instance(config)
        
        if instance_id:
            logger.info(f"实例 {config_name} 处理完成，实例ID: {instance_id}")
        else:
            logger.error(f"实例 {config_name} 处理失败")
    
    logger.info("ECS实例创建流程完成")

if __name__ == "__main__":
    main()