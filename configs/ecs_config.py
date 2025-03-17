# ECS配置文件

ecs_configs = {
    "her-test-ecs": {
        "name": "her-test-hs-sh-gpu-01",  # ECS实例名称
        "description": "测试ECS实例",  # 实例描述
        "dry_run": True,  # 是否预览
        "instance_type": "ecs.xni3.5xlarge",  # 实例规格
        "image_id": "image-ydjqeh6dqtlkt2gxftl3",  # 镜像ID
        "zone_id": "cn-shanghai-a",  # 可用区
        "vpc_id": "vpc-22j75iztkwo3k7r2qr1czeq8b",  # VPC ID
        "subnet_id": "subnet-5gfoskjvbhts73inqkkgo6ow",  # 子网ID
        "security_group_ids": ["sg-22j75j5qo8u0w7r2qr1r5yieo"],  # 安全组ID列表
        "instance_charge_type": "PrePaid",  # 计费类型：PrePaid（包年包月）或PostPaid（按量付费）
        "period_unit": "Month",  # 购买时长单位：Month或Year
        "period": 1,  # 购买时长
        "password": "Ns@123456Shenzhen",  # 密码
        "auto_renew": True,  # 是否自动续费
        "auto_renew_period": 1,  # 自动续费时长
        "hostname": "hs-sh-her-test-ecs",  # 主机名
        "credit_specification": "Standard",  # 性能模式
        "user_data": "aGVsbG8gd29ybGQK",  # 实例自定义数据
        "install_run_command_agent": True,  # 是否安装RunCommandAgent
        "eip": {  # EIP配置，如果不需要可以设为None
            "bandwidth": 200,  # 带宽大小，单位Mbps
            "isp": "BGP",  # 线路类型：BGP
            "billing_type": 3  # 计费类型：1：包年包月。2：按量计费-按带宽上限计费。3：按量计费
        },
        "volumes": [  # 磁盘配置
            {
                "size": 40,  # 系统盘大小，单位GB
                "volume_type": "ESSD_PL0",  # 磁盘类型
                "delete_with_instance": True  # 是否随实例删除
            },
            {
                "size": 400,  # 数据盘大小，单位GB
                "volume_type": "ESSD_PL0",  # 磁盘类型
                "delete_with_instance": True  # 是否随实例删除
            }
        ]
    },
    "her-test-gpu": {
        "name": "her-test-hs-sh-gpu",  # ECS实例名称
        "description": "GPU测试实例",  # 实例描述
        "dry_run": True,  # 是否预览
        "instance_type": "ecs.xni3.5xlarge",  # 实例规格
        "image_id": "image-ydjqeh6dqtlkt2gxftl3",  # 镜像ID
        "zone_id": "cn-shanghai-a",  # 可用区
        "vpc_id": "vpc-22j75iztkwo3k7r2qr1czeq8b",  # VPC ID
        "subnet_id": "subnet-5gfoskjvbhts73inqkkgo6ow",  # 子网ID
        "security_group_ids": ["sg-22j75j5qo8u0w7r2qr1r5yieo"],  # 安全组ID列表
        "instance_charge_type": "PrePaid",  # 计费类型：PrePaid（包年包月）或PostPaid（按量付费）
        "period_unit": "Month",  # 购买时长单位：Month或Year
        "period": 1,  # 购买时长
        "password": "Ns@123456Shenzhen",  # 密码
        "auto_renew": True,  # 是否自动续费
        "auto_renew_period": 1,  # 自动续费时长
        "hostname": "hs-sh-her-test-gpu",  # 主机名
        "credit_specification": "Standard",  # 性能模式
        "user_data": "aGVsbG8gd29ybGQK",  # 实例自定义数据
        "install_run_command_agent": True,  # 是否安装RunCommandAgent
        "eip": {  # EIP配置，如果不需要可以设为None
            "bandwidth": 200,  # 带宽大小，单位Mbps
            "isp": "BGP",  # 线路类型：BGP
            "billing_type": 3  # 计费类型：1：包年包月。2：按量计费-按带宽上限计费。3：按量计费
        },
        "volumes": [  # 磁盘配置
            {
                "size": 40,  # 系统盘大小，单位GB
                "volume_type": "ESSD_PL0",  # 磁盘类型
                "delete_with_instance": True  # 是否随实例删除
            },
            {
                "size": 400,  # 数据盘大小，单位GB
                "volume_type": "ESSD_PL0",  # 磁盘类型
                "delete_with_instance": True  # 是否随实例删除
            }
        ]
    }
}