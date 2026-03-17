#!/usr/bin/env python3
"""
知乎文章自动发布脚本 - 优化版
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
            for c in parsed:
                if 'url' not in c and 'domain' not in c:
                    c['domain'] = '.zhihu.com'
                    c['path'] = '/'
            return parsed
    except:
        pass
    
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.zhihu.com',
                'path': '/',
                'secure': True,
                'httpOnly': False
            })
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
        return
    
    print(f"发布: {title}")
    
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    page = context.new_page()
    
    # 先访问知乎
    print("访问知乎...")
    page.goto("https://www.zhihu.com", timeout=60000)
    time.sleep(5)
    
    # 添加cookie
    for cookie in ZHIHOU_COOKIES:
        try:
            context.add_cookies([{
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain', '.zhihu.com'),
                'path': cookie.get('path', '/')
            }])
        except:
            pass
    
    time.sleep(3)
    
    # 检查是否已登录
    page.goto("https://www.zhihu.com/creator/content-management/article", timeout=60000)
    time.sleep(5)
    
    # 打印页面标题用于调试
    print(f"页面标题: {page.title()}")
    
    # 尝试多种选择器
    try:
        # 尝试点击发布按钮
        print("查找发布按钮...")
        page.click('button:has-text("发布文章")', timeout=10000)
    except Exception as e:
        print(f"点击发布按钮失败: {e}")
        # 保存截图用于调试
        page.screenshot(path='/tmp/zhihu_debug.png')
        print("已保存截图到 /tmp/zhihu_debug.png")
        context.close()
        return
    
    time.sleep(3)
    
    # 输入标题 - 尝试多种选择器
    print("输入标题...")
    try:
        page.fill('input[name="title"]', title, timeout=5000)
    except:
        try:
            page.fill('input[placeholder*="标题"]', title, timeout=5000)
        except:
            page.locator('div[contenteditable="true"]').first.click()
            time.sleep(1)
    
    # 输入正文
    print("输入正文...")
    try:
        page.locator('div[contenteditable="true"]').first.fill(content)
    except Exception as e:
        print(f"输入正文失败: {e}")
    
    time.sleep(2)
    
    # 添加话题
    print("添加话题...")
    topics = ["素颜霜推荐", "身体素颜霜", "宫芙", "美白", "护肤分享", "好物测评"]
    for topic in topics:
        try:
            page.click('input[placeholder*="话题"]')
            page.fill('input[placeholder*="话题"]', topic)
            time.sleep(0.5)
            page.click(f'div:has-text("{topic}")', timeout=2000)
            print(f"  + {topic}")
        except:
            pass
    
    # 发布
    print("提交发布...")
    try:
        page.click('button:has-text("发布")', timeout=5000)
        time.sleep(3)
        print("发布成功!")
    except Exception as e:
        print(f"发布失败: {e}")
        page.screenshot(path='/tmp/zhihu_publish.png')
    
    context.close()

def main():
    print("=" * 50)
    print("知乎自动发布工具")
    print("=" * 50)
    
    if not ZHIHOU_COOKIES:
        print("请设置Cookie")
        return
    
    print(f"已加载 {len(ZHIHOU_COOKIES)} 个Cookie")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        post_article(browser)
        browser.close()

if __name__ == "__main__":
    main()
