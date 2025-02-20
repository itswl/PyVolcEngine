# PostgreSQL实例配置
# 使用说明：
# 1. 在环境变量中设置以下变量：
#    - PG_SUPER_USER_PASSWORD: 超级用户密码
#    - PG_READONLY_USER_PASSWORD: 只读用户密码
#    - PG_PROD_SUPER_USER_PASSWORD: 生产环境超级用户密码
#    - PG_PROD_READONLY_USER_PASSWORD: 生产环境只读用户密码
# 2. 如果环境变量未设置，将使用默认密码（不推荐在生产环境中使用）
# 3. 网络配置说明：
#    - vpc_id和subnet_id为空时，将使用配置中的vpc和subnet信息创建新的网络资源
#    - vpc_id和subnet_id已配置时，将直接使用指定的网络资源
# 4. 安全建议：
#    - 建议将敏感信息（如密码）配置在环境变量中
#    - 生产环境建议使用更复杂的密码策略
#    - 定期更新密码和安全组配置

from os import environ

# PostgreSQL实例配置列表
# 支持配置多个实例，每个实例可以有不同的规格和配置
pg_configs = [
    {
        # 测试环境实例配置
        "instance": {
            "name": "pg-instance-1",  # 实例名称，在账号下必须唯一
            "engine_version": "PostgreSQL_13",  # 数据库版本，支持PostgreSQL_11/12/13
            "storage_type": "LocalSSD",  # 存储类型，目前仅支持LocalSSD（本地SSD盘）
            "storage_space": 100,  # 存储空间大小，单位GB，范围：20-3000
            "node_spec": "rds.postgres.1c2g",  # 实例规格，格式：rds.postgres.[CPU核数]c[内存大小]g
            "zone_id": "cn-shanghai-a",  # 可用区ID，例如：cn-shanghai-a
            # "vpc_id": None,  # VPC ID，为空时将创建新的VPC
            # "subnet_id": None,  # 子网ID，为空时将创建新的子网
            # 实例专用VPC配置
            "vpc": {
                "name": "pg-instance-1-vpc",  # VPC名称
                "cidr_block": "172.16.0.0/16",  # VPC网段
                "description": "PG实例1专用VPC",  # VPC描述
                "project_name": "default",  # 项目名称
                "tags": [  # VPC标签
                    {
                        "key": "environment",
                        "value": "test"
                    },
                    {
                        "key": "project",
                        "value": "demo-1"
                    }
                ]
            },
            # 实例专用子网配置
            "subnet": {
                "name": "pg-instance-1-subnet",  # 子网名称
                "cidr_block": "172.16.1.0/24",  # 子网网段，必须在VPC网段内
                "zone_id": "cn-shanghai-a",  # 子网可用区，必须与实例在同一可用区
                "description": "PG实例1专用子网",  # 子网描述
                "tags": [  # 子网标签
                    {
                        "key": "environment",
                        "value": "test"
                    },
                    {
                        "key": "project",
                        "value": "demo-1"
                    }
                ]
            },
            "charge_info": {  # 计费信息配置
                "charge_type": "PrePaid",  # 计费方式：PrePaid（包年包月）、PostPaid（按量付费）
                "period_unit": "Month",  # 购买时长单位：Month（月）、Year（年）
                "period": 1,  # 购买时长，单位由period_unit决定
                "auto_renew": True  # 是否自动续费
            }
        },
        # 数据库配置
        "databases": [
            {  # 测试数据库配置
                "name": "testdb",  # 数据库名称
                "owner": "testuser",  # 数据库所有者
                "schemas": [  # Schema配置列表
                    {
                        "name": "test_schema_1",  # Schema名称
                        "owner": "testuser"  # Schema所有者
                    },
                    {
                        "name": "test_schema_2",
                        "owner": "testuser"
                    },
                    {
                        "name": "test_schema_3",
                        "owner": "testuser"
                    },
                    {
                        "name": "test_schema_4",
                        "owner": "testuser"
                    }
                ]
            },
            {  # 开发数据库配置
                "name": "devdb",
                "owner": "testuser",
                "schemas": [
                    {
                        "name": "dev_schema",
                        "owner": "testuser"
                    }
                ]
            }
        ],
        # 数据库账号配置
        "accounts": [
            {  # 超级用户账号配置
                "username": "testuser",  # 账号名称，3-63个字符
                "password": environ.get("PG_SUPER_USER_PASSWORD", "Change_Me_123"),  # 密码，从环境变量获取
                "account_type": "Super"  # 账号类型：Super（超级用户）、Normal（普通用户）
            },
            {  # 只读用户账号配置
                "username": "readonly_user",
                "password": environ.get("PG_READONLY_USER_PASSWORD", "Change_Me_456"),
                "account_type": "Normal"
            }
        ],
        # 备份策略配置
        "backup": {
            "retention_period": 7,  # 备份保留天数，范围：7-730天
            "full_backup_period": "Monday,Wednesday,Friday,Sunday",  # 全量备份周期，多个值用逗号分隔
            "full_backup_time": "18:00Z-19:00Z",  # 全量备份时间窗口，UTC时间
            "increment_backup_frequency": 2  # 增量备份频率，单位：小时，范围：1-24
        },
        # 弹性公网IP配置
        "eip": "test-eip",  # EIP配置名称，用于关联已定义的EIP配置
        # 实例标签配置
        "tags": [
            {
                "key": "environment",  # 环境标签
                "value": "test"
            },
            {
                "key": "project",  # 项目标签
                "value": "demo-1"
            }
        ]
    },
    {  # 生产环境实例配置
        "instance": {
            "name": "pg-instance-2",  # 实例名称
            "engine_version": "PostgreSQL_13",  # 数据库版本
            "storage_type": "LocalSSD",  # 存储类型
            "storage_space": 200,  # 存储空间，生产环境建议预留足够空间
            "node_spec": "rds.postgres.2c4g",  # 实例规格，生产环境建议使用更高配置
            "zone_id": "cn-shanghai-b",  # 可用区ID
            #"vpc_id": "",
            #"subnet_id": "",
            # 生产环境VPC配置
            "vpc": {
                "name": "pg-instance-2-vpc",
                "cidr_block": "172.17.0.0/16",  # 使用不同网段避免冲突
                "description": "PG实例2专用VPC",
                "project_name": "default",
                "tags": [
                    {
                        "key": "environment",
                        "value": "test"
                    },
                    {
                        "key": "project",
                        "value": "demo-2"
                    }
                ]
            },
            # 生产环境子网配置
            "subnet": {
                "name": "pg-instance-2-subnet",
                "cidr_block": "172.17.1.0/24",
                "zone_id": "cn-shanghai-b",
                "description": "PG实例2专用子网",
                "tags": [
                    {
                        "key": "environment",
                        "value": "test"
                    },
                    {
                        "key": "project",
                        "value": "demo-2"
                    }
                ]
            },
            "charge_info": {  # 生产环境建议使用包年包月
                "charge_type": "PrePaid",
                "period_unit": "Month",
                "period": 1,
                "auto_renew": True  # 建议开启自动续费避免服务中断
            }
        },
        # 生产环境数据库配置
        "databases": [
            {
                "name": "proddb",  # 生产数据库
                "owner": "produser",
                "schemas": [
                    {
                        "name": "prod_schema_1",
                        "owner": "produser"
                    },
                    {
                        "name": "prod_schema_2",
                        "owner": "produser"
                    }
                ]
            }
        ],
        # 生产环境账号配置
        "accounts": [
            {  # 生产环境超级用户
                "username": "produser",
                "password": environ.get("PG_PROD_SUPER_USER_PASSWORD", "Prod_Change_Me_123"),
                "account_type": "Super"
            },
            {  # 生产环境只读用户
                "username": "prod_readonly",
                "password": environ.get("PG_PROD_READONLY_USER_PASSWORD", "Prod_Change_Me_456"),
                "account_type": "Normal"
            }
        ],
        # 生产环境备份策略配置（更严格的备份策略）
        "backup": {
            "retention_period": 30,  # 保留30天备份
            "full_backup_period": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday",  # 每天进行全量备份
            "full_backup_time": "02:00Z-03:00Z",  # 凌晨进行备份
            "increment_backup_frequency": 1  # 每小时进行增量备份
        },
        "eip": "prod-eip",  # 生产环境EIP配置
        # 生产环境标签
        "tags": [
            {
                "key": "environment",
                "value": "production"
            },
            {
                "key": "project",
                "value": "demo-2"
            }
        ]
    }
]

