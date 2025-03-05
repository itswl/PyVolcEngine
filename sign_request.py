from __future__ import absolute_import
from sign import APIConfig, APIClient, APIError

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
