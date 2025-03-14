import volcenginesdkcore
import volcenginesdkrdspostgresql
import volcenginesdkmongodb
import volcenginesdkescloud
import volcenginesdkkafka
import volcenginesdkredis
from volcenginesdkcore.rest import ApiException
from base_resource_manager import BaseResourceManager
from configs.api_config import api_config
from datetime import datetime
import os

class DatabaseResourceManager(BaseResourceManager):
    def __init__(self):
        super().__init__("Database")
        self.rds_api = volcenginesdkrdspostgresql.RDSPOSTGRESQLApi()
        self.mongodb_api = volcenginesdkmongodb.MONGODBApi()
        self.es_api = volcenginesdkescloud.ESCLOUDApi()
        self.kafka_api = volcenginesdkkafka.KAFKAApi()
        self.redis_api = volcenginesdkredis.REDISApi()

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)

    def list_and_write_resources(self):
        """列出所有数据库和消息队列资源并写入文件"""
        try:
            resources = self.list_resources()
            # 确保 logs 目录存在
            os.makedirs('logs', exist_ok=True)
            # 写入到 logs 目录下的 database_info.md 文件
            with open('logs/database_info.md', 'w', encoding='utf-8') as f:
                self._write_resources_to_file(f, resources)
            return True
        except Exception as e:
            self.logger.error(f"获取和写入数据库资源信息时发生错误: {e}")
            return False

    def list_resources(self):
        """列出所有数据库和消息队列资源"""
        resources = {
            'postgresql': self._list_postgresql_instances(),
            'mongodb': self._list_mongodb_instances(),
            'elasticsearch': self._list_es_instances(),
            'kafka': self._list_kafka_instances(),
            'redis': self._list_redis_instances()
        }
        return resources

    def _list_postgresql_instances(self):
        """列出所有PostgreSQL实例"""
        try:
            request = volcenginesdkrdspostgresql.DescribeDBInstancesRequest()
            request.page_number = 1
            request.page_size = 100
            response = self.rds_api.describe_db_instances(request)
            
            if not hasattr(response, 'instances'):
                self.logger.info("未找到任何PostgreSQL实例")
                return []
            
            return [self._format_postgresql_info(instance) for instance in response.instances]
            
        except ApiException as e:
            self.logger.error(f"获取PostgreSQL实例列表时发生异常: {e}")
            return []

    def _list_mongodb_instances(self):
        """列出所有MongoDB实例"""
        try:
            request = volcenginesdkmongodb.DescribeDBInstancesRequest()
            request.page_number = 1
            request.page_size = 100
            response = self.mongodb_api.describe_db_instances(request)
            # print(response)
            if not hasattr(response, 'db_instances'):
                self.logger.info("未找到任何MongoDB实例")
                return []
            
            return [self._format_mongodb_info(instance) for instance in response.db_instances]
            
        except ApiException as e:
            self.logger.error(f"获取MongoDB实例列表时发生异常: {e}")
            return []

    def _list_es_instances(self):
        """列出所有Elasticsearch实例"""
        try:
            request = volcenginesdkescloud.DescribeInstancesRequest()
            request.page_number = 1
            request.page_size = 100
            response = self.es_api.describe_instances(request)
            # print(response)
            if not hasattr(response, 'instances'):
                self.logger.info("未找到任何Elasticsearch实例")
                return []
            
            return [self._format_es_info(instance) for instance in response.instances]
            
        except ApiException as e:
            self.logger.error(f"获取Elasticsearch实例列表时发生异常: {e}")
            return []

    def _list_kafka_instances(self):
        """列出所有Kafka实例"""
        try:
            request = volcenginesdkkafka.DescribeInstancesRequest(
                page_number = 1,
                page_size = 100,
            )
            response = self.kafka_api.describe_instances(request)
            
            if not hasattr(response, 'instances_info'):
                self.logger.info("未找到任何Kafka实例")
                return []
            
            return [self._format_kafka_info(instance) for instance in response.instances_info]
            
        except ApiException as e:
            self.logger.error(f"获取Kafka实例列表时发生异常: {e}")
            return []

    def _list_redis_instances(self):
        """列出所有Redis实例"""
        try:
            request = volcenginesdkredis.DescribeDBInstancesRequest(
                page_number = 1,
                page_size=100,
            )

            response = self.redis_api.describe_db_instances(request)
            # print(response)
            if not hasattr(response, 'instances'):
                self.logger.info("未找到任何Redis实例")
                return []
            
            return [self._format_redis_info(instance) for instance in response.instances]
            
        except ApiException as e:
            self.logger.error(f"获取Redis实例列表时发生异常: {e}")
            return []

    def _get_redis_instance_detail(self, instance_id):
        """获取Redis实例的详细信息，包括公网地址和子网ID等"""
        try:
            endpoint_request = volcenginesdkredis.DescribeDBInstanceDetailRequest(
                instance_id=instance_id
            )
            endpoint_response = self.redis_api.describe_db_instance_detail(endpoint_request)
            # print(endpoint_response)
            if hasattr(endpoint_response, 'visit_addrs'):
                return endpoint_response
            return None
        except Exception as e:
            self.logger.error(f"获取Redis实例 {instance_id} 的详细信息时发生错误: {e}")
            return None

    def _get_mongodb_public_endpoint(self, instance_id):
        """获取MongoDB实例的公网连接地址"""
        try:
            endpoint_request = volcenginesdkmongodb.DescribeDBEndpointRequest(
                instance_id=instance_id
            )
            endpoint_response = self.mongodb_api.describe_db_endpoint(endpoint_request)
            if hasattr(endpoint_response, 'db_endpoints') and endpoint_response.db_endpoints:
                for endpoint in endpoint_response.db_endpoints:
                    if endpoint.network_type == 'Public' and endpoint.db_addresses:
                        # 返回第一个地址的域名
                        return endpoint.db_addresses[0].address_domain
            return ''
        except Exception as e:
            self.logger.error(f"获取MongoDB实例 {instance_id} 的公网地址时发生错误: {e}")
            return ''

    def _format_postgresql_info(self, instance):
        """格式化PostgreSQL实例信息"""
        # 获取连接信息
        connection_info = {
            'public_endpoint': '',
            'public_port': '',
            'private_endpoint': '',
            'private_port': ''
        }
        if hasattr(instance, 'address_object') and instance.address_object:
            for addr in instance.address_object:
                if addr.network_type == 'Public':
                    connection_info['public_endpoint'] = addr.domain
                    connection_info['public_port'] = addr.port
                elif addr.network_type == 'Private':
                    connection_info['private_endpoint'] = addr.domain
                    connection_info['private_port'] = addr.port

        # 获取计费信息
        charge_info = {
            'charge_type': '',
            'expire_time': '',
            'create_time': ''
        }
        if hasattr(instance, 'charge_detail'):
            charge_info['charge_type'] = instance.charge_detail.charge_type
            charge_info['expire_time'] = instance.charge_detail.charge_end_time
            charge_info['create_time'] = instance.charge_detail.charge_start_time

        return {
            'instance_id': instance.instance_id,
            'instance_name': instance.instance_name,
            'engine': 'PostgreSQL',
            'engine_version': instance.db_engine_version,
            'instance_type': instance.instance_type,
            'instance_status': instance.instance_status,
            'create_time': charge_info['create_time'],
            'expire_time': charge_info['expire_time'],
            'charge_type': charge_info['charge_type'],
            'vpc_id': instance.vpc_id,
            'subnet_id': instance.subnet_id,
            'zone_id': instance.zone_id,
            'storage_space': instance.storage_space,
            'storage_type': instance.storage_type,
            'connection_info': connection_info,
            'tags': getattr(instance, 'tags', []),
            'node_number': getattr(instance, 'node_number', 1),
            'node_spec': getattr(instance, 'node_spec', ''),
            'project_name': getattr(instance, 'project_name', 'default')
        }

    def _format_mongodb_info(self, instance):
        """格式化MongoDB实例信息"""
        # 获取连接信息
        connection_info = {
            'public_endpoint': self._get_mongodb_public_endpoint(instance.instance_id),
            'public_port': '3717',
            'private_endpoint': instance.private_endpoint,
            'private_port': '3717'
        }

        return {
            'instance_id': instance.instance_id,
            'instance_name': instance.instance_name,
            'engine': 'MongoDB',
            'engine_version': instance.db_engine_version_str,
            'instance_type': instance.instance_type,
            'instance_status': instance.instance_status,
            'create_time': instance.create_time,
            'expire_time': instance.expired_time,
            'charge_type': instance.charge_type,
            'vpc_id': instance.vpc_id,
            'subnet_id': instance.subnet_id,
            'zone_id': instance.zone_id,
            'storage_type': instance.storage_type,
            'connection_info': connection_info,
            'tags': getattr(instance, 'tags', []),
            'project_name': getattr(instance, 'project_name', 'default'),
            'config_servers_id': getattr(instance, 'config_servers_id', ''),
            'mongos_id': getattr(instance, 'mongos_id', ''),
            'update_time': getattr(instance, 'update_time', '')
        }

    def _format_es_info(self, instance):
        """格式化Elasticsearch实例信息"""
        # 获取连接信息
        connection_info = {
            'public_endpoint': instance.es_public_endpoint,
            'public_port': '9200',
            'private_endpoint': instance.es_private_endpoint,
            'private_port': '9200'
        }

        # 获取实例配置信息
        instance_config = instance.instance_configuration
        charge_info = {
            'charge_type': instance_config.charge_type if instance_config else '',
            'expire_time': instance.expire_date,
            'create_time': instance.create_time
        }

        # 获取节点信息
        node_info = {
            'total_nodes': instance.total_nodes,
            'master_nodes': instance_config.master_node_number if instance_config else 0,
            'hot_nodes': instance_config.hot_node_number if instance_config else 0,
            'warm_nodes': instance_config.warm_node_number if instance_config else 0,
            'cold_nodes': instance_config.cold_node_number if instance_config else 0,
            'kibana_nodes': instance_config.kibana_node_number if instance_config else 0
        }

        # 获取存储信息
        storage_info = {
            'hot_node_storage': instance_config.hot_node_storage_spec.size if instance_config and instance_config.hot_node_storage_spec else 0,
            'master_node_storage': instance_config.master_node_storage_spec.size if instance_config and instance_config.master_node_storage_spec else 0
        }

        return {
            'instance_id': instance.instance_id,
            'instance_name': instance.instance_configuration.instance_name if instance_config else '',
            'engine': 'Elasticsearch',
            'engine_version': instance.instance_configuration.version if instance_config else '',
            'instance_type': f"{instance_config.hot_node_resource_spec.display_name if instance_config and instance_config.hot_node_resource_spec else ''}",
            'instance_status': instance.status,
            'create_time': charge_info['create_time'],
            'expire_time': charge_info['expire_time'],
            'charge_type': charge_info['charge_type'],
            'vpc_id': instance.instance_configuration.vpc.vpc_id if instance_config and instance_config.vpc else '',
            'subnet_id': instance.instance_configuration.subnet.subnet_id if instance_config and instance_config.subnet else '',
            'zone_id': instance.instance_configuration.zone_id if instance_config else '',
            'storage_space': storage_info['hot_node_storage'] * node_info['hot_nodes'],
            'storage_type': instance_config.hot_node_storage_spec.display_name if instance_config and instance_config.hot_node_storage_spec else '',
            'connection_info': connection_info,
            'tags': instance.resource_tags if hasattr(instance, 'resource_tags') else [],
            'node_number': node_info['total_nodes'],
            'node_spec': f"{instance_config.hot_node_resource_spec.display_name if instance_config and instance_config.hot_node_resource_spec else ''}",
            'kibana_endpoint': instance.kibana_public_domain if instance.kibana_public_domain else instance.kibana_private_domain,
            'cerebro_endpoint': instance.cerebro_public_domain if instance.cerebro_public_domain else instance.cerebro_private_domain,
            'maintenance_time': instance.maintenance_time,
            'deletion_protection': instance.deletion_protection
        }

    def _get_kafka_instance_detail(self, instance_id):
        """获取Kafka实例的详细信息，包括连接信息和计费信息等"""
        try:
            detail_request = volcenginesdkkafka.DescribeInstanceDetailRequest(
                instance_id=instance_id
            )
            detail_response = self.kafka_api.describe_instance_detail(detail_request)
            # print(detail_response)
            if hasattr(detail_response, 'basic_instance_info'):
                return detail_response
            return None
        except Exception as e:
            self.logger.error(f"获取Kafka实例 {instance_id} 的详细信息时发生错误: {e}")
            return None

    def _format_kafka_info(self, instance):
        """格式化Kafka实例信息"""
        # 获取实例详细信息
        instance_detail = self._get_kafka_instance_detail(instance.instance_id)
        # print(instance_detail)
        if not instance_detail:
            # 如果获取详情失败，使用基本信息
            charge_detail = getattr(instance, 'charge_detail', None)
            return {
                'instance_id': instance.instance_id,
                'instance_name': instance.instance_name,
                'engine_version': instance.version,
                'instance_type': instance.compute_spec,
                'instance_status': instance.instance_status,
                'create_time': instance.create_time,
                'expire_time': getattr(charge_detail, 'charge_expire_time', '') if charge_detail else '',
                'charge_type': getattr(charge_detail, 'charge_type', '') if charge_detail else '',
                'vpc_id': instance.vpc_id,
                'subnet_id': instance.subnet_id,
                'zone_id': instance.zone_id,
                'storage_space': instance.storage_space,
                'storage_type': instance.storage_type,
                'connection_info': {
                    'public_endpoint': '',
                    'public_port': '',
                    'private_endpoint': '',
                    'private_port': ''
                },
                'tags': getattr(instance, 'tags', []),
                'default_partition_number': getattr(instance, 'default_partition_number', 0),
                'default_replica_factor': getattr(instance, 'default_replica_factor', 0),
                'used_topic_number': getattr(instance, 'used_topic_number', 0),
                'used_group_number': getattr(instance, 'used_group_number', 0),
                'used_partition_number': getattr(instance, 'used_partition_number', 0),
                'usable_topic_number': getattr(instance, 'usable_topic_number', 0),
                'usable_group_number': getattr(instance, 'usable_group_number', 0),
                'usable_partition_number': getattr(instance, 'usable_partition_number', 0),
                'parameters': ''
            }

        # 获取基础实例信息
        basic_info = instance_detail.basic_instance_info
        
        # 获取连接信息
        connection_info = {
            'public_endpoint': '',
            'public_port': '',
            'private_endpoint': '',
            'private_port': ''
        }
        if hasattr(instance_detail, 'connection_info') and instance_detail.connection_info:
            for conn in instance_detail.connection_info:
                if conn.endpoint_type == 'PLAINTEXT':
                    connection_info['private_endpoint'] = conn.internal_endpoint.split(':')[0]
                    connection_info['private_port'] = conn.internal_endpoint.split(':')[1]
                    connection_info['public_endpoint'] = conn.public_endpoint if conn.public_endpoint else ''
                    connection_info['public_port'] = conn.internal_endpoint.split(':')[1] if conn.public_endpoint else ''

        # 获取计费信息
        charge_info = instance_detail.charge_detail

        return {
            'instance_id': basic_info.instance_id,
            'instance_name': basic_info.instance_name,
            'engine_version': basic_info.version,
            'instance_type': basic_info.compute_spec,
            'instance_status': basic_info.instance_status,
            'create_time': charge_info.charge_start_time,
            'expire_time': charge_info.charge_expire_time,
            'charge_type': charge_info.charge_type,
            'vpc_id': basic_info.vpc_id,
            'subnet_id': basic_info.subnet_id,
            'zone_id': basic_info.zone_id,
            'storage_space': basic_info.storage_space,
            'storage_type': basic_info.storage_type,
            'connection_info': connection_info,
            'tags': basic_info.tags if basic_info.tags else [],
            'default_partition_number': getattr(basic_info, 'default_partition_number', 0),
            'default_replica_factor': getattr(basic_info, 'default_replica_factor', 0),
            'used_topic_number': basic_info.used_topic_number,
            'used_group_number': basic_info.used_group_number,
            'used_partition_number': basic_info.used_partition_number,
            'usable_topic_number': getattr(basic_info, 'usable_topic_number', 0),
            'usable_group_number': basic_info.usable_group_number,
            'usable_partition_number': basic_info.usable_partition_number,
            'parameters': instance_detail.parameters
        }

    def _format_redis_info(self, instance):
        """格式化Redis实例信息"""
        # 获取实例详细信息
        instance_detail = self._get_redis_instance_detail(instance.instance_id)
        # print(instance_detail)
        # 获取连接信息
        connection_info = {
            'public_endpoint': next((addr.address for addr in instance_detail.visit_addrs if addr.addr_type == 'Public'), ''),
            'public_port': next((addr.port for addr in instance_detail.visit_addrs if addr.addr_type == 'Public'), ''),
            'private_endpoint': instance.private_address,
            'private_port': '6379'
        }
        
        # 从详细信息中获取公网地址
        if instance_detail and hasattr(instance_detail, 'visit_addrs'):
            for addr in instance_detail.visit_addrs:
                if addr.addr_type == 'Public':
                    connection_info['public_endpoint'] = addr.address

        return {
            'instance_id': instance.instance_id,
            'instance_name': instance.instance_name,
            'engine_version': instance.engine_version,
            'instance_type': instance.instance_class,
            'instance_status': instance.status,
            'create_time': instance.create_time,
            'expire_time': instance.expired_time,
            'charge_type': instance.charge_type,
            'vpc_id': instance.vpc_id,
            'subnet_id': instance_detail.subnet_id if instance_detail else '',  # 从详细接口获取
            'zone_id': ','.join(instance.zone_ids),
            'storage_space': instance.capacity.total,
            'storage_type': instance.data_layout,
            'connection_info': connection_info,
            'tags': getattr(instance, 'tags', []),
            'node_number': instance.node_number,
            'shard_number': instance.shard_number,
            'shard_capacity': instance.shard_capacity,
            'service_type': instance.service_type,
            'multi_az': instance.multi_az,
            'deletion_protection': instance.deletion_protection
        }

    def _write_resources_to_file(self, file, resources):
        """将数据库资源信息写入不同的文件"""
        try:
            # 确保 logs 目录存在
            os.makedirs('logs', exist_ok=True)
            
            # 写入PostgreSQL实例信息
            if resources['postgresql']:
                with open('logs/postgresql_info.md', 'w', encoding='utf-8') as f:
                    f.write("# PostgreSQL实例信息记录\n\n")
                    f.write("## 记录时间\n")
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("## PostgreSQL实例列表\n")
                    f.write("---\n\n")
                    f.write("| 实例名称 | 实例ID | 引擎版本 | 实例类型 | 状态 | 创建时间 | 过期时间 | 计费类型 | VPC ID | 子网ID | 可用区 | 存储空间(GB) | 存储类型 | 公网地址 | 公网端口 | 内网地址 | 内网端口 | 标签 |\n")
                    f.write("|----------|---------|----------|----------|------|----------|----------|----------|---------|---------|--------|--------------|----------|----------|----------|----------|----------|------|\n")
                    for instance in resources['postgresql']:
                        tags_str = "; ".join([f"{tag.key}: {tag.value}" for tag in instance['tags']]) if instance['tags'] else ""
                        f.write(f"| {instance['instance_name']} | {instance['instance_id']} | {instance['engine_version']} | {instance['instance_type']} | {instance['instance_status']} | {instance['create_time']} | {instance['expire_time']} | {instance['charge_type']} | {instance['vpc_id']} | {instance['subnet_id']} | {instance['zone_id']} | {instance['storage_space']} | {instance['storage_type']} | {instance['connection_info']['public_endpoint']} | {instance['connection_info']['public_port']} | {instance['connection_info']['private_endpoint']} | {instance['connection_info']['private_port']} | {tags_str} |\n")

            # 写入MongoDB实例信息
            if resources['mongodb']:
                with open('logs/mongodb_info.md', 'w', encoding='utf-8') as f:
                    f.write("# MongoDB实例信息记录\n\n")
                    f.write("## 记录时间\n")
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("## MongoDB实例列表\n")
                    f.write("---\n\n")
                    f.write("| 实例名称 | 实例ID | 引擎版本 | 实例类型 | 状态 | 创建时间 | 过期时间 | 计费类型 | VPC ID | 子网ID | 可用区 | 存储类型 | 公网地址 | 公网端口 | 内网地址 | 内网端口 | 标签 |\n")
                    f.write("|----------|---------|----------|----------|------|----------|----------|----------|---------|---------|--------|----------|----------|----------|----------|----------|----------|------|\n")
                    for instance in resources['mongodb']:
                        tags_str = "; ".join([f"{tag.key}: {tag.value}" for tag in instance['tags']]) if instance['tags'] else ""
                        f.write(f"| {instance['instance_name']} | {instance['instance_id']} | {instance['engine_version']} | {instance['instance_type']} | {instance['instance_status']} | {instance['create_time']} | {instance['expire_time']} | {instance['charge_type']} | {instance['vpc_id']} | {instance['subnet_id']} | {instance['zone_id']} | {instance['storage_type']} | {instance['connection_info']['public_endpoint']} | {instance['connection_info']['public_port']} | {instance['connection_info']['private_endpoint']} | {instance['connection_info']['private_port']} | {tags_str} |\n")

            # 写入Elasticsearch实例信息
            if resources['elasticsearch']:
                with open('logs/elasticsearch_info.md', 'w', encoding='utf-8') as f:
                    f.write("# Elasticsearch实例信息记录\n\n")
                    f.write("## 记录时间\n")
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("## Elasticsearch实例列表\n")
                    f.write("---\n\n")
                    f.write("| 实例名称 | 实例ID | 引擎版本 | 实例类型 | 状态 | 创建时间 | 过期时间 | 计费类型 | VPC ID | 子网ID | 可用区 | 存储空间(GB) | 存储类型 | 公网地址 | 公网端口 | 内网地址 | 内网端口 | Kibana地址 | Cerebro地址 | 维护时间 | 删除保护 | 标签 |\n")
                    f.write("|----------|---------|----------|----------|------|----------|----------|----------|---------|---------|--------|--------------|----------|----------|----------|----------|----------|------------|------------|----------|------------|------|\n")
                    for instance in resources['elasticsearch']:
                        tags_str = "; ".join([f"{tag.key}: {tag.value}" for tag in instance['tags']]) if instance['tags'] else ""
                        f.write(f"| {instance['instance_name']} | {instance['instance_id']} | {instance['engine_version']} | {instance['instance_type']} | {instance['instance_status']} | {instance['create_time']} | {instance['expire_time']} | {instance['charge_type']} | {instance['vpc_id']} | {instance['subnet_id']} | {instance['zone_id']} | {instance['storage_space']} | {instance['storage_type']} | {instance['connection_info']['public_endpoint']} | {instance['connection_info']['public_port']} | {instance['connection_info']['private_endpoint']} | {instance['connection_info']['private_port']} | {instance['kibana_endpoint']} | {instance['cerebro_endpoint']} | {instance['maintenance_time']} | {instance['deletion_protection']} | {tags_str} |\n")

            # 写入Kafka实例信息
            if resources['kafka']:
                with open('logs/kafka_info.md', 'w', encoding='utf-8') as f:
                    f.write("# Kafka实例信息记录\n\n")
                    f.write("## 记录时间\n")
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("## Kafka实例列表\n")
                    f.write("---\n\n")
                    f.write("| 实例名称 | 实例ID | 引擎版本 | 实例类型 | 状态 | 创建时间 | 过期时间 | 计费类型 | VPC ID | 子网ID | 可用区 | 存储空间(GB) | 存储类型 | 公网地址 | 公网端口 | 内网地址 | 内网端口 | 标签 |\n")
                    f.write("|----------|---------|----------|----------|------|----------|----------|----------|---------|---------|--------|--------------|----------|----------|----------|----------|----------|------|\n")
                    for instance in resources['kafka']:
                        tags_str = "; ".join([f"{tag.key}: {tag.value}" for tag in instance['tags']]) if instance['tags'] else ""
                        f.write(f"| {instance['instance_name']} | {instance['instance_id']} | {instance['engine_version']} | {instance['instance_type']} | {instance['instance_status']} | {instance['create_time']} | {instance['expire_time']} | {instance['charge_type']} | {instance['vpc_id']} | {instance['subnet_id']} | {instance['zone_id']} | {instance['storage_space']} | {instance['storage_type']} | {instance['connection_info']['public_endpoint']} | {instance['connection_info']['public_port']} | {instance['connection_info']['private_endpoint']} | {instance['connection_info']['private_port']} | {tags_str} |\n")

            # 写入Redis实例信息
            if resources['redis']:
                with open('logs/redis_info.md', 'w', encoding='utf-8') as f:
                    f.write("# Redis实例信息记录\n\n")
                    f.write("## 记录时间\n")
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("## Redis实例列表\n")
                    f.write("---\n\n")
                    f.write("| 实例名称 | 实例ID | 引擎版本 | 实例类型 | 状态 | 创建时间 | 过期时间 | 计费类型 | VPC ID | 子网ID | 可用区 | 存储空间(GB) | 存储类型 | 公网地址 | 公网端口 | 内网地址 | 内网端口 | 标签 |\n")
                    f.write("|----------|---------|----------|----------|------|----------|----------|----------|---------|---------|--------|--------------|----------|----------|----------|----------|----------|------|\n")
                    for instance in resources['redis']:
                        tags_str = "; ".join([f"{tag.key}: {tag.value}" for tag in instance['tags']]) if instance['tags'] else ""
                        f.write(f"| {instance['instance_name']} | {instance['instance_id']} | {instance['engine_version']} | {instance['instance_type']} | {instance['instance_status']} | {instance['create_time']} | {instance['expire_time']} | {instance['charge_type']} | {instance['vpc_id']} | {instance['subnet_id']} | {instance['zone_id']} | {instance['storage_space']} | {instance['storage_type']} | {instance['connection_info']['public_endpoint']} | {instance['connection_info']['public_port']} | {instance['connection_info']['private_endpoint']} | {instance['connection_info']['private_port']} | {tags_str} |\n")

            # 创建一个索引文件，列出所有生成的报告
            with open('logs/database_reports_index.md', 'w', encoding='utf-8') as f:
                f.write("# 数据库资源报告索引\n\n")
                f.write("## 生成时间\n")
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## 报告列表\n")
                f.write("---\n\n")
                if resources['postgresql']:
                    f.write("- [PostgreSQL实例报告](postgresql_info.md)\n")
                if resources['mongodb']:
                    f.write("- [MongoDB实例报告](mongodb_info.md)\n")
                if resources['elasticsearch']:
                    f.write("- [Elasticsearch实例报告](elasticsearch_info.md)\n")
                if resources['kafka']:
                    f.write("- [Kafka实例报告](kafka_info.md)\n")
                if resources['redis']:
                    f.write("- [Redis实例报告](redis_info.md)\n")

        except Exception as e:
            self.logger.error(f"写入数据库资源信息到文件时发生错误: {e}")
            raise

def main():
    try:
        manager = DatabaseResourceManager()
        if manager.list_and_write_resources():
            print("成功完成所有数据库和消息队列资源信息的收集和记录")
        else:
            print("获取和写入数据库资源信息时发生错误")
    except Exception as e:
        print(f"执行过程中发生错误: {e}")

if __name__ == "__main__":
    main() 