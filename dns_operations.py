#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 获取域名和cname

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
from sign import APIConfig, APIClient, APIError
from configs.api_config import api_config
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_credentials(ak: Optional[str] = None, sk: Optional[str] = None) -> Tuple[str, str]:
    """获取访问凭证
    
    Args:
        ak: 访问密钥ID，如果不提供则从api_config获取
        sk: 访问密钥，如果不提供则从api_config获取
        
    Returns:
        Tuple[str, str]: (ak, sk)元组
        
    Raises:
        DNSOperationError: 当无法获取访问凭证时
    """
    # 如果提供了ak和sk，直接使用
    if ak and sk:
        return ak, sk 
    # 从api_config获取
    config_ak = api_config.get('ak')
    config_sk = api_config.get('sk')
    if not config_ak or not config_sk:
        raise DNSOperationError("无法从api_config获取访问凭证，请确保api_config中包含有效的ak和sk")
        
    return config_ak, config_sk

@dataclass
class DNSRecord:
    """DNS记录数据类"""
    fqdn: str
    host: str
    record_type: str
    value: str
    enable: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DNSRecord':
        return cls(
            fqdn=data.get('FQDN', ''),
            host=data.get('Host', ''),
            record_type=data.get('Type', ''),
            value=data.get('Value', ''),
            enable=data.get('Enable', False)
        )

class DNSConfig(APIConfig):
    """DNS API配置类，继承自APIConfig"""
    
    def __init__(self, ak: Optional[str] = None, sk: Optional[str] = None):
        # 设置DNS服务的默认参数
        os.environ.setdefault('Service', 'DNS')
        os.environ.setdefault('Version', '2018-08-01')
        os.environ.setdefault('Region', 'cn-beijing')
        os.environ.setdefault('method', 'POST')
        
        # 获取访问凭证
        self.volcAK, self.volcSK = get_credentials(ak, sk)
        os.environ.setdefault('volcAK', self.volcAK)
        os.environ.setdefault('volcSK', self.volcSK)
        super().__init__()

class DNSOperationError(Exception):
    """DNS操作相关的自定义异常"""
    pass

def _make_api_request(action: str, params: Dict[str, Any], region: str = "cn-beijing",
                     ak: Optional[str] = None, sk: Optional[str] = None) -> Dict[str, Any]:
    """发送API请求的通用函数
    
    Args:
        action: API动作名称
        params: API参数
        region: 区域名称
        ak: 访问密钥ID，如果不提供则从api_config获取
        sk: 访问密钥，如果不提供则从api_config获取
        
    Returns:
        Dict: API响应结果
        
    Raises:
        DNSOperationError: 当API请求失败时
    """
    if region:
        os.environ['Region'] = region
    
    os.environ['Action'] = action
    os.environ['API_PARAMS'] = json.dumps(params)
    
    try:
        config = DNSConfig(ak, sk)
        client = APIClient(config)
        return client.send_request()
    except (ValueError, APIError) as e:
        raise DNSOperationError(f"API请求失败: {str(e)}")

def list_zones(ak: Optional[str] = None, sk: Optional[str] = None, region: str = "cn-beijing") -> Dict[str, Any]:
    """获取域名ID列表
    
    Args:
        ak: 访问密钥ID，如果不提供则从api_config获取
        sk: 访问密钥，如果不提供则从api_config获取
        region: 区域，默认为cn-beijing
        
    Returns:
        Dict: API响应结果
    """
    try:
        response = _make_api_request('ListZones', {}, region, ak, sk)
        logger.info("成功获取域名ID列表")
        return response
    except DNSOperationError as e:
        logger.error(f"获取域名ID列表失败: {str(e)}")
        return {"error": str(e)}

def list_records(zid: int, page_number: int = 1, page_size: int = 500, 
                ak: Optional[str] = None, sk: Optional[str] = None, 
                region: str = "cn-beijing") -> Dict[str, Any]:
    """获取域名记录列表
    
    Args:
        zid: 域名ID
        page_number: 页码，默认为1
        page_size: 每页记录数，默认为500
        ak: 访问密钥ID，如果不提供则从api_config获取
        sk: 访问密钥，如果不提供则从api_config获取
        region: 区域，默认为cn-beijing
        
    Returns:
        Dict: API响应结果
    """
    try:
        params = {
            "ZID": zid,
            "PageNumber": page_number,
            "PageSize": page_size,
        }
        response = _make_api_request('ListRecords', params, region, ak, sk)
        return response
    except DNSOperationError as e:
        logger.error(f"获取域名记录列表失败: {str(e)}")
        return {"error": str(e)}

def check_record_exists(host: str, record_type: str, value: str, zid: int,
                       ak: Optional[str] = None, sk: Optional[str] = None,
                       region: str = "cn-beijing") -> bool:
    """检查DNS记录是否已存在
    
    Args:
        host: 主机记录
        record_type: 记录类型
        value: 记录值
        zid: 域名ID
        ak: 访问密钥ID，如果不提供则从api_config获取
        sk: 访问密钥，如果不提供则从api_config获取
        region: 区域，默认为cn-beijing
        
    Returns:
        bool: 记录是否存在
    """
    try:
        response = list_records(zid=zid, ak=ak, sk=sk, region=region)
        if "error" in response:
            logger.error(f"检查记录是否存在时出错: {response['error']}")
            return False
            
        if "Result" not in response or "Records" not in response["Result"]:
            return False
            
        for record in response["Result"]["Records"]:
            if (record.get('Host') == host and 
                record.get('Type') == record_type and 
                record.get('Value') == value):
                return True
        return False
    except Exception as e:
        logger.error(f"检查记录是否存在时出现异常: {str(e)}")
        return False

def create_record(host: str, record_type: str, value: str, zid: int,
                 ak: Optional[str] = None, sk: Optional[str] = None,
                 region: str = "cn-beijing", skip_check: bool = False) -> Dict[str, Any]:
    """添加DNS解析记录
    
    Args:
        host: 主机记录，例如 example.com
        record_type: 记录类型，例如 CNAME, A, AAAA等
        value: 记录值
        zid: 域名ID
        ak: 访问密钥ID，如果不提供则从api_config获取
        sk: 访问密钥，如果不提供则从api_config获取
        region: 区域，默认为cn-beijing
        skip_check: 是否跳过重复检查，默认为False
        
    Returns:
        Dict: API响应结果
    """
    try:
        # 检查记录是否已存在
        if not skip_check and check_record_exists(host, record_type, value, zid, ak, sk, region):
            logger.warning(f"记录已存在: Host={host}, Type={record_type}, Value={value}")
            return {"error": "记录已存在"}
            
        params = {
            "ZID": zid,
            "Host": host,
            "Type": record_type,
            "Value": value
        }
        response = _make_api_request('CreateRecord', params, region, ak, sk)
        logger.info(f"成功添加DNS解析记录: {host}")
        return response
    except DNSOperationError as e:
        logger.error(f"添加DNS解析记录失败: {str(e)}")
        return {"error": str(e)}

def export_records_to_file(response: Dict[str, Any], output_file: Union[str, Path]) -> bool:
    """将DNS记录导出到文件
    
    Args:
        response: ListRecords函数的返回结果
        output_file: 输出文件路径，默认为dns_records.txt
        
    Returns:
        bool: 是否成功导出
    """
    try:
        if "error" in response:
            logger.error(f"错误: {response['error']}")
            return False
            
        if "Result" not in response or "Records" not in response["Result"]:
            logger.error("错误: 响应中没有找到DNS记录")
            return False
            
        records = [DNSRecord.from_dict(item) for item in response["Result"]["Records"]]
        if not records:
            logger.warning("没有找到有效的DNS记录")
            return False
            
        # 使用Path对象处理文件路径
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 格式化记录为表格
        headers = ['FQDN', 'Host', 'Type', 'Value', 'Enable']
        max_widths = {header: max(len(str(getattr(record, header.lower().replace('type', 'record_type')))) 
                                for record in records) for header in headers}
        
        # 创建表格内容
        table_rows = []
        header_line = ' | '.join(f"{header:{max_widths[header]}}" for header in headers)
        separator_line = '-+-'.join('-' * max_widths[header] for header in headers)
        table_rows.extend([header_line, separator_line])
        
        for record in records:
            row = ' | '.join(
                f"{str(getattr(record, header.lower().replace('type', 'record_type'))):{max_widths[header]}}"
                for header in headers
            )
            table_rows.append(row)
        
        # 写入文件
        output_path.write_text('\n'.join(table_rows), encoding='utf-8')
        logger.info(f"DNS记录已成功写入文件: {output_path}")
        return True
    except Exception as e:
        logger.error(f"导出DNS记录时出现异常: {str(e)}")
        return False

def create_records_from_file(file_path: Union[str, Path], zid: int,
                          ak: Optional[str] = None, sk: Optional[str] = None,
                          region: str = "cn-beijing", skip_check: bool = False) -> List[Dict[str, Any]]:
    """从导出的文件中读取DNS记录并创建这些记录
    
    Args:
        file_path: 导出的DNS记录文件路径
        zid: 域名ID
        ak: 访问密钥ID，如果不提供则从api_config获取
        sk: 访问密钥，如果不提供则从api_config获取
        region: 区域，默认为cn-beijing
        skip_check: 是否跳过重复检查，默认为False
        
    Returns:
        List[Dict[str, Any]]: 创建记录的结果列表
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        content = file_path.read_text(encoding='utf-8')
        if not content or content.strip() == "没有找到有效的DNS记录":
            logger.error(f"文件 {file_path} 中没有找到有效的DNS记录")
            return []
        
        lines = content.strip().split('\n')
        if len(lines) < 3:
            logger.error(f"文件 {file_path} 格式不正确，无法解析")
            return []
        
        headers = [h.strip() for h in lines[0].split('|')]
        results = []
        skipped_records = []
        
        for i, line in enumerate(lines[2:], start=2):
            if not line.strip():
                continue
                
            values = [v.strip() for v in line.split('|')]
            if len(values) < len(headers):
                logger.warning(f"第 {i+1} 行格式不正确，跳过")
                continue
                
            record = dict(zip(headers, values))
            if not all(k in record and record[k] for k in ['Host', 'Type', 'Value']):
                logger.warning(f"第 {i+1} 行缺少必要字段 (Host, Type, Value)，跳过")
                continue
                
            # 检查记录是否已存在
            if not skip_check and check_record_exists(record['Host'], record['Type'], record['Value'], zid, ak, sk, region):
                skipped_records.append(f"Host={record['Host']}, Type={record['Type']}, Value={record['Value']}")
                continue
                
            logger.info(f"正在创建记录: Host={record['Host']}, Type={record['Type']}, Value={record['Value']}")
            response = create_record(
                host=record['Host'],
                record_type=record['Type'],
                value=record['Value'],
                zid=zid,
                ak=ak,
                sk=sk,
                region=region,
                skip_check=skip_check
            )
            
            results.append(response)
        
        # 输出处理结果统计
        if skipped_records:
            logger.warning(f"以下 {len(skipped_records)} 条记录已存在，已跳过：")
            for record in skipped_records:
                logger.warning(f"  - {record}")
                
        if not results and not skipped_records:
            logger.warning("没有找到任何有效的DNS记录")
        else:
            logger.info(f"成功从文件 {file_path} 创建了 {len(results)} 条DNS记录")
            if skipped_records:
                logger.info(f"跳过了 {len(skipped_records)} 条已存在的记录")
            
        return results
    except Exception as e:
        logger.error(f"从文件创建DNS记录时出现异常: {str(e)}")
        return []

if __name__ == "__main__":
    # 示例1：获取域名ID列表
    print("\n获取域名ID列表示例:")
    response = list_zones()
    # print(response)
    if "Result" in response and "Zones" in response["Result"]:
        for zone in response["Result"]["Zones"]:
            print(f"ZID: {zone.get('ZID', 'N/A')}, ZoneName: {zone.get('ZoneName', 'N/A')}")
    # 设置命令行参数解析器
    print('\n')
    print('示例命令：')
    print('python dns_operations.py --zid ZID --action export --output dns_records.txt # 导出到文件')
    print('python dns_operations.py --zid ZID --action create --host test.com --type CNAME --value CNAME.test.com # 创建单条CNAME记录')
    print('python dns_operations.py --zid ZID --action import --input dns_records.txt # 从文件导入')
    print('\n')
    parser = argparse.ArgumentParser(description='DNS操作工具')
    parser.add_argument('--action', required=True, 
                        choices=['list', 'create', 'export', 'import'], 
                        help='操作类型: list (列出记录), create (创建记录), export (导出记录到文件) 或 import (从文件导入记录)')
    parser.add_argument('--zid', type=int, required=True, help='域名ID')
    parser.add_argument('--host', help='主机记录，例如: example.com (仅创建记录时需要)')
    parser.add_argument('--type', help='记录类型，例如: CNAME, A, AAAA等 (仅创建记录时需要)')
    parser.add_argument('--value', help='记录值 (仅创建记录时需要)')
    parser.add_argument('--output', default='dns_records.txt', help='输出文件路径 (仅导出记录时需要)')
    parser.add_argument('--input', help='输入文件路径 (仅从文件导入记录时需要)')
    parser.add_argument('--skip-check', action='store_true', help='跳过重复检查')
    
    args = parser.parse_args()

    # 根据action参数执行不同的操作
    if args.action == 'list':
        # 列出指定域名ID的所有记录
        response = list_records(zid=args.zid)
        print("\n域名记录列表:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    
    elif args.action == 'create':
        # 验证创建记录所需的参数
        if not all([args.host, args.type, args.value]):
            print("错误: 创建记录需要提供 --host, --type 和 --value 参数")
            print('--host test.com --type CNAME --value CNAME.test.com --zid 12345')
            parser.print_help()
            exit(1)
            
        # 创建新记录
        print("\n创建DNS解析记录:")
        create_record(
            host=args.host,
            record_type=args.type,
            value=args.value,
            zid=args.zid,
            skip_check=args.skip_check
        )
    
    elif args.action == 'export':
        # 导出记录到文件
        print("\n导出DNS记录到文件:")
        response = list_records(zid=args.zid)
        export_records_to_file(response, args.output)
    
    elif args.action == 'import':
        # 验证导入记录所需的参数
        if not args.input:
            print("错误: 从文件导入记录需要提供 --input 参数")
            parser.print_help()
            exit(1)
            
        # 从文件导入记录
        print("\n从文件导入DNS记录:")
        create_records_from_file(
            file_path=args.input,
            zid=args.zid,
            skip_check=args.skip_check
        )
    
    elif args.action == 'export':
        # 获取记录并导出到文件
        print("\n导出DNS记录到文件:")
        response = list_records(zid=args.zid)
        export_records_to_file(response, args.output)
