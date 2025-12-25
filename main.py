import requests
import time
from playwright.sync_api import sync_playwright

# ==================== 配置区域 ====================
BARK_URL = "https://api.day.app/LXJuzuCcmf3aR3QP56Ez4o/" 
ALERT_DIFF = 0 # 建议先设0测试
# ================================================

def send_bark(text):
    try:
        url = f"{BARK_URL}价差监控/{text}"
        requests.get(url, timeout=5)
        print(f"✅ Bark 推送: {text}")
    except:
        pass

def get_nado_price():
    # Nado 保持原样，它是好的
    try:
        url = "https://archive.prod.nado.xyz/v2/tickers"
        resp = requests.get(url, timeout=10).json()
        data = list(resp.values()) if isinstance(resp, dict) else resp
        for item in data:
            if not isinstance(item, dict): continue
            tid = str(item.get('tickerId') or item.get('ticker_id') or item.get('symbol') or '').upper()
            if 'BTC' in tid:
                p = item.get('last_price') or item.get('markPrice')
                if p: 
                    print(f"✅ Nado: {p}")
                    return float(p)
    except Exception as e:
        print(f"❌ Nado错: {e}")
    return None

def get_variational_price():
    print("⏳ 正在启动浏览器抓取 Variational...")
    price = None
    
    try:
        with sync_playwright() as p:
            # 启动一个无头 Chrome 浏览器
            browser = p.chromium.launch(headless=True)
            # 伪装一下 UserAgent
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 监听网络请求 (这是最骚的操作)
            # 我们不看网页长啥样，直接截获它发给后台的秘密数据包
            def handle_response(response):
                nonlocal price
                # 只要链接里包含 quotes/indicative 且是成功的
                if "quotes/indicative" in response.url and response.status == 200:
                    try:
                        data = response.json()
                        if "mark_price" in data:
                            price = float(data["mark_price"])
                            print(f"✅ 抓到了! Variational: {price}")
                    except:
                        pass

            # 开启监听
            page.on("response", handle_response)

            # 打开网页 (可能会稍微慢点，因为要加载JS)
            try:
                page.goto("https://omni.variational.io/perpetual/BTC", timeout=60000)
                # 等待 15 秒，让网页加载数据
                page.wait_for_timeout(15000)
            except Exception as e:
                print(f"⚠️ 网页加载超时，但可能已经抓到数据了: {e}")

            browser.close()
            
    except Exception as e:
        print(f"❌ 浏览器报错: {e}")

    return price

def main():
    print("=== 🚀 启动爬虫版监控 ===")
    p_nado = get_nado_price()
    p_var = get_variational_price()
    
    if p_nado and p_var:
        diff = abs(p_nado - p_var)
        print(f"📉 价差: {diff:.2f}")
        if diff > ALERT_DIFF:
            send_bark(f"价差{diff:.1f}_N{p_nado:.0f}_V{p_var:.0f}")
    else:
        print("❌ 失败")

if __name__ == "__main__":
    main()
