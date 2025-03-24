# Redis实例配置

instance_configs = [
    {
        "instance": {
            "name": "eve-cn-prod-redis",
            "engine_version": "7.0",  # Redis版本
            "node_number": 2,  # 节点数量
            "shard_capacity": 8192,  # 分片容量，单位MB
            "sharded_cluster": 0,  # 是否为分片集群
            "port": 6379,  # Redis端口
            "password": "ns2024Xqrif848",  # Redis密码
            "project_name": "default",  # 项目名称
            "configure_nodes": [
                {"az": "cn-shanghai-a"},
                {"az": "cn-shanghai-b"}
            ],
            'vpc_id': 'vpc-22j75iztkwo3k7r2qr1czeq8b',
            "subnet_id": 'subnet-5gfoskjvbhts73inqkkgo6ow',
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
        # 数据库账号配置，默认已创建管理员帐号，新增只读用户
        "accounts": [
            {
                "username": "readonly_user",  # Redis默认账号
                "password": "ReadOnly@123",  # 密码
                "account_type": "ReadOnly"  # 账号类型
            }
        ],
        # 备份策略配置，redis不用
        "backup": {
            "retention_period": 7,  # 备份保留天数
            "backup_time": "03:00-04:00",  # 备份时间段
            "backup_period": ["Monday", "Wednesday", "Friday"]  # 备份周期
        },
        # EIP配置，不配置不创建，选择一个使用
        # 方式1: 字符串引用 (取消注释使用)
        # "eip": "eve-cn-prod-es",  # 使用eip_config.py中配置的名称
        
        ## 方式2: 直接配置(取消注释使用)
        "eip": {
            "name": "eve-cn-prod-redis",  # EIP名称
            "description": "EIP for Production Redis instance",  # EIP描述
            "billing_type": 3,  # 计费类型：3表示按量付费
            "bandwidth": 10,  # 带宽大小，单位Mbps
            "isp": "BGP",  # 线路类型：BGP
            "project_name": "default",  # 项目名称
            "period_unit": "Month",  # 购买时长单位
            "period": 1  # 购买时长
        },
        "whitelists": ["wan_server", "wan_office", "lan"]  # 使用白名单配置名称列表，对应whitelist_config.py中的配置
    }
]