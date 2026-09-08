#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
release.py — CriptoTradey 发布脚本

自动扫描站点文件，生成 sitemap.xml，并提交 IndexNow 通知 Bing。
以后每发一篇新文章，只需运行 `python3 release.py` 即可：
  1. 自动发现新页面并写进 sitemap.xml
  2. 自动把「新增 URL」提交给 IndexNow（Bing 即时收录）

用法：
  python3 release.py                  # 生成 sitemap + 提交新增 URL
  python3 release.py --dry-run        # 只预览（打印将生成的 URL 和 lastmod），不写入、不提交
  python3 release.py --skip-indexnow  # 只生成 sitemap，不提交 IndexNow
  python3 release.py --all            # IndexNow 提交全部 URL（默认只提交新增）

依赖：仅 Python 标准库，无需 pip install。
"""

import os
import re
import json
import argparse
import datetime
import urllib.request

BASE_URL = "https://criptotradey.com"
INDEXNOW_KEY = "9bbcc70476f442948006a29867011ece"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"

ROOT = os.path.dirname(os.path.abspath(__file__))

# 不收录的文件（文件名精确匹配）
EXCLUDE_FILES = {
    "404.html",                                  # 错误页
    "google9de22e855fa4d285.html",               # Google 站点验证文件
    f"{INDEXNOW_KEY}.txt",                       # IndexNow key 文件
}

# 不收录的目录
EXCLUDE_DIRS = {"assets", ".git", ".claude", "node_modules", ".github"}

# 不收录的后缀（只保留 .html）
EXCLUDE_SUFFIXES = (
    ".css", ".js", ".map", ".webp", ".png", ".jpg", ".jpeg", ".svg",
    ".ico", ".txt", ".json", ".md", ".xml", ".pdf", ".woff", ".woff2",
)


def to_url(rel_path):
    """相对路径 → 站点 URL 路径（保持与现有 URL 规范一致）。

    index.html                          → /
    autor.html                          → /autor.html
    artigos/index.html                  → /artigos/
    artigos/bitcoin-guia-completo.html  → /artigos/bitcoin-guia-completo.html
    artigos/como-sacar-usdt-binance/index.html → /artigos/como-sacar-usdt-binance/
    """
    rel_path = rel_path.replace(os.sep, "/")
    if rel_path == "index.html":
        return "/"
    if rel_path.endswith("/index.html"):
        return "/" + rel_path[: -len("/index.html")] + "/"
    if rel_path.endswith(".html"):
        return "/" + rel_path
    return None


def discover_pages():
    """扫描所有可索引页面，返回 [(url_path, abs_path)]。"""
    pages = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # 剪枝：跳过排除目录和隐藏目录
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS and not d.startswith(".")
        ]
        for fn in filenames:
            if fn.endswith(EXCLUDE_SUFFIXES) or fn in EXCLUDE_FILES:
                continue
            abs_path = os.path.join(dirpath, fn)
            rel = os.path.relpath(abs_path, ROOT)
            url = to_url(rel)
            if url:
                pages.append((url, abs_path))
    return pages


def _mtime(abs_path):
    return datetime.datetime.fromtimestamp(
        os.path.getmtime(abs_path)
    ).strftime("%Y-%m-%d")


def extract_lastmod(abs_path, url, old_lastmod_map):
    """提取 lastmod（YYYY-MM-DD），优先级：

    1. 页面 schema JSON-LD 里的 dateModified（文章的真实修改日）
    2. 旧 sitemap.xml 里的 lastmod（非文章页，保留手写值）
    3. 文件 mtime（全新页面）
    """
    result = None
    try:
        html = open(abs_path, encoding="utf-8").read()
        m = re.search(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})', html)
        if m:
            result = m.group(1)
    except Exception:
        pass

    # 保留旧 sitemap 里更晚的 lastmod，避免 lastmod「回退」
    old = old_lastmod_map.get(f"{BASE_URL}{url}")
    if old and (result is None or old > result):
        result = old

    return result or _mtime(abs_path)


def classify(url):
    """返回 (changefreq, priority)。现代搜索引擎基本忽略这两个值，仅作语义标注。"""
    if url == "/":
        return "daily", "1.0"
    if url.endswith("/"):
        if "/artigos/" in url:
            return "monthly", "0.8"       # 干净 URL 文章
        return "weekly", "0.8"            # 目录页
    if "/artigos/" in url:
        return "monthly", "0.8"           # 文章
    name = url.rsplit("/", 1)[-1][:-5]    # 根目录机构页，去掉 .html
    if name in ("sobre", "autor"):
        return "monthly", "0.6"
    if name == "contato":
        return "monthly", "0.5"
    if name in ("politica-de-privacidade", "termos", "disclaimer"):
        return "yearly", "0.3"
    return "monthly", "0.5"


def read_old_sitemap():
    """读旧 sitemap.xml，返回 (url_set, url→lastmod 映射)。"""
    path = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(path):
        return set(), {}
    xml = open(path, encoding="utf-8").read()
    urls = set(re.findall(r"<loc>(.*?)</loc>", xml))
    lastmod_map = {}
    for m in re.finditer(
        r"<loc>(.*?)</loc>\s*<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>", xml
    ):
        lastmod_map[m.group(1)] = m.group(2)
    return urls, lastmod_map


def build_sitemap(pages, old_lastmod_map):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url, abs_path in pages:
        lastmod = extract_lastmod(abs_path, url, old_lastmod_map)
        freq, prio = classify(url)
        lines.append(
            f"  <url><loc>{BASE_URL}{url}</loc>"
            f"<lastmod>{lastmod}</lastmod>"
            f"<changefreq>{freq}</changefreq>"
            f"<priority>{prio}</priority></url>"
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def indexnow_submit(urls, key=INDEXNOW_KEY):
    key_loc = f"{BASE_URL}/{key}.txt"
    ok = 0
    for u in urls:
        full = f"{BASE_URL}{u}"
        body = json.dumps({
            "host": "criptotradey.com",
            "key": key,
            "keyLocation": key_loc,
            "urlList": [full],
        }).encode("utf-8")
        req = urllib.request.Request(
            INDEXNOW_ENDPOINT, data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                print(f"  {r.status}  {full}")
                ok += 1
        except Exception as e:
            print(f"  ERR  {full}  ({e})")
    return ok


def main():
    ap = argparse.ArgumentParser(description="生成 sitemap.xml 并提交 IndexNow")
    ap.add_argument("--dry-run", action="store_true", help="只预览，不写入不提交")
    ap.add_argument("--skip-indexnow", action="store_true", help="只生成 sitemap")
    ap.add_argument("--all", action="store_true", help="IndexNow 提交全部 URL（默认只提交新增）")
    args = ap.parse_args()

    pages = discover_pages()
    # 首页最前，其余按 URL 字母序（保证每次输出顺序确定，便于 diff）
    pages.sort(key=lambda p: (p[0] != "/", p[0]))

    old_urls, old_lastmod_map = read_old_sitemap()
    added = [u for u, _ in pages if f"{BASE_URL}{u}" not in old_urls]

    print(f"发现 {len(pages)} 个可索引页面；新增 {len(added)} 个 URL")

    if args.dry_run:
        for url, abs_path in pages:
            print(f"  {extract_lastmod(abs_path, url, old_lastmod_map)}  {url}")
        if added:
            print("\n新增 URL：")
            for u in added:
                print(f"  + {u}")
        return

    sitemap = build_sitemap(pages, old_lastmod_map)
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)
    print("sitemap.xml 已更新")

    if args.skip_indexnow:
        print("已跳过 IndexNow（--skip-indexnow）")
        return

    submit = [u for u, _ in pages] if args.all else added
    if not submit:
        print("没有需要提交的 URL（全部已存在于 sitemap）")
        return
    print(f"提交 {len(submit)} 个 URL 到 IndexNow…")
    ok = indexnow_submit(submit)
    print(f"完成：{ok}/{len(submit)} 成功")


if __name__ == "__main__":
    main()
