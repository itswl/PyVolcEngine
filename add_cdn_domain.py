#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional

from sign import APIConfig, APIClient, APIError


class CDNConfig(APIConfig):
    """CDN API配置类，继承自APIConfig"""
    
    def __init__(self):
        # 设置CDN服务的默认参数
        os.environ.setdefault('Service', 'CDN')
        os.environ.setdefault('Version', '2021-03-01')
        os.environ.setdefault('Region', 'cn-shanghai')
        os.environ.setdefault('Action', 'AddCdnDomain')
        os.environ.setdefault('method', 'POST')
        super().__init__()


def add_cdn_domain(
    domain: str,
    primary_origin: List[str],
    service_type: str = 'web',
    service_region: str = 'chinese_mainland',
    origin_protocol: str = 'followclient',
    https: bool = True,
    ipv6: bool = True,
    project: str = 'default',
    cert_id: Optional[str] = None,
    cert_name: Optional[str] = None
) -> Dict[str, Any]:
    """添加CDN域名
    
    Args:
        domain: CDN域名，例如 example.com
        primary_origin: 源站列表，例如 ["example-origin.com"]
        service_type: 服务类型，可选值: web, download, video
        service_region: 服务区域，可选值: chinese_mainland, global, overseas
        origin_protocol: 回源协议，可选值: http, https, followclient
        https: 是否开启HTTPS
        ipv6: 是否开启IPv6
        project: 项目名称
        cert_id: 证书ID，启用HTTPS时必填
        cert_name: 证书名称，启用HTTPS时必填
        
    Returns:
        Dict: API响应结果
    """
    # 设置API参数
    api_params = {
        "Domain": domain,
        "PrimaryOrigin": primary_origin,
        "ServiceType": service_type,
        "ServiceRegion": service_region,
        "OriginProtocol": origin_protocol,
        "IPv6": {"Switch": ipv6},  # 将布尔值改为包含Switch字段的字典结构
        "Project": project
    }
    
    # 如果启用HTTPS，添加HTTPS配置
    if https:
        https_config = {"Switch": https}
        # 如果提供了证书信息，添加到HTTPS配置中
        if cert_id and cert_name:
            https_config["CertInfo"] = {
                "CertId": cert_id,
                "CertName": cert_name
            }
        api_params["HTTPS"] = https_config
    else:
        api_params["HTTPS"] = {"Switch": False}
    
    # 将API参数设置到环境变量
    os.environ['API_PARAMS'] = json.dumps(api_params)
    os.environ['Action'] = 'AddCdnDomain'
    
    try:
        # 创建CDN配置和API客户端
        config = CDNConfig()
        client = APIClient(config)
        
        # 发送请求
        response = client.send_request()
        print(f"成功添加CDN域名: {domain}")
        return response
    except (ValueError, APIError) as e:
        print(f"添加CDN域名失败: {str(e)}")
        return {"error": str(e)}


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='添加火山引擎CDN域名')
    parser.add_argument('--domain', required=True, help='CDN域名，例如: example.com')
    parser.add_argument('--primary-origin', required=True, nargs='+', help='源站列表，例如: origin1.com origin2.com')
    parser.add_argument('--service-type', default='web', choices=['web', 'download', 'video'], help='服务类型')
    parser.add_argument('--service-region', default='chinese_mainland', 
                        choices=['chinese_mainland', 'global', 'overseas'], help='服务区域')
    parser.add_argument('--origin-protocol', default='followclient', 
                        choices=['http', 'https', 'followclient'], help='回源协议')
    parser.add_argument('--https', type=lambda x: x.lower() not in ('false', '0', 'no', 'n'), default=True, 
                        help='是否开启HTTPS，可接受的值: true/false, yes/no, 1/0')
    parser.add_argument('--ipv6', type=lambda x: x.lower() not in ('false', '0', 'no', 'n'), default=True, 
                        help='是否开启IPv6，可接受的值: true/false, yes/no, 1/0')
    parser.add_argument('--cert-id', help='证书ID，启用HTTPS时必填')
    parser.add_argument('--cert-name', help='证书名称，启用HTTPS时必填')
    parser.add_argument('--project', default='default', help='项目名称')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 检查HTTPS参数
    if args.https and (not args.cert_id or not args.cert_name):
        print("错误: 启用HTTPS时必须提供证书ID(--cert-id)和证书名称(--cert-name)")
        sys.exit(1)
    
    # 调用添加CDN域名函数
    result = add_cdn_domain(
        domain=args.domain,
        primary_origin=args.primary_origin,
        service_type=args.service_type,
        service_region=args.service_region,
        origin_protocol=args.origin_protocol,
        https=args.https,
        ipv6=args.ipv6,
        project=args.project,
        cert_id=args.cert_id,
        cert_name=args.cert_name
    )
    
    # 打印完整响应
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()