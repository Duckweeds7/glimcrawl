"""
命令行接口模块
"""

import asyncio
import click
from loguru import logger
from playwright.async_api import async_playwright

from .google_image import GoogleImageCrawler

@click.group()
def cli():
    """Google图片爬虫工具"""
    pass

@cli.command()
@click.argument("keyword")
@click.option("--limit", "-l", default=100, help="下载图片数量限制")
@click.option("--save-dir", "-s", default="images", help="保存目录")
def download(keyword: str, limit: int, save_dir: str):
    """下载Google图片搜索结果"""
    logger.info(f"开始下载关键词 '{keyword}' 的图片，限制数量：{limit}，保存目录：{save_dir}")
    
    async def main():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            crawler = GoogleImageCrawler(browser, max_images=limit, save_dir=save_dir)
            await crawler.crawl_images(keyword)
            await browser.close()
    
    asyncio.run(main())

def main():
    """主入口函数"""
    cli() 