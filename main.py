import requests
import json
import time

# ==================== 配置区域 ====================

# 1. 你的 Bark 推送链接
NOTIFY_URL = "https://api.day.app/LXJuzuCcmf3aR3QP56Ez4o/" 

# 2. 报警价差
ALERT_DIFF = 50

# ================================================

# 伪装成浏览器（这是关键！骗过反爬虫）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://omni.variational.io",
    "Referer": "https://omni.variational.io/"
}

def send_alert(text):
    try:
        url = f"{NOTIFY_URL}价差监控/{text}"
        requests.get(url, timeout=5)
        print(f"已推送通知: {text}")
    except Exception as e:
        print(f"推送失败: {e}")

def get_nado_price():
    url = "https://archive.prod.nado.xyz/v2/tickers"
    try:
        # 加上 Headers 伪装
        resp = requests.get(url, headers=HEADERS, timeout=10).json()
        
        # 兼容处理：万一它返回的是 {"BTC": {...}} 这种字典结构
        data_list = []
        if isinstance(resp, list):
            data_list = resp
        elif isinstance(resp, dict):
            if 'tickers' in resp:
                data_list = resp['tickers']
            else:
                # 尝试取字典的所有值
                data_list = resp.values()
        
        for item in data_list:
            # 确保 item 是个字典，防止报错
            if not isinstance(item, dict):
                continue
                
            ticker_id = item.get('tickerId', '').upper()
            # 有些接口可能直接用 symbol 字段
            symbol = item.get('symbol', '').upper()
            
            if ('BTC' in ticker_id and 'USDT' in ticker_id) or ('BTC' in symbol and 'USDT' in symbol):
                price = item.get('markPrice') or item.get('lastPrice') or item.get('price')
                if price:
                    return float(price)
        
        print("Nado: 未找到 BTC 数据，返回结构可能变了")
        # 打印一点数据方便调试
        print(f"Nado 数据预览: {str(resp)[:100]}")
        return None
    except Exception as e:
        print(f"Nado 获取失败: {e}")
        return None

def get_variational_price():
    url = "https://omni.variational.io/api/quotes/indicative"
    payload = {
        "instrument": {
            "underlying": "BTC",
            "funding_interval_s": 3600,
            "settlement_asset": "USDC",
            "instrument_type": "perpetual_future"
        },
        "qty": "0.0001" 
    }
    
    try:
        # 加上 Headers 伪装
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        
        # 如果被拦截，打印状态码
        if resp.status_code != 200:
            print(f"Variational 拒绝访问，状态码: {resp.status_code}")
            return None
            
        data = resp.json()
        if 'mark_price' in data:
            return float(data['mark_price'])
        else:
            print(f"Variational 数据异常: {str(data)[:100]}")
            return None
    except Exception as e:
        print(f"Variational 获取失败: {e}")
        return None

def main():
    print("=== 开始运行监控 (加强版) ===")
    p_nado = get_nado_price()
    p_var = get_variational_price()
    
    print(f"Nado 价格: {p_nado}")
    print(f"Variational 价格: {p_var}")

    if p_nado and p_var:
        diff = p_nado - p_var
        abs_diff = abs(diff)
        
        print(f"当前价差: {abs_diff:.2f}")
        
        if abs_diff > ALERT_DIFF:
            msg = f"发现机会!差价{abs_diff:.1f} (N:{p_nado:.0f}, V:{p_var:.0f})"
            send_alert(msg)
        else:
            print("价差未达到报警线")
    else:
        print("获取价格失败，请检查上方日志")

if __name__ == "__main__":
    main()
