#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用sign.py调用DTS服务的CreateTransmissionTask API示例
用于创建Redis实例间的数据迁移任务
"""

import os
import json
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
    
    # 构建API请求参数
    api_params = {
        "SrcConfig": {
            "EndpointType": "Volc_Redis",
            "VolcRedisSettings": {
                "DBInstanceId": "redis-shzlgishb8lrrybgz",
                "Username": "default",
                "RegionSettings": {
                    "Region": "cn-shanghai"
                },
                "Password": "ns2024Xqrif848"
            }
        },
        "DestConfig": {
            "EndpointType": "Volc_Redis",
            "VolcRedisSettings": {
                "DBInstanceId": "redis-shzl379jcqo5w449a",
                "Username": "default",
                "Password": "ns2024Xqrif848",
                "RegionSettings": {
                    "Region": "cn-shanghai"
                }
            }
        },
        "TaskName": "test",
        "TaskType": "DataMigration",
        "SolutionSettings": {
            "SolutionType": "Redis2Redis",
            "AutoStart": True,
            "Redis2RedisSettings": {
                "FullTransmissionSettings": {
                    "EnableFull": True
                },
                "ErrorBehaviorSettings": {
                    "MaxRetrySeconds": 600
                },
                "ObjectMappings": [
                    {
                        "DestObjName": "0",
                        "ObjectType": "Database",
                        "SrcObjName": "0"
                    }
                ]
            }
        },
        "ChargeConfig": {
            "ChargeType": "PostPaid",
            "OneStep": True
        }
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
            print(f"\n成功创建数据迁移任务，任务ID: {task_id}")
            
    except APIError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"发生异常: {e}")

def start_task(task_id):
    try:
        # 设置基本API参数
        os.environ['method'] = 'POST'
        os.environ['Service'] = 'dts'
        os.environ['Action'] = 'StartTransmissionTask'
        os.environ['Version'] = '2022-10-01'
        os.environ['Region'] = 'cn-shanghai'
        os.environ['ContentType'] = 'application/json'
        os.environ['Host'] = 'open.volcengineapi.com'
        
        # 构建API请求参数
        api_params = {
            "TaskId": task_id
        }
        
        # 将API参数转换为JSON字符串并设置到环境变量
        os.environ['API_PARAMS'] = json.dumps(api_params)
        
        # 创建API配置和客户端
        config = APIConfig()
        client = APIClient(config)
        
        # 发送请求
        print("正在启动数据迁移任务...")
        response = client.send_request()
        
        # 处理响应
        print("\n请求成功，响应内容:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        print(f"\n成功启动数据迁移任务: {task_id}")
        return True
        
    except APIError as e:
        print(f"错误: {e}")
        return False
    except Exception as e:
        print(f"发生异常: {e}")
        return False

if __name__ == "__main__":
    main()
    
    # 启动刚创建的任务
    task_id = "37965963ac5841e09553cf3183774f9e"
    start_task(task_id)