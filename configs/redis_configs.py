# Redis实例配置

instance_configs = [
    {
        "instance": {
            "name": "test-dev-redis",
            "engine_version": "7.0",  # Redis版本
            "node_number": 2,  # 节点数量
            "shard_capacity": 1024,  # 分片容量，单位MB
            "sharded_cluster": 0,  # 是否为分片集群
            "port": 6379,  # Redis端口
            "password": "Test_2021!",  # Redis密码
            "project_name": "default",  # 项目名称
            "configure_nodes": [
                {"az": "cn-shanghai-a"},
                {"az": "cn-shanghai-b"}
            ],
            "multi_az": "enabled",  # 是否启用多可用区
            "region_id": "cn-shanghai",  # 地域ID
            "vpc": {
                "name": "redis-vpc",
                "cidr_block": "172.16.0.0/16",
                "description": "VPC for Redis instance",
                "tags": [
                    {
                        "key": "project",
                        "value": "redis-test"
                    }
                ]
            },
            "subnet": {
                "name": "redis-subnet",
                "cidr_block": "172.16.1.0/24",
                "zone_id": "cn-shanghai-a",
                "description": "Subnet for Redis instance",
                "tags": [
                    {
                        "key": "project",
                        "value": "redis-test"
                    }
                ]
            },
            "charge_info": {
                "charge_type": "PrePaid",  # 计费类型：PostPaid（按量付费）或PrePaid（包年包月）
                "period_unit": "Month",  # 购买时长单位：Month或Year
                "period": 1,  # 购买时长
                "auto_renew": True  # 是否自动续费
            }
        },
        "accounts": [
            {
                "username": "default",  # Redis默认账号
                "password": "Admin@123456",  # 密码
                "account_type": "Administrator"  # 账号类型
            }
        ],
        "backup": {
            "retention_period": 7,  # 备份保留天数
            "backup_time": "03:00-04:00",  # 备份时间段
            "backup_period": ["Monday", "Wednesday", "Friday"]  # 备份周期
        },
        "eip": "test-redis-eip",  # 使用EIP配置名称，对应eip_config.py中的配置
        "whitelists": ["default-whitelist", "office-whitelist", "vpc-whitelist"]  # 使用白名单配置名称列表，对应whitelist_config.py中的配置
    }
]