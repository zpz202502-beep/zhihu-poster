#!/usr/bin/env python3
"""
知乎文章自动发布 - 反检测版本
"""

import os
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIE_STRING = os.environ.get('ZHIHOU_COOKIES', '')

def parse_cookies(cookie_string):
    if not cookie_string:
        return []
    try:
        parsed = json.loads(cookie_string)
        if isinstance(parsed, list):
            return parsed
    except:
        pass
    cookies = []
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            cookies.append({'name': name.strip(), 'value': value.strip()})
    return cookies

ZHIHOU_COOKIES = parse_cookies(COOKIE_STRING)
ARTICLE_FILE = Path(__file__).parent / "article.md"

def load_article():
    if ARTICLE_FILE.exists():
        content = ARTICLE_FILE.read_text(encoding='utf-8')
        lines = content.strip().split('\n')
        title, body = "", []
        for line in lines:
            if line.startswith('# ') and not title:
                title = line[2:].strip()
            elif title:
                body.append(line)
        return title, '\n'.join(body)
    return None, None

def stealth_context(browser):
    """创建反检测context"""
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale='zh-CN',
        timezone_id='Asia/Shanghai',
        permissions=['geolocation', 'notifications']
    )
    
    # 反检测脚本
    context.add_init_script("""
        // 隐藏webdriver
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        
        // 模拟真实浏览器
        window.navigator.chrome = { runtime: {} };
        
        // 修改permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // 模拟插件
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // 模拟languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
    """)
    
    return context

def post_article(browser):
    title, content = load_article()
    if not title or not content:
        print("未找到文章")
        return False
    
    print(f"发布: {title}")
    
    context = stealth_context(browser)
    page = context.new_page()
    
    # 分阶段访问，建立会话
    print("1. 访问知乎...")
    page.goto("https://www.zhihu.com/", timeout=60000)
    time.sleep(5)
    
    # 设置cookie
    print("2. 设置Cookie...")
    for cookie in ZHIHOU_COOKIES:
        try:
            context.add_cookies([{
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': '.zhihu.com',
                'path': '/'
            }])
        except:
            pass
    
    time.sleep(3)
    
    print("3. 检查页面...")
    page_url = page.url
    print(f"   当前URL: {page_url}")
    print(f"   页面标题: {page.title()}")
    
    # 如果需要验证
    if "安全验证" in page.title():
        print("⚠️ 需要验证码，等待中...")
        time.sleep(10)
        
        # 再试一次
        page.reload()
        time.sleep(5)
        
        if "安全验证" in page.title():
            print("❌ 验证码未通过")
            context.close()
            return False
    
    # 访问创作中心
    print("4. 访问创作中心...")
    try:
        page.goto("https://creator.zhihu.com/", timeout=60000)
        time.sleep(5)
    except:
        pass
    
    print(f"   页面: {page.title()}")
    
    # 尝试发布
    print("5. 尝试发布...")
    try:
        page.click('text=写文章', timeout=5000)
    except:
        pass
    
    time.sleep(3)
    
    # 输入
    print("6. 输入内容...")
    try:
        page.fill('input[placeholder*="标题"]', title)
    except:
        try:
            page.locator('div[contenteditable="true"]').first.click()
            page.keyboard.type(title, delay=50)
        except:
            pass
    
    time.sleep(1)
    
    try:
        page.locator('div[contenteditable="true"]').last.fill(content)
    except:
        pass
    
    time.sleep(2)
    
    # 发布
    print("7. 发布...")
    try:
        page.click('button:has-text("发布")', timeout=10000)
        time.sleep(5)
        print("✅ 发布成功!")
        context.close()
        return True
    except Exception as e:
        print(f"❌ 发布失败: {e}")
        context.close()
        return False

def main():
    print("=" * 50)
    print("知乎自动发布工具 - 反检测版")
    print("=" * 50)
    
    if not ZHIHOU_COOKIES:
        print("请设置Cookie")
        return
    
    print(f"已加载 {len(ZHIHOU_COOKIES)} 个Cookie")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        result = post_article(browser)
        browser.close()
        
        if result:
            print("\n🎉 任务完成!")
        else:
            print("\n⚠️ 任务未完成")

if __name__ == "__main__":
    main()
