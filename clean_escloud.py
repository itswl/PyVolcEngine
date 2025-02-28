#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import argparse
import logging
import os
import sys
from escloud_manager import ESCloudManager

# 配置日志记录
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(log_dir, 'escloud_cleaner.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


def list_instances():
    """列出所有ESCloud实例"""
    try:
        manager = ESCloudManager()
        request = manager.api.DescribeInstancesRequest()
        response = manager.client_api.describe_instances(request)
        
        if not hasattr(response, 'instances') or not response.instances:
            logger.info("未找到任何ESCloud实例")
            print("未找到任何ESCloud实例")
            return
        
        print("\n当前ESCloud实例列表:")
        print("-" * 80)
        print(f"{'实例ID':<20} {'实例名称':<30} {'状态':<15} {'版本':<15}")
        print("-" * 80)
        
        for instance in response.instances:
            print(f"{instance.instance_id:<20} {instance.instance_configuration.instance_name:<30} {instance.status:<15} {instance.instance_configuration.version:<15}")
        
        print("-" * 80)
        return response.instances
    except Exception as e:
        logger.error(f"获取实例列表时发生错误: {e}")
        print(f"获取实例列表时发生错误: {e}")
        return None


def delete_instance(instance_id, force=False):
    """删除指定的ESCloud实例"""
    try:
        manager = ESCloudManager()
        
        # 获取实例详情，确认实例存在
        instance_detail = manager.get_instance_detail(instance_id)
        if not instance_detail or not hasattr(instance_detail, 'instances') or not instance_detail.instances:
            logger.error(f"实例 {instance_id} 不存在")
            print(f"实例 {instance_id} 不存在")
            return False
        
        # 找到匹配的实例
        target_instance = None
        for instance in instance_detail.instances:
            if instance.instance_id == instance_id:
                target_instance = instance
                break
        
        if not target_instance:
            logger.error(f"实例 {instance_id} 不存在")
            print(f"实例 {instance_id} 不存在")
            return False
        
        # 确认删除
        if not force:
            confirm = input(f"确认要删除实例 {instance_id} ({target_instance.instance_configuration.instance_name})? [y/N]: ")
            if confirm.lower() != 'y':
                print("操作已取消")
                return False
        
        # 先禁用删除保护
        logger.info(f"正在禁用实例 {instance_id} 的删除保护...")
        if not manager.deletion_protection(instance_id, deletion_protection=False):
            logger.error(f"禁用实例 {instance_id} 的删除保护失败")
            print(f"禁用实例 {instance_id} 的删除保护失败")
            return False
        
        # 释放实例
        logger.info(f"正在释放实例 {instance_id}...")
        if manager.release_instance(instance_id):
            logger.info(f"实例 {instance_id} 释放请求已发送")
            print(f"实例 {instance_id} 释放请求已发送")
            return True
        else:
            logger.error(f"释放实例 {instance_id} 失败")
            print(f"释放实例 {instance_id} 失败")
            return False
            
    except Exception as e:
        logger.error(f"删除实例时发生错误: {e}")
        print(f"删除实例时发生错误: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='ESCloud实例清理工具')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有ESCloud实例')
    parser.add_argument('-d', '--delete', metavar='INSTANCE_ID', help='删除指定的ESCloud实例')
    parser.add_argument('-f', '--force', action='store_true', help='强制删除，不提示确认')
    
    args = parser.parse_args()
    
    if args.list:
        list_instances()
    elif args.delete:
        delete_instance(args.delete, args.force)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()