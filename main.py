import requests
from curl_cffi import requests as crequests 
import time

# ==================== 配置区域 ====================

# 1. 你的 Bark 推送链接
NOTIFY_URL = "https://api.day.app/LXJuzuCcmf3aR3QP56Ez4o/" 

# 2. 报警价差 (建议先设为 0 测试)
ALERT_DIFF = 0

# ================================================

# 关键：必须带上这些身份证明，否则必报 403
HEADERS = {
    "Origin": "https://omni.variational.io",
    "Referer": "https://omni.variational.io/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json"
}

def send_alert(text):
    try:
        url = f"{NOTIFY_URL}价差监控/{text}"
        requests.get(url, timeout=5)
        print(f"✅ 已推送通知: {text}")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

def get_nado_price():
    url = "https://archive.prod.nado.xyz/v2/tickers"
    try:
        # Nado 已经稳了，用最简单的 requests 即可
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
                # 之前日志验证过 last_price 是对的
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
        # ⚠️ 这里的改动是关键：
        # 1. 用了 chrome120 指纹
        # 2. 加上了 headers (Origin/Referer)
        resp = crequests.post(
            url, 
            json=payload, 
            headers=HEADERS, 
            impersonate="chrome120", 
            timeout=15
        )
        
        if resp.status_code != 200:
            print(f"⚠️ Variational 状态码: {resp.status_code}")
            # 打印一下返回内容，死也要死个明白
            print(f"错误内容: {resp.text[:200]}")
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
    print("=== 🚀 终极修正版 (指纹+Header) ===")
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
        print("❌ 依然有失败项，请检查日志")

if __name__ == "__main__":
    main()
