# EIP配置文件

eip_configs = {
    "test-eip": {
        "name": "test-eip",  # EIP名称
        "description": "EIP for PostgreSQL instance",  # EIP描述
        "billing_type": 3,  # 计费类型：1：包年包月。2：按量计费-按带宽上限计费。3：按量计费-按实际流量计费。
        "bandwidth": 10,  # 带宽大小，单位Mbps
        "isp": "BGP",  # 线路类型：BGP
        "project_name": "default",  # 项目名称
        "period_unit": "Month",  # 购买时长单位
        "period": 1  # 购买时长
    },
    "prod-eip": {
        "name": "prod-eip",  # EIP名称
        "description": "EIP for Production PostgreSQL instance",  # EIP描述
        "billing_type": 3,  # 计费类型：3表示按量付费
        "bandwidth": 20,  # 带宽大小，单位Mbps
        "isp": "BGP",  # 线路类型：BGP
        "project_name": "default",  # 项目名称
        "period_unit": "Month",  # 购买时长单位
        "period": 1  # 购买时长
    },
    "test-redis-eip": {
        "name": "test-redis-eip",  # EIP名称
        "description": "EIP for Production PostgreSQL instance",  # EIP描述
        "billing_type": 3,  # 计费类型：3表示按量付费
        "bandwidth": 20,  # 带宽大小，单位Mbps
        "isp": "BGP",  # 线路类型：BGP
        "project_name": "default",  # 项目名称
        "period_unit": "Month",  # 购买时长单位
        "period": 1  # 购买时长
    },
    "test-mongodb-eip": {
        "name": "test-mongodb-eip",  # EIP名称
        "description": "EIP for Production PostgreSQL instance",  # EIP描述
        "billing_type": 3,  # 计费类型：3表示按量付费
        "bandwidth": 10,  # 带宽大小，单位Mbps
        "isp": "BGP",  # 线路类型：BGP
        "project_name": "default",  # 项目名称
        "period_unit": "Month",  # 购买时长单位
        "period": 1  # 购买时长
    }
}