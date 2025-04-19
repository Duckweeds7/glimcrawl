# GlimCrawl

[![PyPI version](https://img.shields.io/pypi/v/glimcrawl.svg)](https://pypi.org/project/glimcrawl/)
[![Python Version](https://img.shields.io/pypi/pyversions/glimcrawl.svg)](https://pypi.org/project/glimcrawl/)
[![License](https://img.shields.io/pypi/l/glimcrawl.svg)](https://gitee.com/duckweeds7/glimcrawl/blob/master/LICENSE)

[English](README.en.md) | 简体中文

一个强大的 Google 图片爬虫工具，支持批量下载、图片处理和代理设置。名称来源：glimpse（一瞥）+ crawl（爬行），强调"快速捕捉网络图片片段"。

## ✨ 特性

- 🚀 异步并发下载，提高效率
- 🎨 自动图片处理和优化（去水印、调整大小等）
- 🌐 支持代理设置，解决网络问题
- 📏 支持图片尺寸和时间筛选
- 🖥️ 命令行界面，易于使用
- 📦 支持作为 Python 库导入使用
- 🔒 安全可靠，遵循 Google 搜索规范

## 📦 安装

```bash
# 从 PyPI 安装（推荐）
pip install glimcrawl

# 安装 Playwright 浏览器（必需）
playwright install chromium
```

## 🚀 快速开始

### 命令行使用

```bash
# 基本使用
glimcrawl download "猫咪"

# 指定下载数量和保存目录
glimcrawl download "猫咪" -n 50 -d ./images

# 使用代理
glimcrawl download "猫咪" -p http://127.0.0.1:1080

# 筛选大图和最近图片
glimcrawl download "猫咪" -s l -t w
```

### Python 库使用

```python
import asyncio
from glimcrawl import GoogleImageCrawler
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        crawler = GoogleImageCrawler(browser)
        # 下载 20 张猫咪图片到 images 目录
        await crawler.crawl_images("猫咪", max_images=20, save_dir="images")
        await browser.close()

asyncio.run(main())
```

## 📝 参数说明

### 命令行参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `keyword` | 搜索关键词（必需） | - | `"猫咪"` |
| `-n, --max-images` | 最大下载数量 | 20 | `-n 50` |
| `-d, --save-dir` | 保存目录 | downloaded_images | `-d ./images` |
| `-p, --proxy` | 代理服务器 | None | `-p http://127.0.0.1:1080` |
| `-s, --size` | 图片尺寸 | None | `-s l` (大图) |
| `-t, --date` | 时间范围 | None | `-t w` (一周内) |

### 图片尺寸选项

- `l`: 大图
- `m`: 中图
- `i`: 图标

### 时间范围选项

- `d`: 24小时内
- `w`: 一周内
- `m`: 一月内
- `y`: 一年内

## 🛠️ 图片处理

下载的图片会自动进行以下处理：

1. 格式转换：统一转为 JPG 格式
2. 尺寸调整：最大 1920x1080，保持比例
3. 质量优化：85% 压缩率
4. 文件命名：使用 MD5 哈希，避免重复
5. 去水印：自动识别和移除水印（实验性功能）

## 🔒 安全建议

1. 使用代理时建议配置 HTTPS 代理
2. 遵循目标网站的爬虫规范
3. 合理设置下载间隔和并发数
4. 图片仅供学习研究使用

## 🤝 贡献

1. Fork 本仓库
2. 创建新分支: `git checkout -b feat/new-feature`
3. 提交更改: `git commit -am 'feat: add new feature'`
4. 推送分支: `git push origin feat/new-feature`
5. 提交 Pull Request

## 📄 许可证

[MIT License](LICENSE) © 2024 Duckweeds7
