from __future__ import absolute_import
from sign import APIConfig, APIClient, APIError

def volc_requests():
    try:
        config = APIConfig()
        client = APIClient(config)
        response = client.send_request()
        return response
    except (ValueError, APIError) as e:
        print(f'错误：{str(e)}')
        exit(1)

def get_AvailableBalance():
    response = volc_requests()
    return response['Result']['AvailableBalance']

def is_balance_greater_than(threshold):
    """检查可用余额是否大于指定阈值
    
    Args:
        threshold: 阈值数值
        
    Returns:
        bool: 如果可用余额大于阈值返回True，否则返回False
    """
    balance = get_AvailableBalance()
    return balance, float(balance) > threshold


if __name__ == '__main__':
    threshold = 7000
    balance,  result = is_balance_greater_than(threshold)
    print('当前余额: ', balance)
    if not result:
        print('余额不足', threshold)
        exit(1)
    