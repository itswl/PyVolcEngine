# EIP配置文件

eip_configs = {
    "her-dev-pg": {
        "name": "her-dev-pg",  # EIP名称
        "description": "EIP for PostgreSQL instance",  # EIP描述
        "billing_type": 3,  # 计费类型：1：包年包月。2：按量计费-按带宽上限计费。3：按量计费
        "bandwidth": 10,  # 带宽大小，单位Mbps
        "isp": "BGP",  # 线路类型：BGP
        "project_name": "default",  # 项目名称
        "period_unit": "Month",  # 购买时长单位
        "period": 1  # 购买时长
    },
    "her-dev-kafka": {
        "name": "her-dev-kafka",  # EIP名称
        "description": "EIP for Production Kafka instance",  # EIP描述
        "billing_type": 3,  # 计费类型：3表示按量付费
        "bandwidth": 10,  # 带宽大小，单位Mbps
        "isp": "BGP",  # 线路类型：BGP
        "project_name": "default",  # 项目名称
        "period_unit": "Month",  # 购买时长单位
        "period": 1  # 购买时长
    },
    "her-dev-redis": {
        "name": "her-dev-redis",  # EIP名称
        "description": "EIP for Production Redis instance",  # EIP描述
        "billing_type": 3,  # 计费类型：3表示按量付费
        "bandwidth": 10,  # 带宽大小，单位Mbps
        "isp": "BGP",  # 线路类型：BGP
        "project_name": "default",  # 项目名称
        "period_unit": "Month",  # 购买时长单位
        "period": 1  # 购买时长
    },
    "her-dev-mongodb": {
        "name": "her-dev-mongodb",  # EIP名称
        "description": "EIP for Production MongoDB instance",  # EIP描述
        "billing_type": 3,  # 计费类型：3表示按量付费
        "bandwidth": 10,  # 带宽大小，单位Mbps
        "isp": "BGP",  # 线路类型：BGP
        "project_name": "default",  # 项目名称
        "period_unit": "Month",  # 购买时长单位
        "period": 1  # 购买时长
    }
}