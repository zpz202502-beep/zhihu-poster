#!/usr/bin/env python3
"""
知乎文章自动发布 - 移动端版本
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

def post_article(browser):
    title, content = load_article()
    if not title or not content:
        print("未找到文章")
        return False
    
    print(f"发布: {title}")
    
    # 使用移动端UA
    context = browser.new_context(
        viewport={'width': 375, 'height': 812},
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True
    )
    
    page = context.new_page()
    
    # 尝试移动端登录
    print("1. 访问知乎移动端...")
    try:
        page.goto("https://www.zhihu.com/", timeout=30000)
        time.sleep(5)
    except Exception as e:
        print(f"访问失败: {e}")
    
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
    
    print(f"页面: {page.title()}")
    
    # 尝试发布
    print("3. 查找发布入口...")
    try:
        # 移动端可能入口不同
        page.click('text=写文章', timeout=5000)
    except:
        try:
            page.click('text=发布', timeout=5000)
        except:
            print("未找到发布入口")
    
    time.sleep(3)
    
    # 输入内容
    print("4. 输入内容...")
    try:
        # 移动端选择器
        page.fill('input[type="text"]', title)
    except:
        pass
    
    try:
        page.locator('div[contenteditable="true"]').first.fill(content)
    except:
        pass
    
    time.sleep(2)
    
    # 发布
    print("5. 发布...")
    try:
        page.click('button:has-text("发布")', timeout=5000)
        time.sleep(5)
        print("✅ 成功!")
        context.close()
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        context.close()
        return False

def main():
    print("=" * 50)
    print("知乎发布 - 移动端版")
    print("=" * 50)
    
    if not ZHIHOU_COOKIES:
        print("请设置Cookie")
        return
    
    print(f"已加载 {len(ZHIHOU_COOKIES)} 个Cookie")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        result = post_article(browser)
        browser.close()

if __name__ == "__main__":
    main()
