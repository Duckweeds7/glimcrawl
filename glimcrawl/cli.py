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
@click.option("--save-dir", "-d", default="images", help="保存目录的根路径")
@click.option("--use-keyword-dir/--no-keyword-dir", default=True, 
              help="是否使用关键词创建子目录（默认：是）")
@click.option("--if-exists", "-e", type=click.Choice(['skip', 'overwrite', 'rename']), 
              default='rename', help="目录已存在时的处理方式（跳过/覆盖/重命名，默认：重命名）")
def download(keyword: str, limit: int, save_dir: str, use_keyword_dir: bool, if_exists: str):
    """下载Google图片搜索结果"""
    logger.info(f"开始下载关键词 '{keyword}' 的图片")
    logger.info(f"限制数量：{limit}")
    logger.info(f"保存目录：{save_dir}")
    logger.info(f"使用关键词子目录：{use_keyword_dir}")
    logger.info(f"目录存在时处理方式：{if_exists}")
    
    async def main():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            crawler = GoogleImageCrawler(
                browser, 
                max_images=limit, 
                save_dir=save_dir,
                use_keyword_dir=use_keyword_dir,
                if_exists=if_exists
            )
            await crawler.crawl_images(keyword)
            await browser.close()
    
    asyncio.run(main())

def main():
    """主入口函数"""
    cli() 