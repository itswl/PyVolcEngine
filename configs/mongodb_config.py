# coding: utf-8

# MongoDB实例配置
mongodb_configs = [
    {
        "instance": {
            "name": "mongodb-test",
            "engine_version": "6.0",
            "db_engine": "MongoDB",
            "storage_type": "LocalSSD",
            "storage_space_gb": 20,
            "node_spec": "mongo.2c4g",
            "zone_id": "cn-beijing-a",
            "instance_type": "ShardedCluster",
            "period": 1,
            "period_unit": "Month",
            "project_name": "default",
            "mongos_node_number": 2,
            "mongos_node_spec": "mongo.mongos.2c4g",
            "node_number": 2,
            "node_spec": "mongo.mongos.2c4g",
            "shard_number": 2,
            "super_account_name": "root",
            "super_account_password": "root",
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
                "zone_id": "cn-beijing-a",
                "description": "MongoDB Subnet",
                "tags": [
                    {
                        "key": "project",
                        "value": "mongodb"
                    }
                ]
            },
            "charge_info": {
                "charge_type": "PostPaid",
                "period_unit": "Month",
                "period": 1,
                "auto_renew": False
            }
        },
        "databases": [
            {
                "name": "testdb",
                "schemas": [
                    {
                        "name": "test_schema_1",
                        "owner": "admin"
                    },
                    {
                        "name": "test_schema_2",
                        "owner": "admin"
                    }
                ]
            },
            {
                "name": "devdb",
                "schemas": [
                    {
                        "name": "dev_schema",
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
            },
            {
                "username": "developer",
                "password": "Dev123456",
                "account_type": "Normal"
            }
        ],
        "backup": {
            "retention_period": 7,
            "full_backup_period": "Monday,Thursday",
            "full_backup_time": "03:00-04:00",
            "increment_backup_frequency": "Every_6_Hours"
        },
        "eip": {
            "name": "mongodb-eip",
            "description": "MongoDB EIP",
            "bandwidth": 5,
            "isp": "BGP",
            "billing_type": "PostPaidByBandwidth",
            "tags": [
                {
                    "key": "project",
                    "value": "mongodb"
                }
            ]
        }
    }
]