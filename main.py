import requests
import cloudscraper # 引入核武器
import json
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
    url = "https://archive.prod.nado.xyz/v2/tickers"
    try:
        # Nado 能抓到数据，用 requests 就够了
        resp = requests.get(url, timeout=10).json()
        
        # 提取 value 数据
        data_list = []
        if isinstance(resp, dict):
            data_list = list(resp.values())
        elif isinstance(resp, list):
            data_list = resp
            
        for item in data_list:
            if not isinstance(item, dict): continue
            
            # 兼容各种 ID 写法
            tid = str(item.get('tickerId') or item.get('ticker_id') or item.get('symbol') or '').upper()
            
            # 只要包含 BTC
            if 'BTC' in tid:
                # 穷举所有可能的价格字段名
                candidates = [
                    'markPrice', 'mark_price', 
                    'lastPrice', 'last_price', 
                    'oraclePrice', 'oracle_price',
                    'indexPrice', 'index_price',
                    'price'
                ]
                
                for key in candidates:
                    if key in item and item[key]:
                        print(f"✅ Nado 成功 (字段名 {key}): {item[key]}")
                        return float(item[key])
                        
                # 如果代码跑到这里，说明找到了 BTC 但没找到价格，打印出来看看
                print(f"⚠️ Nado 找到了BTC但没找到价格字段，keys: {list(item.keys())}")
                
        print(f"⚠️ Nado 遍历结束未找到目标")
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
        # 启用 cloudscraper 绕过 403
        scraper = cloudscraper.create_scraper()
        resp = scraper.post(url, json=payload, timeout=15)
        
        if resp.status_code != 200:
            print(f"⚠️ Variational 状态码: {resp.status_code}")
            print(f"网页内容预览: {resp.text[:100]}")
            return None
            
        data = resp.json()
        if 'mark_price' in data:
            return float(data['mark_price'])
        else:
            print(f"⚠️ Variational 数据异常: {str(data)[:100]}")
            return None
    except Exception as e:
        print(f"❌ Variational 出错: {e}")
        return None

def main():
    print("=== 🚀 启动终极方案 (Cloudscraper) ===")
    p_nado = get_nado_price()
    p_var = get_variational_price()
    
    print(f"Nado: {p_nado}")
    print(f"Variational: {p_var}")

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
