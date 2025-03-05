import datetime
import hashlib
import hmac
from urllib.parse import quote
import requests
import os
import json
from typing import Optional, Dict, Any, Union


'''
export method='POST'
export API_PARAMS='{"InstanceId": "postgres-b7b939b9efe4","BackupType": "Increment"}'
export Service='rds_postgresql'
export Action='CreateBackup'
export Version='2022-01-01'
export Region='cn-shanghai'
export ContentType='application/json'
export Host='open.volcengineapi.com'
export volcAK=''
export volcSK=''

Service: rds_postgresql mongodb vke Redis Kafka ESloud iam 
'''

class APIConfig:
    def __init__(self):
        self.ak = self._get_required_env('volcAK', '访问密钥ID不能为空')
        self.sk = self._get_required_env('volcSK', '访问密钥不能为空')
        self.action = os.environ.get('Action', 'DescribeVpcs')
        self.method = os.environ.get('method', 'GET')
        self.service = os.environ.get('Service', 'vpc')
        self.version = os.environ.get('Version', '2020-04-01')
        self.region = os.environ.get('Region', 'cn-shanghai')
        self.host = os.environ.get('Host', 'open.volcengineapi.com')
        self.content_type = os.environ.get('ContentType', 'application/json')
        self.api_params = self._parse_api_params()

    @staticmethod
    def _get_required_env(key: str, error_message: str) -> str:
        value = os.environ.get(key)
        if not value:
            raise ValueError(error_message)
        return value

    @staticmethod
    def _parse_api_params() -> Optional[Dict[str, Any]]:
        env_params = os.environ.get('API_PARAMS')
        if env_params:
            try:
                return json.loads(env_params)
            except json.JSONDecodeError as e:
                raise ValueError(f'API参数解析失败: {e}')
        return None

class SignatureBuilder:
    @staticmethod
    def norm_query(params: Dict[str, Any]) -> str:
        query_items = []
        for key in sorted(params.keys()):
            if isinstance(params[key], list):
                for item in params[key]:
                    query_items.append(f"{quote(key, safe='-_.~')}={quote(str(item), safe='-_.~')}")
            else:
                query_items.append(f"{quote(key, safe='-_.~')}={quote(str(params[key]), safe='-_.~')}")
        return '&'.join(query_items).replace('+', '%20')

    @staticmethod
    def hash_sha256(content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def hmac_sha256(key: bytes, content: str) -> bytes:
        return hmac.new(key, content.encode('utf-8'), hashlib.sha256).digest()

class APIClient:
    def __init__(self, config: APIConfig):
        self.config = config
        self.signature_builder = SignatureBuilder()

    def send_request(self) -> Dict[str, Any]:
        now = datetime.datetime.now(datetime.UTC)
        body = json.dumps(self.config.api_params) if self.config.api_params is not None else ''

        request_params = self._build_request_params(body, now)
        headers = self._build_headers(request_params)
        response = self._make_request(request_params, headers)
        return self._handle_response(response)

    def _build_request_params(self, body: str, date: datetime.datetime) -> Dict[str, Any]:
        return {
            'body': body,
            'host': self.config.host,
            'path': '/',
            'method': self.config.method,
            'content_type': self.config.content_type,
            'date': date,
            'query': {'Action': self.config.action, 'Version': self.config.version}
        }

    def _build_headers(self, request_params: Dict[str, Any]) -> Dict[str, str]:
        x_date = request_params['date'].strftime('%Y%m%dT%H%M%SZ')
        short_date = x_date[:8]
        content_sha256 = self.signature_builder.hash_sha256(request_params['body'])

        headers = {
            'Host': request_params['host'],
            'X-Content-Sha256': content_sha256,
            'X-Date': x_date,
            'Content-Type': request_params['content_type']
        }

        signature = self._calculate_signature(request_params, x_date, short_date, content_sha256)
        headers['Authorization'] = self._build_authorization_header(short_date, signature)

        return headers

    def _calculate_signature(self, request_params: Dict[str, Any], x_date: str, short_date: str, content_sha256: str) -> str:
        signed_headers = ['content-type', 'host', 'x-content-sha256', 'x-date']
        signed_headers_str = ';'.join(signed_headers)

        canonical_request = self._build_canonical_request(request_params, content_sha256, x_date, signed_headers_str)
        hashed_canonical_request = self.signature_builder.hash_sha256(canonical_request)

        credential_scope = f"{short_date}/{self.config.region}/{self.config.service}/request"
        string_to_sign = f"HMAC-SHA256\n{x_date}\n{credential_scope}\n{hashed_canonical_request}"

        k_date = self.signature_builder.hmac_sha256(self.config.sk.encode('utf-8'), short_date)
        k_region = self.signature_builder.hmac_sha256(k_date, self.config.region)
        k_service = self.signature_builder.hmac_sha256(k_region, self.config.service)
        k_signing = self.signature_builder.hmac_sha256(k_service, 'request')

        return self.signature_builder.hmac_sha256(k_signing, string_to_sign).hex()

    def _build_canonical_request(self, request_params: Dict[str, Any], content_sha256: str, x_date: str, signed_headers_str: str) -> str:
        canonical_headers = [
            f"content-type:{request_params['content_type']}",
            f"host:{request_params['host']}",
            f"x-content-sha256:{content_sha256}",
            f"x-date:{x_date}"
        ]

        return '\n'.join([
            request_params['method'].upper(),
            request_params['path'],
            self.signature_builder.norm_query(request_params['query']),
            '\n'.join(canonical_headers),
            '',
            signed_headers_str,
            content_sha256
        ])

    def _build_authorization_header(self, short_date: str, signature: str) -> str:
        credential_scope = f"{short_date}/{self.config.region}/{self.config.service}/request"
        return f"HMAC-SHA256 Credential={self.config.ak}/{credential_scope}, SignedHeaders=content-type;host;x-content-sha256;x-date, Signature={signature}"

    def _make_request(self, request_params: Dict[str, Any], headers: Dict[str, str]) -> requests.Response:
        url = f"https://{request_params['host']}{request_params['path']}?{self.signature_builder.norm_query(request_params['query'])}"
        return requests.request(
            method=request_params['method'],
            url=url,
            headers=headers,
            data=request_params['body']
        )

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        if response.status_code != 200:
            raise APIError(f'HTTP请求失败，状态码：{response.status_code}\n响应内容：{response.text}')

        if not response.text.strip():
            print('任务执行成功，响应为空')
            return {}

        try:
            result = response.json()
        except json.JSONDecodeError as e:
            raise APIError(f'响应内容不是有效的JSON格式：{response.text}')

        if result.get('ResponseMetadata', {}).get('Error'):
            raise APIError(f'任务执行失败：{result["ResponseMetadata"]["Error"]}')

        print('任务执行成功')
        return result

class APIError(Exception):
    pass

def main():
    try:
        config = APIConfig()
        client = APIClient(config)
        response = client.send_request()
        print(response)
    except (ValueError, APIError) as e:
        print(f'错误：{str(e)}')
        exit(1)

if __name__ == '__main__':
    main()
