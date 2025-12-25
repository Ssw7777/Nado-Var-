import requests
import time
import sys
from playwright.sync_api import sync_playwright

# ==================== 配置区域 ====================
BARK_URL = "https://api.day.app/LXJuzuCcmf3aR3QP56Ez4o/" 
ALERT_DIFF = 0 # 调试期设为0
# ================================================

def log(text):
    # 强制刷新日志，确保你能看到报错
    print(text, flush=True)

def send_bark(text):
    try:
        url = f"{BARK_URL}价差监控/{text}"
        requests.get(url, timeout=5)
        log(f"✅ Bark 推送: {text}")
    except:
        pass

def get_nado_price():
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
                    log(f"✅ Nado: {p}")
                    return float(p)
    except Exception as e:
        log(f"❌ Nado错: {e}")
    return None

def get_variational_price():
    log("⏳ 启动浏览器...")
    price = None
    
    try:
        with sync_playwright() as p:
            # 关键：加上防检测参数
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled'] 
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 监听 Response
            def handle_response(response):
                nonlocal price
                if "quotes/indicative" in response.url and response.status == 200:
                    try:
                        data = response.json()
                        if "mark_price" in data:
                            price = float(data["mark_price"])
                            log(f"✅ 抓到了! Variational: {price}")
                    except:
                        pass

            page.on("response", handle_response)

            try:
                # 访问网页
                log("🌍 正在打开网页...")
                page.goto("https://omni.variational.io/perpetual/BTC", timeout=60000)
                # 等待久一点，给 Cloudflare 验证的时间
                page.wait_for_timeout(20000)
            except Exception as e:
                log(f"⚠️ 网页加载警报: {e}")

            browser.close()
            
    except Exception as e:
        log(f"❌ 浏览器严重错误: {e}")

    return price

def main():
    log("=== 🚀 启动监控 (Pro版) ===")
    p_nado = get_nado_price()
    p_var = get_variational_price()
    
    if p_nado and p_var:
        diff = abs(p_nado - p_var)
        log(f"📉 最终结果: Nado:{p_nado} | Var:{p_var} | 差:{diff:.2f}")
        if diff > ALERT_DIFF:
            send_bark(f"价差{diff:.1f}_N{p_nado:.0f}_V{p_var:.0f}")
    else:
        log("❌ 任务失败: 至少有一个价格没取到")

if __name__ == "__main__":
    main()
