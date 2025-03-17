#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
python batch_update_cdn_config.py \
    --domains eve-cn-dev-cms-object-cdn.yourdomain.com \
    --http2 true \
    --https true \
    --ipv6 true \
    --service-type web \
    --service-region chinese_mainland \
    --origin-protocol followclient

python update_cdn_domain.py \
    --domain eve-cn-dev-cms-object-cdn.yourdomain.com \
    --http2 true \
    --https true \
    --ipv6 true

python list_cdn_domains.py \
    --page-size 10 \
    --page-number 1
'''
import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional

from sign import APIConfig, APIClient, APIError


class CDNConfig(APIConfig):
    """CDN API配置类，继承自APIConfig"""
    
    def __init__(self, action: str = 'BatchUpdateCdnConfig'):
        # 设置CDN服务的默认参数
        os.environ.setdefault('Service', 'CDN')
        os.environ.setdefault('Version', '2021-03-01')
        os.environ.setdefault('Region', 'cn-shanghai')
        os.environ.setdefault('Action', action)
        os.environ.setdefault('method', 'POST')
        super().__init__()


def update_cdn_domain(
    domain: str,
    http2: bool = True,
    https: bool = None,
    ipv6: bool = None,
    service_type: Optional[str] = None,
    service_region: Optional[str] = None,
    origin_protocol: Optional[str] = None,
    project: str = 'default'
) -> Dict[str, Any]:
    """更新单个CDN域名配置
    
    Args:
        domain: CDN域名
        http2: 是否开启HTTP2
        https: 是否开启HTTPS
        ipv6: 是否开启IPv6
        service_type: 服务类型，可选值: web, download, video
        service_region: 服务区域，可选值: chinese_mainland, global, overseas
        origin_protocol: 回源协议，可选值: http, https, followclient
        project: 项目名称
        
    Returns:
        Dict: API响应结果
    """
    # 设置API参数
    api_params = {
        "Domains": [domain],
    }
    
    # 配置HTTPS
    if http2 is not None:
        https_config = {"Switch": http2}
        https_config["HTTP2"] = http2
        api_params["HTTPS"] = https_config
    
    # 配置IPv6
    if ipv6 is not None:
        api_params["IPv6"] = {"Switch": ipv6}
    
    # 配置服务类型
    if service_type:
        api_params["ServiceType"] = service_type
    
    # 配置服务区域
    if service_region:
        api_params["ServiceRegion"] = service_region
    
    # 配置回源协议
    if origin_protocol:
        api_params["OriginProtocol"] = origin_protocol
    
    # 将API参数设置到环境变量
    os.environ['API_PARAMS'] = json.dumps(api_params)
    print(os.environ['API_PARAMS'])
    os.environ['Action'] = 'BatchUpdateCdnConfig'
    
    try:
        # 创建CDN配置和API客户端
        config = CDNConfig('BatchUpdateCdnConfig')
        client = APIClient(config)
        
        # 发送请求
        response = client.send_request()
        print(f"成功更新CDN域名配置: {domain}")
        return response
    except (ValueError, APIError) as e:
        print(f"更新CDN域名配置失败: {str(e)}")
        return {"error": str(e)}


def list_cdn_domains(
    page_size: int = 10,
    page_number: int = 1,
    project: str = 'default'
) -> Dict[str, Any]:
    """获取CDN域名列表
    
    Args:
        page_size: 每页数量
        page_number: 页码
        project: 项目名称
        
    Returns:
        Dict: API响应结果
    """
    # 设置API参数
    api_params = {
        "PageSize": page_size,
        "PageNumber": page_number,
        "Project": project
    }
    
    # 将API参数设置到环境变量
    os.environ['API_PARAMS'] = json.dumps(api_params)
    os.environ['Action'] = 'ListCdnDomains'
    
    try:
        # 创建CDN配置和API客户端
        config = CDNConfig('ListCdnDomains')
        client = APIClient(config)
        
        # 发送请求
        response = client.send_request()
        print(f"成功获取CDN域名列表")
        return response
    except (ValueError, APIError) as e:
        print(f"获取CDN域名列表失败: {str(e)}")
        return {"error": str(e)}


def batch_update_cdn_config(
    domains: List[str],
    http2: bool = True,
    https: bool = None,
    ipv6: bool = None,
    service_type: Optional[str] = None,
    service_region: Optional[str] = None,
    origin_protocol: Optional[str] = None,
    project: str = 'default'
) -> Dict[str, Any]:
    """批量更新CDN配置
    
    Args:
        domains: CDN域名列表
        http2: 是否开启HTTP2
        https: 是否开启HTTPS
        ipv6: 是否开启IPv6
        service_type: 服务类型，可选值: web, download, video
        service_region: 服务区域，可选值: chinese_mainland, global, overseas
        origin_protocol: 回源协议，可选值: http, https, followclient
        project: 项目名称
        
    Returns:
        Dict: API响应结果
    """
    # 设置API参数
    api_params = {
        "Domains": domains,
        "Project": project
    }
    
    # 配置HTTPS
    if https is not None:
        https_config = {"Switch": https}
        if https:
            https_config["HTTP2"] = http2
        api_params["HTTPS"] = https_config
    
    # 配置IPv6
    if ipv6 is not None:
        api_params["IPv6"] = {"Switch": ipv6}
    
    # 配置服务类型
    if service_type:
        api_params["ServiceType"] = service_type
    
    # 配置服务区域
    if service_region:
        api_params["ServiceRegion"] = service_region
    
    # 配置回源协议
    if origin_protocol:
        api_params["OriginProtocol"] = origin_protocol
    
    # 将API参数设置到环境变量
    os.environ['API_PARAMS'] = json.dumps(api_params)
    os.environ['Action'] = 'BatchUpdateCdnConfig'
    
    try:
        # 创建CDN配置和API客户端
        config = CDNConfig()
        client = APIClient(config)
        
        # 发送请求
        response = client.send_request()
        print(f"成功更新CDN配置: {', '.join(domains)}")
        return response
    except (ValueError, APIError) as e:
        print(f"更新CDN配置失败: {str(e)}")
        return {"error": str(e)}


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='火山引擎CDN配置管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 批量更新配置命令
    batch_update_parser = subparsers.add_parser('batch-update', help='批量更新CDN配置')
    batch_update_parser.add_argument('--domains', required=True, nargs='+', help='CDN域名列表，例如: domain1.com domain2.com')
    batch_update_parser.add_argument('--http2', type=lambda x: x.lower() not in ('false', '0', 'no', 'n'), default=True, 
                                    help='是否开启HTTP2，可接受的值: true/false, yes/no, 1/0')
    batch_update_parser.add_argument('--https', type=lambda x: x.lower() not in ('false', '0', 'no', 'n'), 
                                    help='是否开启HTTPS，可接受的值: true/false, yes/no, 1/0')
    batch_update_parser.add_argument('--ipv6', type=lambda x: x.lower() not in ('false', '0', 'no', 'n'), 
                                    help='是否开启IPv6，可接受的值: true/false, yes/no, 1/0')
    batch_update_parser.add_argument('--service-type', choices=['web', 'download', 'video'],
                                    help='服务类型: web, download, video')
    batch_update_parser.add_argument('--service-region', choices=['chinese_mainland', 'global', 'overseas'],
                                    help='服务区域: chinese_mainland, global, overseas')
    batch_update_parser.add_argument('--origin-protocol', choices=['http', 'https', 'followclient'],
                                    help='回源协议: http, https, followclient')
    batch_update_parser.add_argument('--project', default='default', help='项目名称')
    
    # 更新单个域名配置命令
    update_parser = subparsers.add_parser('update', help='更新单个CDN域名配置')
    update_parser.add_argument('--domain', required=True, help='CDN域名')
    update_parser.add_argument('--http2', type=lambda x: x.lower() not in ('false', '0', 'no', 'n'), default=True, 
                              help='是否开启HTTP2，可接受的值: true/false, yes/no, 1/0')
    update_parser.add_argument('--https', type=lambda x: x.lower() not in ('false', '0', 'no', 'n'), 
                              help='是否开启HTTPS，可接受的值: true/false, yes/no, 1/0')
    update_parser.add_argument('--ipv6', type=lambda x: x.lower() not in ('false', '0', 'no', 'n'), 
                              help='是否开启IPv6，可接受的值: true/false, yes/no, 1/0')
    update_parser.add_argument('--service-type', choices=['web', 'download', 'video'],
                              help='服务类型: web, download, video')
    update_parser.add_argument('--service-region', choices=['chinese_mainland', 'global', 'overseas'],
                              help='服务区域: chinese_mainland, global, overseas')
    update_parser.add_argument('--origin-protocol', choices=['http', 'https', 'followclient'],
                              help='回源协议: http, https, followclient')
    update_parser.add_argument('--project', default='default', help='项目名称')
    
    # 获取域名列表命令
    list_parser = subparsers.add_parser('list', help='获取CDN域名列表')
    list_parser.add_argument('--page-size', type=int, default=10, help='每页数量')
    list_parser.add_argument('--page-number', type=int, default=1, help='页码')
    list_parser.add_argument('--project', default='default', help='项目名称')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    if args.command == 'batch-update':
        # 批量更新CDN配置
        result = batch_update_cdn_config(
            domains=args.domains,
            http2=args.http2,
            https=args.https,
            ipv6=args.ipv6,
            service_type=args.service_type,
            service_region=args.service_region,
            origin_protocol=args.origin_protocol,
            project=args.project
        )
    elif args.command == 'update':
        # 更新单个CDN域名配置
        result = update_cdn_domain(
            domain=args.domain,
            http2=args.http2,
            https=args.https,
            ipv6=args.ipv6,
            service_type=args.service_type,
            service_region=args.service_region,
            origin_protocol=args.origin_protocol,
            project=args.project
        )
    elif args.command == 'list':
        # 获取CDN域名列表
        result = list_cdn_domains(
            page_size=args.page_size,
            page_number=args.page_number,
            project=args.project
        )
    else:
        print("请指定要执行的命令：batch-update, update, list")
        return
    
    # 打印完整响应
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main() 