import requests
import json
import time

# ==================== 配置区域 ====================

# 1. 你的 Bark 推送链接
NOTIFY_URL = "https://api.day.app/LXJuzuCcmf3aR3QP56Ez4o/" 

# 2. 报警价差 (建议先设为 0 测试)
ALERT_DIFF = 0

# ================================================

# 全套 Chrome 伪装 (专门对付 403)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://omni.variational.io",
    "Referer": "https://omni.variational.io/",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
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
        # Nado 对 headers 要求不高，简单的即可
        resp = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=10).json()
        
        # === 修复点：处理字典结构 ===
        data_list = []
        if isinstance(resp, dict):
            # 如果返回的是 {'BTC...': {...}, 'ETH...': {...}} 这种结构
            # 我们直接取所有的值 (values) 组成列表
            data_list = list(resp.values())
        elif isinstance(resp, list):
            data_list = resp
            
        for item in data_list:
            if not isinstance(item, dict): continue
            
            # Nado 的 ID 有时候叫 ticker_id 有时候叫 tickerId
            ticker_id = item.get('tickerId') or item.get('ticker_id') or ''
            ticker_id = str(ticker_id).upper()
            
            # 只要包含 BTC 和 USDT 就认为是目标
            if 'BTC' in ticker_id and 'USDT' in ticker_id:
                price = item.get('markPrice') or item.get('lastPrice') or item.get('oraclePrice')
                if price:
                    return float(price)
                    
        print(f"⚠️ Nado 数据里没找到 BTC，数据样例: {str(resp)[:100]}")
        return None
    except Exception as e:
        print(f"❌ Nado 获取出错: {e}")
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
        # 使用全套伪装 Headers
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        
        if resp.status_code == 403:
            print("❌ Variational 依然 403 (伪装失效)。可能需要更高级的 Cloudscraper 库。")
            return None
        elif resp.status_code != 200:
            print(f"⚠️ Variational 错误代码: {resp.status_code}")
            return None
            
        data = resp.json()
        if 'mark_price' in data:
            return float(data['mark_price'])
        else:
            print(f"⚠️ Variational 数据结构: {str(data)[:100]}")
            return None
    except Exception as e:
        print(f"❌ Variational 获取出错: {e}")
        return None

def main():
    print("=== 🚀 开始监控 (修复版 V3) ===")
    p_nado = get_nado_price()
    p_var = get_variational_price()
    
    print(f"Nado 价格: {p_nado}")
    print(f"Variational 价格: {p_var}")

    if p_nado and p_var:
        diff = p_nado - p_var
        abs_diff = abs(diff)
        print(f"📉 当前价差: {abs_diff:.2f}")
        
        if abs_diff > ALERT_DIFF:
            msg = f"价差{abs_diff:.1f} (N:{p_nado:.0f}, V:{p_var:.0f})"
            send_alert(msg)
        else:
            print("💤 价差未达标")
    else:
        print("❌ 获取失败")

if __name__ == "__main__":
    main()
