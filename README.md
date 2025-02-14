```
python pg_manager.py
2025-02-14 19:18:56,023 - INFO - VPC创建成功，VPC ID: vpc-22j3w66jbfn5s7r2qr19q9lxg
2025-02-14 19:18:56,210 - INFO - 当前VPC状态: Pending
2025-02-14 19:19:06,387 - INFO - VPC已准备就绪
2025-02-14 19:19:06,785 - INFO - 子网创建成功，子网ID: subnet-22j3wagfq7x8g7r2qr1gi2rop
2025-02-14 19:19:06,868 - INFO - VPC vpc-22j3w66jbfn5s7r2qr19q9lxg 当前状态为 Pending，等待其变为可用状态
2025-02-14 19:19:06,967 - INFO - 当前VPC状态: Pending
2025-02-14 19:19:17,140 - INFO - VPC已准备就绪
2025-02-14 19:19:17,659 - INFO - 子网创建成功，子网ID: subnet-5g7stt7bhr0g73inqkduahin
2025-02-14 19:19:17,824 - INFO - VPC vpc-22j3w66jbfn5s7r2qr19q9lxg 当前状态为 Pending，等待其变为可用状态
2025-02-14 19:19:17,907 - INFO - 当前VPC状态: Pending
2025-02-14 19:19:28,092 - INFO - VPC已准备就绪
2025-02-14 19:19:28,453 - INFO - 子网创建成功，子网ID: subnet-5g7swltw8jr473inqkonr5uc
2025-02-14 19:19:28,609 - INFO - 子网已准备就绪
PostgreSQL实例创建成功: {'instance_id': 'postgres-f071be4dc0b1', 'order_id': 'Order2345000017748906370'}
2025-02-14 19:23:00,556 - INFO - 等待实例创建完成...
实例状态: Creating
实例状态: Creating
实例状态: Creating
实例状态: Creating
实例状态: Creating
实例已准备就绪
EIP申请成功: {'allocation_id': 'eip-3qe3qj8is0zy87prmkznt7jek',
 'eip_address': '14.103.150.79',
 'request_id': '20250214192603C3AF487A9C6F384A0FD3'}
正在创建公网访问地址...
等待30秒后重试...
公网访问端点创建成功:
  - 域名: postgres-f071be4dc0b1-public.rds-pg.volces.com
  - 端口: 5432
  - 完整连接地址: postgres-f071be4dc0b1-public.rds-pg.volces.com:5432
2025-02-14 19:26:36,204 - INFO - 白名单 default-whitelist 创建成功
2025-02-14 19:26:36,513 - INFO - 白名单 office-whitelist 创建成功
2025-02-14 19:26:37,019 - INFO - 白名单 vpc-whitelist 创建成功
2025-02-14 19:26:37,927 - INFO - 当前实例状态: Running
2025-02-14 19:26:38,187 - INFO - 白名单 ID: acl-2ff7551d6f78401d8705ea05189e6136 绑定成功
2025-02-14 19:26:48,746 - INFO - 白名单 ID: acl-30f8cb69d1b8496288e4a8d298c7186e 绑定成功
2025-02-14 19:26:59,211 - INFO - 白名单 ID: acl-8523a05acf2c43429bba148f260e3871 绑定成功
当前实例状态: Running
账号 testuser 创建成功
账号 readonly_user 创建成功
2025-02-14 19:27:10,805 - INFO - 当前实例没有已存在的数据库
2025-02-14 19:27:11,840 - INFO - 数据库 testdb 创建成功
2025-02-14 19:27:12,932 - INFO - 数据库 devdb 创建成功

数据库: testdb
Schema列表:
  - pg_catalog (已存在)
  - information_schema (已存在)
  - public (已存在)
  - test_schema_1 (新创建)
  - test_schema_2 (新创建)
  - test_schema_3 (新创建)
  - test_schema_4 (新创建)

数据库: devdb
Schema列表:
  - pg_catalog (已存在)
  - information_schema (已存在)
  - public (已存在)
  - dev_schema (新创建)
2025-02-14 19:27:15,206 - INFO - 备份策略修改成功
2025-02-14 19:27:15,206 - INFO - 成功完成所有操作！
2025-02-14 19:27:15,206 - INFO - PostgreSQL实例ID: postgres-f071be4dc0b1
2025-02-14 19:27:15,207 - INFO - EIP地址: 14.103.150.79
2025-02-14 19:27:15,207 - INFO - 数据库列表: testdb, devdb
2025-02-14 19:27:15,207 - INFO - 主用户名: testuser
2025-02-14 19:27:15,207 - INFO - 主用户密码: Wl19950707
2025-02-14 19:27:15,207 - INFO - 只读用户名: readonly_user
2025-02-14 19:27:15,207 - INFO - 只读用户密码: Readonly123
2025-02-14 19:27:15,207 - INFO - Schema列表: testdb.test_schema_1, testdb.test_schema_2, testdb.test_schema_3, testdb.test_schema_4, devdb.dev_schema
```