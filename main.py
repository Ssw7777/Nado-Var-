import requests
import time

# ==================== 配置区域 ====================

# 1. 你的 Bark 推送链接 (已填好)
NOTIFY_URL = "https://api.day.app/LXJuzuCcmf3aR3QP56Ez4o/" 

# 2. 报警价差 (当两边价格差距超过多少U时提醒)
ALERT_DIFF = 50 

# ================================================

def send_alert(text):
    try:
        # Bark 推送
        # 发送请求，标题是"价差提醒"，内容是 text
        url = f"{NOTIFY_URL}价差提醒/{text}"
        requests.get(url, timeout=5)
        print("已发送通知")
    except Exception as e:
        print(f"推送失败: {e}")

def get_nado_price():
    url = "https://archive.prod.nado.xyz/v2/tickers"
    try:
        resp = requests.get(url, timeout=10).json()
        if isinstance(resp, dict) and 'tickers' in resp:
            resp = resp['tickers']
            
        for item in resp:
            ticker_id = item.get('tickerId', '').upper()
            if 'BTC' in ticker_id and 'USDT' in ticker_id:
                price = item.get('markPrice') or item.get('lastPrice')
                if price:
                    return float(price)
        return None
    except Exception as e:
        print(f"Nado 获取失败: {e}")
        return None

def get_variational_price():
    url = "https://omni.variational.io/api/quotes/indicative"
    
    # 根据你提供的截图填写的参数
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
        resp = requests.post(url, json=payload, timeout=10).json()
        if 'mark_price' in resp:
            return float(resp['mark_price'])
        else:
            print("Variational 结构异常:", resp)
            return None
    except Exception as e:
        print(f"Variational 获取失败: {e}")
        return None

def main():
    print("=== 开始监控 ===")
    p_nado = get_nado_price()
    p_var = get_variational_price()
    
    print(f"Nado价格: {p_nado}")
    print(f"Variational价格: {p_var}")

    if p_nado and p_var:
        diff = p_nado - p_var
        abs_diff = abs(diff)
        
        print(f"当前价差: {abs_diff:.2f}")
        
        if abs_diff > ALERT_DIFF:
            msg = f"价差{abs_diff:.1f}U (N:{p_nado:.0f}, V:{p_var:.0f})"
            send_alert(msg)
    else:
        print("获取价格失败")

if __name__ == "__main__":
    main()
