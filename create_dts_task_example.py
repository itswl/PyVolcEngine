#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Redis实例间数据传输任务示例 - 使用DTS服务API

此示例展示如何使用DTS服务API创建Redis实例之间的数据传输任务
包含完整的SrcConfig和DstConfig配置
"""

import os
import json
import time
import logging
from volcenginesdkcore import Configuration
from volcenginesdkcore.rest import ApiException
import volcenginesdkdts
from configs.api_config import api_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DTSManager:
    def __init__(self):
        self._init_client()
        self.api = volcenginesdkdts
        self.client_api = self.api.DTSApi()
        
    def _init_client(self):
        """初始化API客户端配置"""
        configuration = Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        Configuration.set_default(configuration)
    
    def create_transmission_task(self, task_config):
        """创建Redis实例间数据传输任务
        
        Args:
            task_config (dict): 传输任务配置
            
        Returns:
            str: 传输任务ID，如果创建失败则返回None
        """
        try:
            # 创建源配置对象
            src_config = self.api.SrcConfigForCreateTransmissionTaskInput(
                instance_id=task_config['source_instance_id'],
                instance_type="redis",  # 实例类型：redis
                region=task_config.get('source_region', api_config['region']),
                vpc_id=task_config.get('source_vpc_id', ''),
                ip=task_config.get('source_ip', ''),
                port=task_config.get('source_port', 6379),
                account=task_config.get('source_account', ''),
                password=task_config.get('source_password', ''),
                database=task_config.get('source_database', ''),
                subnet_id=task_config.get('source_subnet_id', '')
            )
            
            # 创建目标配置对象
            dst_config = self.api.DstConfigForCreateTransmissionTaskInput(
                instance_id=task_config['target_instance_id'],
                instance_type="redis",  # 实例类型：redis
                region=task_config.get('target_region', api_config['region']),
                vpc_id=task_config.get('target_vpc_id', ''),
                ip=task_config.get('target_ip', ''),
                port=task_config.get('target_port', 6379),
                account=task_config.get('target_account', ''),
                password=task_config.get('target_password', ''),
                database=task_config.get('target_database', ''),
                subnet_id=task_config.get('target_subnet_id', '')
            )
            
            # 创建数据传输任务请求
            request = self.api.CreateTransmissionTaskRequest(
                task_name=task_config['task_name'],
                description=task_config.get('description', ''),
                src_config=src_config,  # 源配置
                dst_config=dst_config,  # 目标配置
                transmission_type=task_config['transmission_type'],  # FullSync(全量同步) 或 IncrementalSync(增量同步)
                database_whitelist=task_config.get('database_whitelist', []),  # 要同步的数据库列表，为空表示全部同步
                database_blacklist=task_config.get('database_blacklist', []),  # 不同步的数据库列表
                key_pattern_whitelist=task_config.get('key_pattern_whitelist', []),  # 要同步的key模式列表
                key_pattern_blacklist=task_config.get('key_pattern_blacklist', []),  # 不同步的key模式列表
                conflict_policy=task_config.get('conflict_policy', 'OverwriteTarget')  # 冲突策略: OverwriteTarget(覆盖目标) 或 SkipConflict(跳过冲突)
            )
            
            # 发送请求创建传输任务
            response = self.client_api.create_transmission_task(request)
            logger.info(f"Redis数据传输任务创建成功: {response.task_id}")
            return response.task_id
            
        except ApiException as e:
            logger.error(f"创建Redis数据传输任务时发生异常: {e}")
            return None
    
    def start_transmission_task(self, task_id):
        """启动传输任务
        
        Args:
            task_id (str): 传输任务ID
            
        Returns:
            bool: 是否成功启动
        """
        try:
            request = self.api.StartTransmissionTaskRequest(
                task_id=task_id
            )
            
            self.client_api.start_transmission_task(request)
            logger.info(f"成功启动传输任务: {task_id}")
            return True
            
        except ApiException as e:
            logger.error(f"启动传输任务时发生异常: {e}")
            return False
    
    def get_transmission_task(self, task_id):
        """获取传输任务详情
        
        Args:
            task_id (str): 传输任务ID
            
        Returns:
            dict: 传输任务详情，如果查询失败则返回None
        """
        try:
            request = self.api.DescribeTransmissionTaskRequest(
                task_id=task_id
            )
            
            response = self.client_api.describe_transmission_task(request)
            
            # 将响应转换为字典格式
            task_info = {
                'task_id': response.task_id,
                'task_name': response.task_name,
                'description': response.description,
                'transmission_type': response.transmission_type,
                'status': response.status,
                'create_time': response.create_time,
                'update_time': response.update_time,
                'progress': response.progress
            }
            
            return task_info
            
        except ApiException as e:
            logger.error(f"获取传输任务详情时发生异常: {e}")
            return None

def create_full_sync_task():
    """创建全量数据同步任务示例"""
    # 初始化DTS管理器
    dts_manager = DTSManager()
    
    # 配置全量同步任务
    full_sync_config = {
        'source_instance_id': 'redis-xxxxxxxx',  # 源Redis实例ID
        'source_password': 'YourSourcePassword',  # 源Redis密码
        'target_instance_id': 'redis-yyyyyyyy',  # 目标Redis实例ID
        'target_password': 'YourTargetPassword',  # 目标Redis密码
        'task_name': 'FullSyncTask-Production',  # 任务名称
        'description': '生产环境数据全量同步到灾备环境',  # 任务描述
        'transmission_type': 'FullSync',  # 传输类型：全量同步
        'conflict_policy': 'OverwriteTarget',  # 冲突策略：覆盖目标
        # 可选：指定要同步的数据库
        'database_whitelist': [0, 1, 2],  # 只同步DB 0, 1, 2
        # 可选：指定要同步的key模式
        'key_pattern_whitelist': ['user:*', 'order:*'],  # 只同步user:和order:开头的key
        # 可选：指定不同步的key模式
        'key_pattern_blacklist': ['temp:*', 'cache:*']  # 不同步temp:和cache:开头的key
    }
    
    # 创建传输任务
    task_id = dts_manager.create_transmission_task(full_sync_config)
    
    if task_id:
        logger.info(f"全量同步任务创建成功，任务ID: {task_id}")
        
        # 启动任务
        if dts_manager.start_transmission_task(task_id):
            logger.info(f"全量同步任务启动成功")
            
            # 监控任务进度
            monitor_task_progress(dts_manager, task_id)
        else:
            logger.error("全量同步任务启动失败")
    else:
        logger.error("全量同步任务创建失败")

def create_incremental_sync_task():
    """创建增量数据同步任务示例"""
    # 初始化DTS管理器
    dts_manager = DTSManager()
    
    # 配置增量同步任务
    incremental_sync_config = {
        'source_instance_id': 'redis-xxxxxxxx',  # 源Redis实例ID
        'source_password': 'YourSourcePassword',  # 源Redis密码
        'source_vpc_id': 'vpc-xxxxxxxx',  # 源Redis所在VPC ID
        'target_instance_id': 'redis-yyyyyyyy',  # 目标Redis实例ID
        'target_password': 'YourTargetPassword',  # 目标Redis密码
        'target_vpc_id': 'vpc-yyyyyyyy',  # 目标Redis所在VPC ID
        'task_name': 'IncrementalSyncTask-Daily',  # 任务名称
        'description': '每日增量数据同步',  # 任务描述
        'transmission_type': 'IncrementalSync',  # 传输类型：增量同步
        'conflict_policy': 'SkipConflict'  # 冲突策略：跳过冲突
    }
    
    # 创建传输任务
    task_id = dts_manager.create_transmission_task(incremental_sync_config)
    
    if task_id:
        logger.info(f"增量同步任务创建成功，任务ID: {task_id}")
        
        # 启动任务
        if dts_manager.start_transmission_task(task_id):
            logger.info(f"增量同步任务启动成功")
            
            # 监控任务进度
            monitor_task_progress(dts_manager, task_id)
        else:
            logger.error("增量同步任务启动失败")
    else:
        logger.error("增量同步任务创建失败")

def monitor_task_progress(dts_manager, task_id, check_interval=10, timeout=600):
    """监控任务进度
    
    Args:
        dts_manager: DTS管理器实例
        task_id: 任务ID
        check_interval: 检查间隔（秒）
        timeout: 超时时间（秒）
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        # 获取任务详情
        task_info = dts_manager.get_transmission_task(task_id)
        
        if not task_info:
            logger.error(f"获取任务信息失败，任务ID: {task_id}")
            return
        
        # 打印任务状态和进度
        logger.info(f"任务状态: {task_info['status']}, 进度: {task_info['progress']}%")
        
        # 如果任务已完成或失败，退出循环
        if task_info['status'] in ['Completed', 'Failed', 'Stopped']:
            if task_info['status'] == 'Completed':
                logger.info(f"任务已完成，任务ID: {task_id}")
            elif task_info['status'] == 'Failed':
                logger.error(f"任务执行失败，任务ID: {task_id}")
            else:
                logger.warning(f"任务已停止，任务ID: {task_id}")
            return
        
        # 等待一段时间后再次检查
        time.sleep(check_interval)
    
    # 超时处理
    logger.warning(f"监控任务超时，任务ID: {task_id}")

if __name__ == "__main__":
    # 创建全量同步任务示例
    create_full_sync_task()
    
    # 创建增量同步任务示例
    # create_incremental_sync_task()