#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Redis实例间数据传输任务示例

此示例展示如何使用RedisTransmissionManager创建和管理Redis实例之间的数据传输任务
支持全量数据同步和增量数据同步
"""

import time
import logging
import os
from redis2redis_transmission import RedisTransmissionManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_full_sync_task():
    """
    创建全量数据同步任务示例
    """
    # 初始化传输管理器
    transmission_manager = RedisTransmissionManager()
    
    # 配置全量同步任务
    full_sync_config = {
        'source_instance_id': 'redis-shzlgishb8lrrybgz',  # 源Redis实例ID
        'target_instance_id': 'redis-shzl379jcqo5w449a',  # 目标Redis实例ID
        'task_name': 'FullSyncTask-Production',  # 任务名称
        'description': '生产环境数据全量同步到灾备环境',  # 任务描述
        'transmission_type': 'FullSync',  # 传输类型：全量同步
        'conflict_policy': 'OverwriteTarget',  # 冲突策略：覆盖目标
        # 可选：指定要同步的数据库
        'database_whitelist': [0, 1, 2],  # 只同步DB 0, 1, 2
        # 可选：指定要同步的key模式
        'key_pattern_whitelist': ['user:*', 'order:*'],  # 只同步user:和order:开头的key
        # 可选：指定不同步的key模式
        'key_pattern_blacklist': ['temp:*', 'cache:*'],  # 不同步temp:和cache:开头的key
        # 可选：调度配置
        'schedule_config': {
            'start_time': '2023-06-01T02:00:00Z',  # 开始时间
            'recurrence': 'Once'  # 一次性任务
        }
    }
    
    # 创建传输任务
    task_id = transmission_manager.create_transmission_task(full_sync_config)
    
    if task_id:
        logger.info(f"全量同步任务创建成功，任务ID: {task_id}")
        
        # 启动任务
        if transmission_manager.start_transmission_task(task_id):
            logger.info(f"全量同步任务启动成功")
            
            # 监控任务进度
            monitor_task_progress(transmission_manager, task_id)
        else:
            logger.error("全量同步任务启动失败")
    else:
        logger.error("全量同步任务创建失败")

def create_incremental_sync_task():
    """
    创建增量数据同步任务示例
    """
    # 初始化传输管理器
    transmission_manager = RedisTransmissionManager()
    
    # 配置增量同步任务
    incremental_sync_config = {
        'source_instance_id': 'redis-cn-xxxxxxxx',  # 源Redis实例ID
        'target_instance_id': 'redis-cn-yyyyyyyy',  # 目标Redis实例ID
        'task_name': 'IncrementalSyncTask-Daily',  # 任务名称
        'description': '每日增量数据同步',  # 任务描述
        'transmission_type': 'IncrementalSync',  # 传输类型：增量同步
        'conflict_policy': 'SkipConflict',  # 冲突策略：跳过冲突
        # 可选：调度配置 - 每天凌晨2点执行
        'schedule_config': {
            'start_time': '2023-06-01T02:00:00Z',  # 开始时间
            'end_time': '2023-12-31T02:00:00Z',  # 结束时间
            'recurrence': 'Daily',  # 每天执行
            'recurrence_interval': 1  # 间隔1天
        }
    }
    
    # 创建传输任务
    task_id = transmission_manager.create_transmission_task(incremental_sync_config)
    
    if task_id:
        logger.info(f"增量同步任务创建成功，任务ID: {task_id}")
        
        # 启动任务
        if transmission_manager.start_transmission_task(task_id):
            logger.info(f"增量同步任务启动成功")
            
            # 监控任务进度
            monitor_task_progress(transmission_manager, task_id)
        else:
            logger.error("增量同步任务启动失败")
    else:
        logger.error("增量同步任务创建失败")

def create_weekly_sync_task():
    """
    创建每周执行的数据同步任务示例
    """
    # 初始化传输管理器
    transmission_manager = RedisTransmissionManager()
    
    # 配置每周同步任务
    weekly_sync_config = {
        'source_instance_id': 'redis-cn-xxxxxxxx',  # 源Redis实例ID
        'target_instance_id': 'redis-cn-yyyyyyyy',  # 目标Redis实例ID
        'task_name': 'WeeklySyncTask',  # 任务名称
        'description': '每周一、三、五同步数据',  # 任务描述
        'transmission_type': 'FullSync',  # 传输类型：全量同步
        'conflict_policy': 'OverwriteTarget',  # 冲突策略：覆盖目标
        # 调度配置 - 每周一、三、五执行
        'schedule_config': {
            'start_time': '2023-06-01T02:00:00Z',  # 开始时间
            'end_time': '2023-12-31T02:00:00Z',  # 结束时间
            'recurrence': 'Weekly',  # 每周执行
            'recurrence_interval': 1,  # 间隔1周
            'days_of_week': ['Monday', 'Wednesday', 'Friday']  # 周一、三、五执行
        }
    }
    
    # 创建传输任务
    task_id = transmission_manager.create_transmission_task(weekly_sync_config)
    
    if task_id:
        logger.info(f"每周同步任务创建成功，任务ID: {task_id}")
    else:
        logger.error("每周同步任务创建失败")

def monitor_task_progress(transmission_manager, task_id, check_interval=10, timeout=600):
    """
    监控任务进度
    
    Args:
        transmission_manager: 传输管理器实例
        task_id: 任务ID
        check_interval: 检查间隔（秒）
        timeout: 超时时间（秒）
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        # 获取任务详情
        task_info = transmission_manager.get_transmission_task(task_id)
        
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

def list_and_manage_tasks():
    """
    列出并管理现有的传输任务
    """
    # 初始化传输管理器
    transmission_manager = RedisTransmissionManager()
    
    # 列出所有传输任务
    tasks = transmission_manager.list_transmission_tasks()
    
    if not tasks:
        logger.info("没有找到任何传输任务")
        return
    
    logger.info(f"找到 {len(tasks)} 个传输任务:")
    
    for i, task in enumerate(tasks):
        logger.info(f"任务 {i+1}:")
        logger.info(f"  - 任务ID: {task['task_id']}")
        logger.info(f"  - 任务名称: {task['task_name']}")
        logger.info(f"  - 传输类型: {task['transmission_type']}")
        logger.info(f"  - 状态: {task['status']}")
        logger.info(f"  - 进度: {task['progress']}%")
        logger.info(f"  - 创建时间: {task['create_time']}")
        logger.info("")
    
    # 示例：停止第一个任务
    if tasks and tasks[0]['status'] == 'Running':
        task_id = tasks[0]['task_id']
        if transmission_manager.stop_transmission_task(task_id):
            logger.info(f"成功停止任务: {task_id}")
        else:
            logger.error(f"停止任务失败: {task_id}")
    
    # 示例：删除最后一个已完成的任务
    completed_tasks = [task for task in tasks if task['status'] == 'Completed']
    if completed_tasks:
        task_id = completed_tasks[-1]['task_id']
        if transmission_manager.delete_transmission_task(task_id):
            logger.info(f"成功删除任务: {task_id}")
        else:
            logger.error(f"删除任务失败: {task_id}")

def main():
    """
    主函数，演示不同类型的数据传输任务创建和管理
    """
    # 创建全量同步任务
    create_full_sync_task()
    
    # 创建增量同步任务
    create_incremental_sync_task()
    
    # 创建每周执行的同步任务
    create_weekly_sync_task()
    
    # 列出并管理现有任务
    list_and_manage_tasks()

if __name__ == "__main__":
    main()