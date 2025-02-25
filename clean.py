from __future__ import absolute_import
import resource_cleaner 
import logging
import os

# 可能需要多次执行
# 定义需要清理的PostgreSQL实例配置
pg_resources = {
    "instances": [
        {
            "instance_id": "postgres-89ac20a21d91",
            "eip_address": "14.103.144.18"
        },
        {
            "instance_id": "postgres-f54b33c4ea44",
            "eip_address": "14.103.145.39"
        }
    ]
}

# 定义需要清理的Redis实例配置
redis_resources = {
    "instances": [
        {
            "instance_id": "redis-89ac20a21d91",
            "eip_address": ""
        },
        {
            "instance_id": "redis-shzls6puukagurhnz",
            "eip_address": "14.103.151.19"
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
        pg_cleaner = resource_cleaner.PostgreSQLResourceCleaner()
        
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
        redis_cleaner = resource_cleaner.RedisResourceCleaner()
        
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

def main():
    try:
        # 清理PostgreSQL资源
        pg_success = clean_pg_resources()
        
        # 清理Redis资源
        redis_success = clean_redis_resources()
        
        # 汇总清理结果
        if pg_success and redis_success:
            logger.info("所有资源清理完成！")
        else:
            logger.warning("部分资源清理失败，请检查日志获取详细信息")
            
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        return

if __name__ == "__main__":
    main()
