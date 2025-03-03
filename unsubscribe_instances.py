#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import logging
import os
import sys
import volcenginesdkcore
import volcenginesdkbilling
from volcenginesdkcore.rest import ApiException
from configs.api_config import api_config

# 配置日志记录
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(log_dir, 'unsubscribe_escloud.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
'''
veDB for DocumentDB
Message_Queue_for_Kafka
ESCloud
'''

def unsubscribe_instance(instance_id, product="ESCloud", force=False):
    """退订指定的实例
    Args:
        instance_id: 实例ID
        product: 产品类型，如ESCloud、Message_Queue_for_Kafka等
        force: 是否强制退订，不提示确认
    Returns:
        bool: 退订是否成功
    """
    try:
        # 初始化配置
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        volcenginesdkcore.Configuration.set_default(configuration)

        # 确认退订
        if not force:
            confirm = input(f"确认要退订{product}实例 {instance_id}? [y/N]: ")
            if confirm.lower() != 'y':
                print("操作已取消")
                return False

        # 创建退订请求
        api_instance = volcenginesdkbilling.BILLINGApi()
        unsubscribe_request = volcenginesdkbilling.UnsubscribeInstanceRequest(
            instance_id=instance_id,
            product=product
        )

        # 发送退订请求
        api_instance.unsubscribe_instance(unsubscribe_request)
        logger.info(f"{product}实例 {instance_id} 退订请求已发送")
        print(f"{product}实例 {instance_id} 退订请求已发送")
        return True

    except ApiException as e:
        error_message = f"退订{product}实例时发生错误: {e}"
        logger.error(error_message)
        print(error_message)
        return False


def main():
    print('请谨慎操作!')
    print('请谨慎操作!!')
    print('请谨慎操作!!!')
    print('请先调用 list_resources.py 获取实例信息')
    print('请先调用 list_resources.py 获取实例信息')
    print('请先调用 list_resources.py 获取实例信息')
    parser = argparse.ArgumentParser(description='实例退订工具')
    parser.add_argument('-i', '--instance-id', required=True, help='要退订的实例ID')
    parser.add_argument('-p', '--product', default='ESCloud', choices=['ESCloud', 'Message_Queue_for_Kafka', 'veDB for DocumentDB', 'RDS for PostgreSQL', 'veDB_for_Redis'],
                        help='产品类型 (默认: ESCloud)')
    parser.add_argument('-f', '--force', action='store_true', help='强制退订，不提示确认')

    args = parser.parse_args()
    unsubscribe_instance(args.instance_id, args.product, args.force)


if __name__ == '__main__':
    main()