# PostgreSQL实例配置
pg_config = {

    "instance": {
        "name": "test-pg-instance",
        "engine_version": "PostgreSQL_13",
        "storage_type": "LocalSSD",
        "storage_space": 100,
        "node_spec": "rds.postgres.1c2g",
        "zone_id": "cn-shanghai-a",
        "charge_info": {
            "charge_type": "PrePaid",
            "period_unit": "Month",
            "period": 1,
            "auto_renew": True
        }
    },
    "databases": [
        {
            "name": "testdb",
            "owner": "testuser",
            "schemas": [
                {
                    "name": "test_schema_1",
                    "owner": "testuser"
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
        {
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
    "accounts": [
        {
            "username": "testuser",
            "password": "Wl19950707",
            "account_type": "Super"
        },
        {
            "username": "readonly_user",
            "password": "Readonly123",
            "account_type": "Normal"
        }
    ],
    "backup": {
        "retention_period": 7,
        "full_backup_period": "Monday,Wednesday,Friday,Sunday",
        "full_backup_time": "18:00Z-19:00Z",
        "increment_backup_frequency": 2
    },
    "eip": {
        "name": "test-eip",
        "description": "EIP for PostgreSQL instance",
        "billing_type": 3, # 3 按量付费
        "bandwidth": 10,
        "isp": "BGP",
        "project_name": "default",
        "period_unit": "Month",
        "period": 1
    },
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