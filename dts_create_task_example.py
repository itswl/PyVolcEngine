#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用sign.py调用DTS服务的CreateTransmissionTask API示例

此示例展示如何使用sign.py中的签名功能正确调用DTS服务的CreateTransmissionTask API
包含完整的SrcConfig和DstConfig配置
"""

import os
import json
import sys
from sign import APIConfig, APIClient, APIError

# 设置环境变量
def set_env_vars():
    # 设置基本API参数
    os.environ['method'] = 'POST'
    os.environ['Service'] = 'dts'
    os.environ['Action'] = 'CreateTransmissionTask'
    os.environ['Version'] = '2022-10-01'
    os.environ['Region'] = 'cn-shanghai'
    os.environ['ContentType'] = 'application/json'
    os.environ['Host'] = 'open.volcengineapi.com'
    
    # 请替换为您的实际访问密钥
    # os.environ['volcAK'] = 'YOUR_ACCESS_KEY_ID'
    # os.environ['volcSK'] = 'YOUR_SECRET_ACCESS_KEY'
    
    # 构建API请求参数
    api_params = {
        # 任务名称
        "TaskName": "Redis-Data-Sync-Example",
        
        # 任务描述
        "Description": "Redis实例间数据同步示例",
        
        # 源配置 - 这是必需的参数
        "SrcConfig": {
            "InstanceId": "redis-xxxxxxxx",  # 源Redis实例ID
            "InstanceType": "redis",         # 实例类型：redis
            "Region": "cn-shanghai",         # 区域
            "VpcId": "vpc-xxxxxxxx",        # VPC ID
            "Password": "YourSourcePassword", # Redis密码
            "Port": 6379                     # Redis端口
        },
        
        # 目标配置 - 这是必需的参数
        "DstConfig": {
            "InstanceId": "redis-yyyyyyyy",  # 目标Redis实例ID
            "InstanceType": "redis",         # 实例类型：redis
            "Region": "cn-shanghai",         # 区域
            "VpcId": "vpc-yyyyyyyy",        # VPC ID
            "Password": "YourTargetPassword", # Redis密码
            "Port": 6379                     # Redis端口
        },
        
        # 传输类型：FullSync(全量同步) 或 IncrementalSync(增量同步)
        "TransmissionType": "FullSync",
        
        # 冲突策略: OverwriteTarget(覆盖目标) 或 SkipConflict(跳过冲突)
        "ConflictPolicy": "OverwriteTarget",
        
        # 可选：指定要同步的数据库列表，为空表示全部同步
        "DatabaseWhitelist": [0, 1, 2],
        
        # 可选：指定不同步的数据库列表
        "DatabaseBlacklist": [],
        
        # 可选：指定要同步的key模式列表
        "KeyPatternWhitelist": ["user:*", "order:*"],
        
        # 可选：指定不同步的key模式列表
        "KeyPatternBlacklist": ["temp:*", "cache:*"]
    }
    
    # 将API参数转换为JSON字符串并设置到环境变量
    os.environ['API_PARAMS'] = json.dumps(api_params)

def main():
    try:
        # 设置环境变量
        set_env_vars()
        
        # 创建API配置和客户端
        config = APIConfig()
        client = APIClient(config)
        
        # 发送请求
        print("正在发送CreateTransmissionTask请求...")
        response = client.send_request()
        
        # 处理响应
        print("\n请求成功，响应内容:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 如果成功创建任务，打印任务ID
        if 'Result' in response and 'TaskId' in response['Result']:
            task_id = response['Result']['TaskId']
            print(f"\n成功创建传输任务，任务ID: {task_id}")
            print("\n您可以使用以下命令启动此任务:")
            print(f"export method='POST'")
            print(f"export Service='dts'")
            print(f"export Action='StartTransmissionTask'")
            print(f"export Version='2022-10-01'")
            print(f"export API_PARAMS='{{\"TaskId\": \"{task_id}\"}}'") 
            print("python sign.py")
        
    except APIError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"发生异常: {e}")

if __name__ == "__main__":
    main()