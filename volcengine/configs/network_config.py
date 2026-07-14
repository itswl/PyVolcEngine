# VPC和子网配置
network_config = {
    "vpc": {
        "name": "test-vpc",
        "cidr_block": "172.16.0.0/16",
        "description": "测试用VPC",
        "project_name": "default",
        "tags": [
            {
                "key": "environment",
                "value": "test"
            },
            {
                "key": "project",
                "value": "demo"
            }
        ]
    },
    "subnets": [
        {
            "name": "test-subnet-3",
            "cidr_block": "172.16.3.0/24",
            "zone_id": "cn-shanghai-a",
            "description": "测试子网3",
            "tags": [
                {
                    "key": "environment",
                    "value": "test"
                },
                {
                    "key": "project",
                    "value": "demo"
                }
            ]
        },
        {
            "name": "test-subnet-2",
            "cidr_block": "172.16.2.0/24",
            "zone_id": "cn-shanghai-b",
            "description": "测试子网2",
            "tags": [
                {
                    "key": "environment",
                    "value": "test"
                },
                {
                    "key": "project",
                    "value": "demo"
                }
            ]
        },
        {
            "name": "test-subnet-1",
            "cidr_block": "172.16.1.0/24",
            "zone_id": "cn-shanghai-c",
            "description": "测试子网1",
            "tags": [
                {
                    "key": "environment",
                    "value": "test"
                },
                {
                    "key": "project",
                    "value": "demo"
                }
            ]
        }
    ]
}