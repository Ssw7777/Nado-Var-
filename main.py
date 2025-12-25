import requests
from curl_cffi import requests as crequests # 引入新武器
import time

# ==================== 配置区域 ====================

# 1. 你的 Bark 推送链接
NOTIFY_URL = "https://api.day.app/LXJuzuCcmf3aR3QP56Ez4o/" 

# 2. 报警价差 (建议先设为 0 测试)
ALERT_DIFF = 0

# ================================================

def send_alert(text):
    try:
        url = f"{NOTIFY_URL}价差监控/{text}"
        requests.get(url, timeout=5)
        print(f"✅ 已推送通知: {text}")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

def get_nado_price():
    # Nado 已经成功了，保持逻辑不变
    url = "https://archive.prod.nado.xyz/v2/tickers"
    try:
        resp = requests.get(url, timeout=10).json()
        data_list = []
        if isinstance(resp, dict):
            data_list = list(resp.values())
        elif isinstance(resp, list):
            data_list = resp
            
        for item in data_list:
            if not isinstance(item, dict): continue
            tid = str(item.get('tickerId') or item.get('ticker_id') or item.get('symbol') or '').upper()
            if 'BTC' in tid:
                # 之前日志显示字段名是 last_price
                price = item.get('last_price') or item.get('lastPrice') or item.get('markPrice')
                if price:
                    print(f"✅ Nado 获取成功: {price}")
                    return float(price)
        return None
    except Exception as e:
        print(f"❌ Nado 出错: {e}")
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
        # 使用 curl_cffi 模拟 Chrome 浏览器指纹
        # impersonate="chrome110" 是关键
        resp = crequests.post(url, json=payload, impersonate="chrome110", timeout=15)
        
        if resp.status_code != 200:
            print(f"⚠️ Variational 状态码: {resp.status_code}")
            return None
            
        data = resp.json()
        if 'mark_price' in data:
            price = float(data['mark_price'])
            print(f"✅ Variational 获取成功: {price}")
            return price
        else:
            print(f"⚠️ Variational 数据异常: {str(data)[:100]}")
            return None
    except Exception as e:
        print(f"❌ Variational 出错: {e}")
        return None

def main():
    print("=== 🚀 启动指纹伪装方案 (curl_cffi) ===")
    p_nado = get_nado_price()
    p_var = get_variational_price()
    
    if p_nado and p_var:
        diff = p_nado - p_var
        abs_diff = abs(diff)
        print(f"📉 价差: {abs_diff:.2f}")
        
        if abs_diff > ALERT_DIFF:
            msg = f"价差{abs_diff:.1f} (N:{p_nado:.0f}, V:{p_var:.0f})"
            send_alert(msg)
    else:
        print("❌ 依然有失败项，请检查上方日志")

if __name__ == "__main__":
    main()
