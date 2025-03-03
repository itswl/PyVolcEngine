# coding: utf-8
from __future__ import absolute_import
import resource_manager
import logging

# 配置日志记录
logger = logging.getLogger(__name__)

def list_kafka_resource(page_number=1, page_size=100):
    """列出所有Kafka资源"""
    kafka_resource = resource_manager.KafkaResource()
    kafka_resource_result = kafka_resource.list_instances(page_number=1, page_size=100)
    if not kafka_resource_result:
        print("未找到任何Kafka实例")
        return
    
    print("\nKafka实例列表:")
    print("-" * 120)
    print(f"{'实例ID':<20} {'实例名称':<20} {'状态':<12} {'VPC ID':<20} {'公网IP':<15} {'EIP ID':<36} {'引擎版本':<10} {'创建时间':<25}")
    print("-" * 120)
    
    for instance in kafka_resource_result:
        # 直接从字典中获取属性
        instance_id = instance['instance_id']
        instance_name = instance['instance_name']
        status = instance['status']
        vpc_id = instance.get('vpc_id', 'N/A')
        version = instance.get('version', 'N/A')
        create_time = instance.get('create_time', 'N/A')
        
        # 获取公网IP
        public_ip = instance.get('public_ip', 'N/A')
        eip_id = instance.get('eip_id', 'N/A')
        
        print(f"{instance_id:<20} {instance_name:<20} {status:<12} {vpc_id:<20} {public_ip:<15} {eip_id:<36} {version:<10} {create_time:<25}")
    
    print("-" * 120)
    print("注意: 如需查看更详细信息，请使用get_instance_detail方法获取实例详情")

def list_pg_resource():
    """列出所有PostgreSQL资源"""
    pg_resource = resource_manager.PostgreSQLResource()
    pg_resource_result = pg_resource.list_instances()
    if not pg_resource_result:
        print("未找到任何PostgreSQL实例")
        return
    
    print("\nPostgreSQL实例列表:")
    print("-" * 120)
    print(f"{'实例ID':<20} {'实例名称':<20} {'状态':<12} {'VPC ID':<20} {'公网IP':<15} {'EIP ID':<36} {'引擎版本':<10} {'创建时间':<25}")
    print("-" * 120)
    
    for instance in pg_resource_result:
        # 获取基本属性
        instance_id = instance.get('instance_id', 'N/A')
        instance_name = instance.get('instance_name', 'N/A')
        status = instance.get('status', 'N/A')
        vpc_id = instance.get('vpc_id', 'N/A')
        db_engine_version = instance.get('db_engine_version', 'N/A')
        create_time = instance.get('create_time', 'N/A')
        
        # 获取公网IP和EIP ID
        public_ip = instance.get('public_ip', 'N/A')
        eip_id = instance.get('eip_id', 'N/A')
        
        print(f"{instance_id:<20} {instance_name:<20} {status:<12} {vpc_id:<20} {public_ip:<15} {eip_id:<36} {db_engine_version:<10} {create_time:<25}")
    
    print("-" * 120)
    print("注意: 如需查看更详细信息，请使用list_instances方法获取实例详情")

def list_redis_resource():
    """列出所有Redis资源"""
    redis_resource = resource_manager.RedisResource()
    redis_resource_result = redis_resource.get_instance_detail()
    if not redis_resource_result:
        print("未找到任何Redis实例")
        return
    
    print("\nRedis实例列表:")
    print("-" * 120)
    print(f"{'实例ID':<20} {'实例名称':<20} {'状态':<12} {'VPC ID':<20} {'公网IP':<15} {'EIP ID':<36} {'引擎版本':<10} {'创建时间':<25}")
    print("-" * 120)
    
    for instance in redis_resource_result:
        # 获取基本属性
        instance_id = getattr(instance, 'instance_id', 'N/A')
        instance_name = getattr(instance, 'instance_name', 'N/A')
        status = getattr(instance, 'status', 'N/A')
        vpc_id = getattr(instance, 'vpc_id', 'N/A')
        engine_version = getattr(instance, 'engine_version', 'N/A')
        create_time = getattr(instance, 'create_time', 'N/A')
        
        # 获取公网IP和EIP ID
        public_ip = 'N/A'
        eip_id = 'N/A'
        if hasattr(instance, 'visit_addrs'):
            for addr in instance.visit_addrs:
                if getattr(addr, 'addr_type', '') == 'Public':
                    public_ip = getattr(addr, 'vip', 'N/A')
                    eip_id = getattr(addr, 'eip_id', 'N/A')
                    break
        
        print(f"{instance_id:<20} {instance_name:<20} {status:<12} {vpc_id:<20} {public_ip:<15} {eip_id:<36} {engine_version:<10} {create_time:<25}")
    
    print("-" * 120)
    print("注意: 如需查看更详细信息，请使用get_instance_detail方法获取实例详情")

def list_mongodb_resource():
    """列出所有MongoDB资源"""
    mongodb_resource = resource_manager.MongoDbResource()
    mongodb_resource_result = mongodb_resource.get_instance_detail()
    if not mongodb_resource_result:
        print("未找到任何MongoDB实例")
        return
    
    print("\nMongoDB实例列表:")
    print("-" * 120)
    print(f"{'实例ID':<20} {'实例名称':<20} {'状态':<12} {'VPC ID':<20} {'公网IP':<15} {'EIP ID':<36} {'引擎版本':<10} {'创建时间':<25}")
    print("-" * 120)
    
    for instance_detail in mongodb_resource_result:
        # MongoDB实例数据结构与Redis不同，需要从db_instance字段获取信息
        if hasattr(instance_detail, 'db_instance'):
            instance = instance_detail.db_instance
            
            # 获取基本属性
            instance_id = getattr(instance, 'instance_id', 'N/A')
            instance_name = getattr(instance, 'instance_name', 'N/A')
            status = getattr(instance, 'instance_status', 'N/A')
            vpc_id = getattr(instance, 'vpc_id', 'N/A')
            engine_version = getattr(instance, 'db_engine_version_str', 'N/A')
            create_time = getattr(instance, 'create_time', 'N/A')
            
            # MongoDB可能没有公网访问信息，或者结构不同
            public_ip = 'N/A'
            eip_id = 'N/A'
            
            print(f"{instance_id:<20} {instance_name:<20} {status:<12} {vpc_id:<20} {public_ip:<15} {eip_id:<36} {engine_version:<10} {create_time:<25}")
        else:
            print(f"{'数据结构错误':<20} {'无法解析':<20} {'N/A':<12} {'N/A':<20} {'N/A':<15} {'N/A':<36} {'N/A':<10} {'N/A':<25}")
    
    print("-" * 120)
    print("注意: 如需查看更详细信息，请使用get_instance_detail方法获取实例详情")

def list_escloud_resource():
    """列出所有ESCloud资源"""
    try:
        # 创建ESCloud资源清理器实例
        escloud_cleaner = resource_manager.ESCloudResource()
        escloud_resource_result = escloud_cleaner.list_instances()
        # print(escloud_resource_result)
        if not escloud_resource_result:
            print("未找到任何ESCloud实例")
            return
        
        print("\nESCloud实例列表:")
        print("-" * 120)
        print(f"{'实例ID':<20} {'实例名称':<30} {'状态':<15} {'版本':<15}")
        print("-" * 120)
        
        for instance in escloud_resource_result:
            instance_id = instance.get('instance_id','null')
            instance_name = instance.get('instance_name','null')
            status = instance.get('status','null')
            version = instance.get('version','null')
            
            print(f"{instance_id:<20} {instance_name:<30} {status:<15} {version:<15}")
        
        print("-" * 120)
        print("注意: 如需查看更详细信息，请使用get_instance_detail方法获取实例详情")
        
    except Exception as e:
        logger.error(f"获取ESCloud实例列表时发生错误: {e}")
        print(f"获取ESCloud实例列表时发生错误: {e}")

def print_menu():
    """打印菜单选项"""
    print("\n资源列表查询系统")
    print("-" * 30)
    print("1. 列出所有PostgreSQL资源")
    print("2. 列出所有Redis资源")
    print("3. 列出所有MongoDB资源")
    print("4. 列出所有Kafka资源")
    print("5. 列出所有ESCloud资源")
    print("6. 列出所有资源")
    print("0. 退出")
    print("-" * 30)

def list_all_resources():
    """列出所有资源"""
    print("\n=== 开始获取所有资源信息 ===")
    list_pg_resource()
    list_redis_resource()
    list_mongodb_resource()
    list_kafka_resource()
    list_escloud_resource()
    print("\n=== 所有资源信息获取完成 ===")

def main():
    while True:
        try:
            print_menu()
            choice = input("请选择操作 (0-6): ").strip()
            
            if choice == '0':
                print("感谢使用，再见！")
                break
            elif choice == '1':
                list_pg_resource()
            elif choice == '2':
                list_redis_resource()
            elif choice == '3':
                list_mongodb_resource()
            elif choice == '4':
                list_kafka_resource()
            elif choice == '5':
                list_escloud_resource()
            elif choice == '6':
                list_all_resources()
            else:
                print("无效的选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            break
        except Exception as e:
            logger.error(f"执行过程中发生错误: {e}")
            print(f"执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()