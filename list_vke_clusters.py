#!/usr/bin/env python
# -*- coding: utf-8 -*-

import volcenginesdkcore
import volcenginesdkvke
from volcenginesdkvke.models.list_clusters_request import ListClustersRequest
from configs.api_config import api_config

def list_clusters(ak=None, sk=None, region='cn-shanghai'):
    """列出所有集群的信息
    
    Args:
        ak (str): 访问密钥ID
        sk (str): 访问密钥密码
        region (str): 区域，默认为上海
        
    Returns:
        list: 集群信息列表
    """
    try:
        # 初始化配置
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = ak or api_config['ak']
        configuration.sk = sk or api_config['sk']
        configuration.region = region or api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)
        
        # 初始化VKE API客户端
        vke_api = volcenginesdkvke.VKEApi()
        
        # 创建请求
        list_clusters_request = ListClustersRequest()
        
        # 发送请求获取集群列表
        response = vke_api.list_clusters(list_clusters_request)
        
        if response and response.items:
            return response.items
        return []
        
    except Exception as e:
        print(f'获取集群列表时发生错误: {str(e)}')
        return []

def save_cluster_info(clusters, output_file='./logs/clusters_info.txt'):
    """保存集群信息到文件
    
    Args:
        clusters (list): 集群信息列表
        output_file (str): 输出文件路径
    """
    try:
        # 初始化VKE API客户端
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)
        vke_api = volcenginesdkvke.VKEApi()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f'找到 {len(clusters)} 个集群\n\n')
            
            for cluster in clusters:
                f.write('=' * 50 + '\n')
                f.write(f'集群名称: {cluster.name}\n')
                f.write(f'集群ID: {cluster.id}\n')
                f.write(f'Kubernetes版本: {cluster.kubernetes_version}\n')
                f.write(f'创建时间: {cluster.create_time}\n')
                f.write(f'集群状态: {cluster.status.phase}\n')
                f.write(f'描述: {cluster.description}\n')
                
                # 网络配置
                f.write('\n网络配置:\n')
                f.write(f'VPC ID: {cluster.cluster_config.vpc_id}\n')
                f.write(f'子网IDs: {cluster.cluster_config.subnet_ids}\n')
                f.write(f'服务CIDR: {cluster.services_config.service_cidrsv4}\n')
                f.write(f'Pod网络模式: {cluster.pods_config.pod_network_mode}\n')
                
                # 访问配置
                f.write('\n访问配置:\n')
                f.write(f'公网访问: {"已开启" if cluster.cluster_config.api_server_public_access_enabled else "未开启"}\n')
                f.write(f'默认公网访问: {"已开启" if cluster.cluster_config.resource_public_access_default_enabled else "未开启"}\n')
                
                # 获取并保存kubeconfig
                f.write('\nKubeconfig配置:\n')
                try:
                    # 检查是否已存在public类型的kubeconfig
                    kubeconfig_req_filter = volcenginesdkvke.FilterForListKubeconfigsInput(
                        cluster_ids=[cluster.id],
                        types=["Public"]
                    )
                    kubeconfig_request = volcenginesdkvke.ListKubeconfigsRequest(
                        filter=kubeconfig_req_filter,
                        page_number=1,
                        page_size=100,
                    )
                    kubeconfig_response = vke_api.list_kubeconfigs(kubeconfig_request)
                    
                    # 如果没有找到现有的public kubeconfig，则创建新的
                    if not (kubeconfig_response and kubeconfig_response.items):
                        create_kubeconfig_request = volcenginesdkvke.CreateKubeconfigRequest(
                            cluster_id=cluster.id,
                            type="Public",
                            valid_duration=867240
                        )
                        vke_api.create_kubeconfig(create_kubeconfig_request)
                        # 重新获取创建的kubeconfig
                        kubeconfig_response = vke_api.list_kubeconfigs(kubeconfig_request)
                    
                    if kubeconfig_response and kubeconfig_response.items:
                        for kubeconfig in kubeconfig_response.items:
                            f.write(kubeconfig.kubeconfig + '\n')
                    else:
                        f.write('无法获取kubeconfig配置\n')
                except Exception as e:
                    f.write(f'获取kubeconfig时发生错误: {str(e)}\n')
                
                f.write('\n\n' + '=' * 50 + '\n\n')
                
        print(f'集群信息已保存到: {output_file}')
        return True
    except Exception as e:
        print(f'保存集群信息时发生错误: {str(e)}')
        return False

def main():
    # 获取集群列表
    clusters = list_clusters()
    
    if clusters:
        print(f'找到 {len(clusters)} 个集群')
        
        # 打印基本信息到控制台
        for cluster in clusters:
            print(f'\n集群: {cluster.name} (ID: {cluster.id})')
            print(f'状态: {cluster.status.phase}')
        
        # 保存详细信息到文件
        save_cluster_info(clusters)
    else:
        print('未找到任何集群')

if __name__ == '__main__':
    main()