# coding: utf-8

# ESCloud实例配置
instance_configs = [
    {
        "instance": {
            "name": "test-es2",
            "version": "V7_10",
            "zone_id": "cn-shanghai-a,cn-shanghai-b",
            "instance_type": "es.standard",
            "enable_pure_master": True,
            "master_node_number": 3,
            "master_node_spec": "es.x4.small",
            "master_node_storage_type": "es.volume.essd.pl0",
            "master_node_storage_size": 20,
            "hot_node_number": 4,
            "hot_node_spec": "es.x4.small",
            "hot_node_storage_type": "es.volume.essd.pl0",
            "hot_node_storage_size": 100,
            "kibana_node_number": 1,
            "kibana_node_spec": "kibana.x2.small",
            "project_name": "default",
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
            "charge_info": {
                "charge_type": "PrePaid",
                "period_unit": "Month",
                "period": 1,
                "auto_renew": True
            },
            "network_specs": {
                "bandwidth": 10,
                "is_open": True,
                "type": "Kibana"
            },
            "admin_password": "test@1234",
            "deletion_protection": True,
            "enable_https": False,
            "region_id": "cn-shanghai",
            "whitelist_ip": '61.145.163.230,10.0.0.0/8'
        }
    }
]