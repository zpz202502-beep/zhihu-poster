#!/usr/bin/env python3
"""
知乎文章自动发布脚本 - 最终版
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
    
    cookies = []
    try:
        parsed = json.loads(cookie_string)
        if isinstance(parsed, list):
            return parsed
    except:
        pass
    
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
        title = ""
        body_lines = []
        for line in lines:
            if line.startswith('# ') and not title:
                title = line[2:].strip()
            elif title:
                body_lines.append(line)
        return title, '\n'.join(body_lines)
    return None, None

def post_article(browser):
    title, content = load_article()
    
    if not title or not content:
        print("未找到文章内容")
        return False
    
    print(f"发布: {title}")
    
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale='zh-CN',
        timezone_id='Asia/Shanghai'
    )
    
    page = context.new_page()
    
    # 设置额外的浏览器属性来绕过检测
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    # 1. 先访问知乎首页
    print("访问知乎首页...")
    page.goto("https://www.zhihu.com/", timeout=60000)
    page.wait_for_load_state('networkidle', timeout=30000)
    time.sleep(3)
    
    # 2. 添加Cookie
    print("设置Cookie...")
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
    
    time.sleep(2)
    
    # 3. 刷新页面
    print("刷新页面...")
    page.reload()
    page.wait_for_load_state('networkidle', timeout=30000)
    time.sleep(3)
    
    # 4. 检查登录状态
    print(f"当前页面: {page.title()}")
    
    # 5. 尝试访问创作中心
    print("访问创作中心...")
    page.goto("https://creator.zhihu.com/", timeout=60000)
    page.wait_for_load_state('networkidle', timeout=30000)
    time.sleep(3)
    
    print(f"创作中心页面: {page.title()}")
    
    # 6. 尝试多种方式找到发布按钮
    print("查找发布入口...")
    
    # 尝试点击"写文章"
    try:
        page.click('text=写文章', timeout=5000)
        print("找到写文章按钮")
    except:
        pass
    
    time.sleep(2)
    
    # 7. 输入标题
    print("输入标题...")
    try:
        # 尝试多种选择器
        selectors = [
            'input[placeholder*="标题"]',
            'input[class*="title"]',
            'div[contenteditable="true"]'
        ]
        for sel in selectors:
            try:
                page.fill(sel, title, timeout=3000)
                print(f"使用选择器 {sel} 成功")
                break
            except:
                continue
    except Exception as e:
        print(f"输入标题失败: {e}")
    
    time.sleep(1)
    
    # 8. 输入正文
    print("输入正文...")
    try:
        page.locator('div[contenteditable="true"]').first.fill(content)
    except Exception as e:
        print(f"输入正文失败: {e}")
    
    time.sleep(2)
    
    # 9. 发布
    print("提交发布...")
    try:
        page.click('button:has-text("发布"):not([disabled])', timeout=10000)
        time.sleep(5)
        print("发布完成!")
        context.close()
        return True
    except Exception as e:
        print(f"发布失败: {e}")
        # 保存页面用于调试
        page.screenshot(path='/tmp/debug.png')
        print("已保存截图")
        context.close()
        return False

def main():
    print("=" * 50)
    print("知乎自动发布工具")
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
        success = post_article(browser)
        browser.close()
        
        if success:
            print("=" * 50)
            print("🎉 发布成功!")
            print("=" * 50)
        else:
            print("=" * 50)
            print("❌ 发布失败，请检查")
            print("=" * 50)

if __name__ == "__main__":
    main()
