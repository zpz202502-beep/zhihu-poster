#!/usr/bin/env python3
"""
知乎文章自动发布脚本
从 article.md 读取内容并发布到知乎
"""

import os
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# 从环境变量读取Cookie
COOKIE_STRING = os.environ.get('ZHIHOU_COOKIES', '')

def parse_cookies(cookie_string):
    """解析cookie字符串为playwright需要的格式"""
    if not cookie_string:
        return []
    
    cookies = []
    
    # 方法1: 尝试解析JSON格式
    try:
        parsed = json.loads(cookie_string)
        if isinstance(parsed, list):
            # 检查是否已有url/domain
            for c in parsed:
                if 'url' not in c and 'domain' not in c:
                    c['domain'] = '.zhihu.com'
                    c['path'] = '/'
            return parsed
    except:
        pass
    
    # 方法2: 解析 name=value; 格式
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

# 读取文章内容
ARTICLE_FILE = Path(__file__).parent / "article.md"

def load_article():
    """从markdown文件加载文章"""
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
    """发布文章到知乎"""
    title, content = load_article()
    
    if not title or not content:
        print("未找到文章内容")
        return
    
    print(f"发布: {title}")
    
    # 先导航到知乎，让浏览器自动设置正确的域名
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()
    
    # 先访问知乎首页，让domain正确设置
    page.goto("https://www.zhihu.com")
    time.sleep(2)
    
    # 添加cookie到正确的context
    for cookie in ZHIHOU_COOKIES:
        # 移除可能导致问题的字段
        clean_cookie = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie.get('domain', '.zhihu.com'),
            'path': cookie.get('path', '/')
        }
        try:
            context.add_cookies([clean_cookie])
        except Exception as e:
            print(f"添加cookie失败: {cookie['name']}: {e}")
    
    time.sleep(1)
    
    # 1. 打开创作中心
    print("打开创作中心...")
    page.goto("https://www.zhihu.com/creator/content-management/article")
    time.sleep(3)
    
    # 2. 点击发布按钮
    print("点击发布...")
    try:
        page.click('button:has-text("发布文章")', timeout=5000)
    except:
        pass
    time.sleep(2)
    
    # 3. 输入标题
    print("输入标题...")
    page.fill('input[name="title"]', title)
    
    # 4. 输入正文
    print("输入正文...")
    content_box = page.locator('div[contenteditable="true"]').first
    content_box.click()
    content_box.fill(content)
    time.sleep(1)
    
    # 5. 添加话题标签
    print("添加话题...")
    topics = ["素颜霜推荐", "身体素颜霜", "宫芙", "美白", "护肤分享", "好物测评"]
    for topic in topics:
        try:
            page.click('input[placeholder="搜索话题"]')
            page.fill('input[placeholder="搜索话题"]', topic)
            time.sleep(0.5)
            page.click(f'div:has-text("{topic}")', timeout=1500)
            print(f"  + {topic}")
        except:
            pass
    
    # 6. 发布
    print("提交发布...")
    page.click('button:has-text("发布")')
    time.sleep(5)
    
    print("发布成功!")
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
