from __future__ import absolute_import
import resource_manager 
import logging
import os

# 可能需要多次执行
# 定义需要清理的ESCloud实例配置
escloud_resources = {
    "instances": [
        {
            "instance_id": "es-test",
            "eip_address": "eip-3qdru72trhslc7prmkzww6wzq"
        }
    ]
}

# 定义需要清理的PostgreSQL实例配置
pg_resources = {
    "instances": [
        {
            "instance_id": "postgres-test",
            "eip_address": "eip-3qdru72trhslc7prmkzww6wzq"
        },
        {
            "instance_id": "postgres-f54b33c4ea44",
            "eip_address": "14.103.144.IP_ADDRESS2"
        }
    ]
}

# 定义需要清理的Redis实例配置
redis_resources = {
    "instances": [
        {
            "instance_id": "redis-test",
            "eip_address": ""
        },
        {
            "instance_id": "redis-test",
            "eip_address": "IP_ADDRESS3"
        }
    ]
}

mongodb_resources = {
    "instances": [
        {
            "instance_id": "mongo-test",
            "eip_address": ""
        },
        {
            "instance_id": "mongo-shard-b29649ced34a",
            "eip_address": "IP_ADDRESS3"
        }
    ]
}

kafka_resources = {
    "instances": [
        {
            "instance_id": "kafka-cnai9jdysiovuzz7",
            "eip_address": ""
        }
    ]
}

log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(log_dir, 'cleaner.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)



def clean_pg_resources():
    """清理PostgreSQL资源"""
    try:
        # 创建PostgreSQL资源清理器实例
        pg_cleaner = resource_manager.PostgreSQLResource()
        
        # 从配置中获取需要清理的PostgreSQL实例信息
        pg_instance_ids = [instance['instance_id'] for instance in pg_resources['instances']]
        pg_eip_addresses = [instance['eip_address'] for instance in pg_resources['instances']]
        
        if pg_cleaner.clean_all_resources(pg_instance_ids, pg_eip_addresses):
            logger.info("PostgreSQL资源清理完成！")
            return True
        else:
            logger.warning("PostgreSQL资源清理部分失败，请检查日志获取详细信息")
            return False
            
    except Exception as e:
        logger.error(f"清理PostgreSQL资源时发生错误: {e}")
        return False

def clean_redis_resources():
    """清理Redis资源"""
    try:
        # 创建Redis资源清理器实例
        redis_cleaner = resource_manager.RedisResource()
        
        # 从配置中获取需要清理的Redis实例信息
        redis_instance_ids = [instance['instance_id'] for instance in redis_resources['instances']]
        redis_eip_addresses = [instance['eip_address'] for instance in redis_resources['instances']]
        
        if redis_cleaner.clean_all_resources(redis_instance_ids, redis_eip_addresses):
            logger.info("Redis资源清理完成！")
            return True
        else:
            logger.warning("Redis资源清理部分失败，请检查日志获取详细信息")
            return False
            
    except Exception as e:
        logger.error(f"清理Redis资源时发生错误: {e}")
        return False

def clean_mongodb_resources():
    """清理MongoDB资源"""
    try:
        # 创建Redis资源清理器实例
        mongodb_cleaner = resource_manager.MongoDbResource()
        
        # 从配置中获取需要清理的Redis实例信息
        mongodb_instance_ids = [instance['instance_id'] for instance in mongodb_resources['instances']]
        mongodb_eip_addresses = [instance['eip_address'] for instance in mongodb_resources['instances']]
        
        if mongodb_cleaner.clean_all_resources(mongodb_instance_ids, mongodb_eip_addresses):
            logger.info("mongodb资源清理完成！")
            return True
        else:
            logger.warning("mongodb资源清理部分失败，请检查日志获取详细信息")
            return False
            
    except Exception as e:
        logger.error(f"清理mongodb资源时发生错误: {e}")
        return False

def clean_kafka_resources():
    """清理Kafka资源"""
    try:
        # 创建Kafka资源清理器实例
        kafka_cleaner = resource_manager.KafkaResource()
        
        # 从配置中获取需要清理的Kafka实例信息
        kafka_instance_ids = [instance['instance_id'] for instance in kafka_resources['instances']]
        kafka_eip_addresses = [instance['eip_address'] for instance in kafka_resources['instances']]
        
        if kafka_cleaner.clean_all_resources(kafka_instance_ids, kafka_eip_addresses):
            logger.info("Kafka资源清理完成！")
            return True
        else:
            logger.warning("Kafka资源清理部分失败，请检查日志获取详细信息")
            return False
            
    except Exception as e:
        logger.error(f"清理Kafka资源时发生错误: {e}")
        return False

def list_kafka_resource(page_number=1, page_size=100):
    """列出所有Kafka资源"""
    kafka_resource = resource_manager.KafkaResource()
    kafka_resource_result = kafka_resource.list_instances(page_number=1, page_size=100)
    print(kafka_resource_result)
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
            
            # 尝试获取公网访问信息（如果有的话）
            # 这里需要根据实际MongoDB API返回的结构调整
            
            print(f"{instance_id:<20} {instance_name:<20} {status:<12} {vpc_id:<20} {public_ip:<15} {eip_id:<36} {engine_version:<10} {create_time:<25}")
        else:
            print(f"{'数据结构错误':<20} {'无法解析':<20} {'N/A':<12} {'N/A':<20} {'N/A':<15} {'N/A':<36} {'N/A':<10} {'N/A':<25}")
    
    print("-" * 120)
    print("注意: 如需查看更详细信息，请使用get_instance_detail方法获取实例详情")

def clean_all_resources():
    """清理所有资源"""
    try:
        # 清理PostgreSQL资源
        pg_success = clean_pg_resources()
        
        # 清理Redis资源
        redis_success = clean_redis_resources()
        
        # 清理MongoDB资源
        mongodb_success = clean_mongodb_resources()
        
        # 清理Kafka资源
        kafka_success = clean_kafka_resources()
        
        # 清理ESCloud资源
        escloud_success = clean_escloud_resources()
        
        # 汇总清理结果
        if pg_success and redis_success and mongodb_success and kafka_success and escloud_success:
            logger.info("所有资源清理完成！")
            print("所有资源清理完成！")
        else:
            logger.warning("部分资源清理失败，请检查日志获取详细信息")
            print("部分资源清理失败，请检查日志获取详细信息")
            
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        print(f"执行过程中发生错误: {e}")
        return

def print_menu():
    """打印菜单选项"""
    print("\n资源管理系统")
    print("-" * 30)
    print("1. 列出所有PostgreSQL资源")
    print("2. 列出所有Redis资源")
    print("3. 列出所有MongoDB资源")
    print("4. 列出所有Kafka资源")
    print("5. 列出所有ESCloud资源")
    print("6. 列出所有资源")
    print("7. 清理PostgreSQL资源(使用预定义配置)")
    print("8. 清理Redis资源(使用预定义配置)")
    print("9. 清理MongoDB资源(使用预定义配置)")
    print("10. 清理Kafka资源(使用预定义配置)")
    print("11. 清理ESCloud资源(使用预定义配置)")
    print("12. 清理所有资源(使用预定义配置)")
    print("13. 手动输入PostgreSQL实例ID和EIP进行清理")
    print("14. 手动输入Redis实例ID和EIP进行清理")
    print("15. 手动输入MongoDB实例ID和EIP进行清理")
    print("16. 手动输入Kafka实例ID和EIP进行清理")
    print("17. 手动输入ESCloud实例ID进行清理")
    print("0. 退出")
    print("-" * 30)

def clean_pg_resource_manual():
    """手动输入PostgreSQL实例ID和EIP进行清理"""
    try:
        instance_id = input("请输入PostgreSQL实例ID: ").strip()
        if not instance_id:
            print("实例ID不能为空")
            return False
            
        eip_address = input("请输入EIP地址 (如果没有，请直接按Enter): ").strip()
        
        # 创建PostgreSQL资源清理器实例
        pg_cleaner = resource_manager.PostgreSQLResource()
        
        if pg_cleaner.clean_all_resources([instance_id], [eip_address] if eip_address else []):
            logger.info(f"PostgreSQL实例 {instance_id} 清理完成！")
            return True
        else:
            logger.warning(f"PostgreSQL实例 {instance_id} 清理部分失败，请检查日志获取详细信息")
            return False
            
    except Exception as e:
        logger.error(f"清理PostgreSQL资源时发生错误: {e}")
        return False

def clean_redis_resource_manual():
    """手动输入Redis实例ID和EIP进行清理"""
    try:
        instance_id = input("请输入Redis实例ID: ").strip()
        if not instance_id:
            print("实例ID不能为空")
            return False
            
        eip_address = input("请输入EIP地址 (如果没有，请直接按Enter): ").strip()
        
        # 创建Redis资源清理器实例
        redis_cleaner = resource_manager.RedisResource()
        
        if redis_cleaner.clean_all_resources([instance_id], [eip_address] if eip_address else []):
            logger.info(f"Redis实例 {instance_id} 清理完成！")
            return True
        else:
            logger.warning(f"Redis实例 {instance_id} 清理部分失败，请检查日志获取详细信息")
            return False
            
    except Exception as e:
        logger.error(f"清理Redis资源时发生错误: {e}")
        return False

def clean_mongodb_resource_manual():
    """手动输入MongoDB实例ID和EIP进行清理"""
    try:
        instance_id = input("请输入MongoDB实例ID: ").strip()
        if not instance_id:
            print("实例ID不能为空")
            return False
            
        eip_address = input("请输入EIP地址 (如果没有，请直接按Enter): ").strip()
        
        # 创建MongoDB资源清理器实例
        mongodb_cleaner = resource_manager.MongoDbResource()
        
        if mongodb_cleaner.clean_all_resources([instance_id], [eip_address] if eip_address else []):
            logger.info(f"MongoDB实例 {instance_id} 清理完成！")
            return True
        else:
            logger.warning(f"MongoDB实例 {instance_id} 清理部分失败，请检查日志获取详细信息")
            return False
            
    except Exception as e:
        logger.error(f"清理MongoDB资源时发生错误: {e}")
        return False

def clean_kafka_resource_manual():
    """手动输入Kafka实例ID和EIP进行清理"""
    try:
        instance_id = input("请输入Kafka实例ID: ").strip()
        if not instance_id:
            print("实例ID不能为空")
            return False
            
        eip_address = input("请输入EIP地址 (如果没有，请直接按Enter): ").strip()
        
        # 创建Kafka资源清理器实例
        kafka_cleaner = resource_manager.KafkaResource()
        
        if kafka_cleaner.clean_all_resources([instance_id], [eip_address] if eip_address else []):
            logger.info(f"Kafka实例 {instance_id} 清理完成！")
            return True
        else:
            logger.warning(f"Kafka实例 {instance_id} 清理部分失败，请检查日志获取详细信息")
            return False
            
    except Exception as e:
        logger.error(f"清理Kafka资源时发生错误: {e}")
        return False

def list_escloud_resource():
    """列出所有ESCloud资源"""
    try:
        # 创建ESCloud资源清理器实例
        escloud_cleaner = resource_manager.ESCloudResource()
        escloud_resource_result = escloud_cleaner.list_instances()
        
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

def clean_escloud_resources():
    """清理ESCloud资源"""
    try:
        # 创建ESCloud资源清理器实例
        escloud_cleaner = resource_manager.ESCloudResource()
        
        # 从配置中获取需要清理的ESCloud实例信息
        escloud_instance_ids = [instance['instance_id'] for instance in escloud_resources['instances']]
        
        if escloud_cleaner.clean_all_resources(escloud_instance_ids):
            logger.info("ESCloud资源清理完成！")
            return True
        else:
            logger.warning("ESCloud资源清理部分失败，请检查日志获取详细信息")
            return False
            
    except Exception as e:
        logger.error(f"清理ESCloud资源时发生错误: {e}")
        return False

def clean_escloud_resource_manual():
    """手动输入ESCloud实例ID进行清理"""
    try:
        instance_id = input("请输入ESCloud实例ID: ").strip()
        if not instance_id:
            print("实例ID不能为空")
            return False
        
        # 创建ESCloud资源清理器实例
        escloud_cleaner = resource_manager.ESCloudResource()
        
        if escloud_cleaner.clean_all_resources([instance_id]):
            logger.info(f"ESCloud实例 {instance_id} 清理完成！")
            return True
        else:
            logger.warning(f"ESCloud实例 {instance_id} 清理部分失败，请检查日志获取详细信息")
            return False
            
    except Exception as e:
        logger.error(f"清理ESCloud资源时发生错误: {e}")
        return False

def main():
    """主函数，提供交互式菜单"""
    while True:
        print_menu()
        try:
            print('最好只使用 list, 清理请优先调用 unsubscribe_instances.py')
            print('最好只使用 list, 清理请优先调用 unsubscribe_instances.py')
            print('最好只使用 list, 清理请优先调用 unsubscribe_instances.py')
            choice = input("请选择操作 [0-17]: ")
            if choice == "0":
                print("退出程序...")
                break
            elif choice == "1":
                list_pg_resource()
            elif choice == "2":
                list_redis_resource()
            elif choice == "3":
                list_mongodb_resource()
            elif choice == "4":
                list_kafka_resource(page_number=1, page_size=100)
            elif choice == "5":
                list_escloud_resource()
            elif choice == "6":
                list_pg_resource()
                list_redis_resource()
                list_mongodb_resource()
                list_kafka_resource(page_number=1, page_size=100)
                list_escloud_resource()
            elif choice == "7":
                result = clean_pg_resources()
                if result:
                    print("PostgreSQL资源清理完成！")
                else:
                    print("PostgreSQL资源清理部分失败，请检查日志获取详细信息")
            elif choice == "8":
                result = clean_redis_resources()
                if result:
                    print("Redis资源清理完成！")
                else:
                    print("Redis资源清理部分失败，请检查日志获取详细信息")
            elif choice == "9":
                result = clean_mongodb_resources()
                if result:
                    print("MongoDB资源清理完成！")
                else:
                    print("MongoDB资源清理部分失败，请检查日志获取详细信息")
            elif choice == "10":
                result = clean_kafka_resources()
                if result:
                    print("Kafka资源清理完成！")
                else:
                    print("Kafka资源清理部分失败，请检查日志获取详细信息")
            elif choice == "11":
                result = clean_escloud_resources()
                if result:
                    print("ESCloud资源清理完成！")
                else:
                    print("ESCloud资源清理部分失败，请检查日志获取详细信息")
            elif choice == "12":
                clean_all_resources()
            elif choice == "13":
                result = clean_pg_resource_manual()
                if result:
                    print("PostgreSQL资源手动清理完成！")
                else:
                    print("PostgreSQL资源手动清理部分失败，请检查日志获取详细信息")
            elif choice == "14":
                result = clean_redis_resource_manual()
                if result:
                    print("Redis资源手动清理完成！")
                else:
                    print("Redis资源手动清理部分失败，请检查日志获取详细信息")
            elif choice == "15":
                result = clean_mongodb_resource_manual()
                if result:
                    print("MongoDB资源手动清理完成！")
                else:
                    print("MongoDB资源手动清理部分失败，请检查日志获取详细信息")
            elif choice == "16":
                result = clean_kafka_resource_manual()
                if result:
                    print("Kafka资源手动清理完成！")
                else:
                    print("Kafka资源手动清理部分失败，请检查日志获取详细信息")
            elif choice == "17":
                result = clean_escloud_resource_manual()
                if result:
                    print("ESCloud资源手动清理完成！")
                else:
                    print("ESCloud资源手动清理部分失败，请检查日志获取详细信息")
            else:
                print("无效的选择，请重新输入")
        except Exception as e:
            print(f"操作过程中发生错误: {e}")
            logger.error(f"操作过程中发生错误: {e}")
        
        # 操作完成后暂停
        input("\n按Enter键继续...")

if __name__ == "__main__":
    main()
