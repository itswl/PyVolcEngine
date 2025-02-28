# coding: utf-8

# MongoDB实例优化配置
instance_configs = [
    {
        "instance": {
            "name": "optimized-mongo",
            "engine_version": "MongoDB_6_0",
            "db_engine": "MongoDB",
            "storage_type": "LocalSSD",
            "storage_space_gb": 20,  # 参考现有实例配置
            "zone_id": "cn-shanghai-a,cn-shanghai-b,cn-shanghai-c",  # 多可用区部署
            "instance_type": "ShardedCluster",
            "period": 1,
            "period_unit": "Month",
            "project_name": "default",
            "mongos_node_number": 2,  # 参考现有实例配置
            "mongos_node_spec": "mongo.mongos.1c2g",  # 参考现有实例配置
            "node_number": 3,  # 每个分片3个节点（1主2从，其中1个Hidden）
            "node_spec": "mongo.shard.1c2g",  # 参考现有实例配置
            "shard_number": 2,  # 参考现有实例配置的2个分片
            "super_account_name": "root",
            "super_account_password": "Test@123456",
            "SpecType": "GENERAL",
            "vpc": {
                "name": "mongodb-vpc",
                "cidr_block": "172.16.0.0/16",
                "description": "MongoDB VPC",
                "tags": [
                    {
                        "key": "project",
                        "value": "mongodb"
                    }
                ]
            },
            "subnet": {
                "name": "mongodb-subnet",
                "cidr_block": "172.16.1.0/24",
                "zone_id": "cn-shanghai-a",
                "description": "MongoDB Subnet",
                "tags": [
                    {
                        "key": "project",
                        "value": "mongodb"
                    }
                ]
            },
            "charge_info": {
                "charge_type": "Prepaid",  # 参考现有实例的计费类型
                "period_unit": "Month",
                "period": 1,
                "auto_renew": True  # 参考现有实例的自动续费设置
            }
        },
        "databases": [
            {
                "name": "testdb",
                "schemas": [
                    {
                        "name": "test_schema_1",
                        "owner": "admin"
                    }
                ]
            }
        ],
        "accounts": [
            {
                "username": "admin",
                "password": "Admin123456",
                "account_type": "Super"
            }
        ],
        "backup": {
            "retention_period": 7,
            "full_backup_period": "Monday,Thursday",
            "full_backup_time": "03:00-04:00",
            "increment_backup_frequency": "Every_6_Hours"
        },
        "eip": "test-mongodb-eip"
    }
]