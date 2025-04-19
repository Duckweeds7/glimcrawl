# GlimCrawl

一个强大的Google图片爬虫工具，支持批量下载、图片处理和代理设置。

## 特性

- 支持Google图片搜索结果的批量下载
- 异步并发下载，提高效率
- 自动图片处理和优化
- 支持代理设置
- 支持图片尺寸和时间筛选
- 命令行界面，易于使用
- 支持作为Python库导入使用

## 安装

```bash
# 从PyPI安装
pip install glimcrawl

# 从源码安装
git clone https://gitee.com/duckweeds7/glimcrawl.git
cd glimcrawl
pip install -e .
```

## 快速开始

### 命令行使用

```bash
# 基本使用
glimcrawl download "猫咪"

# 指定下载数量
glimcrawl download "猫咪" -n 50

# 指定保存目录
glimcrawl download "猫咪" -d ./images

# 使用代理
glimcrawl download "猫咪" -p http://127.0.0.1:1080

# 筛选大图
glimcrawl download "猫咪" -s l

# 筛选最近一周的图片
glimcrawl download "猫咪" -t w
```

### 作为Python库使用

```python
import asyncio
from glimcrawl import GoogleImageCrawler
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        crawler = GoogleImageCrawler(
            browser=browser,
            max_images=20,
            save_dir="downloaded_images",
            proxy="http://127.0.0.1:1080"  # 可选
        )
        await crawler.crawl_images("猫咪", size="l", date="w")
        await browser.close()

asyncio.run(main())
```

## 参数说明

### 命令行参数

- `keyword`: 搜索关键词（必需）
- `-n, --max-images`: 最大下载图片数量（默认：20）
- `-d, --save-dir`: 图片保存目录（默认：downloaded_images）
- `-p, --proxy`: 代理服务器地址
- `-s, --size`: 图片尺寸筛选
  - l: 大图
  - m: 中图
  - i: 图标
- `-t, --date`: 时间筛选
  - d: 一天内
  - w: 一周内
  - m: 一月内
  - y: 一年内

### Python API

#### GoogleImageCrawler

```python
class GoogleImageCrawler:
    def __init__(
        self,
        browser: Browser,
        max_images: int = 20,
        save_dir: str = "downloaded_images",
        proxy: str = None
    ):
        """
        初始化Google图片爬虫
        
        Args:
            browser: Playwright浏览器实例
            max_images: 最大下载图片数量
            save_dir: 图片保存目录
            proxy: 代理服务器地址
        """
        pass

    async def crawl_images(
        self,
        keyword: str,
        size: str = "",
        date: str = ""
    ) -> List[str]:
        """
        爬取Google图片搜索结果
        
        Args:
            keyword: 搜索关键词
            size: 图片尺寸筛选
            date: 时间筛选
            
        Returns:
            List[str]: 下载的图片URL列表
        """
        pass
```

## 注意事项

1. 使用前请确保已安装Playwright浏览器：
   ```bash
   playwright install chromium
   ```

2. 如果遇到网络问题，可以尝试使用代理：
   ```bash
   glimcrawl download "关键词" -p http://your-proxy:port
   ```

3. 下载的图片会自动进行优化处理：
   - 转换为JPG格式
   - 调整大小（最大1920x1080）
   - 优化质量（85%）
   - 使用MD5哈希命名

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
