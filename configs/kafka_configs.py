# Kafka实例配置

instance_configs = [
    {
        "instance": {
            "name": "test-kafka",
            "product_id": "kafka.20xrate.hw",  # Kafka规格
            "zone_id": "cn-shanghai-a,cn-shanghai-b,cn-shanghai-c",  # 可用区
            "storage_size": 300,  # 存储大小，单位GB
            "partition_num": 350,  # 分区数量
            "topic_num": 10,  # 主题数量
            "compute_spec": "kafka.20xrate.hw",  # 计算规格，表示2核4G
            "storage_type": "ESSD_FlexPL",  # 存储类型
            "version": "2.8.2",  # Kafka版本
            "vpc": {
                "name": "kafka-vpc",
                "cidr_block": "172.16.0.0/16",
                "description": "VPC for Kafka instance",
                "tags": [
                    {
                        "key": "project",
                        "value": "kafka-test"
                    }
                ]
            },
            "subnet": {
                "name": "kafka-subnet",
                "cidr_block": "172.16.2.0/24",
                "zone_id": "cn-shanghai-a",
                "description": "Subnet for Kafka instance",
                "tags": [
                    {
                        "key": "project",
                        "value": "kafka-test"
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
        "acls": [
            {
                "username": "*",  # 用户名
                "operation": "Read,Write",  # 操作类型：Read, Write, Create, Delete, Alter, Describe, ClusterAction, All
                "permission": "Create,Delete",  # 权限类型：Allow, Deny
                "resource_type": "Topic",  # 资源类型：Topic, Group, Cluster
                "resource_name": "*",  # 资源名称，*表示所有
                "pattern_type": "Literal",  # 模式类型：Literal, Prefixed
                "host": "*"  # 主机，*表示所有
            }
        ],
        "eip": "kafka-eip",  # 使用EIP配置名称，对应eip_config.py中的配置
        "whitelists": ["default-whitelist", "office-whitelist", "vpc-whitelist"]  # 使用白名单配置名称列表，对应whitelist_config.py中的配置
    }
]