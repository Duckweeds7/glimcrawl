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
@click.option("--size", "-s", type=click.Choice(['l', 'm', 'i']), 
              help="图片尺寸筛选（l:大图，m:中图，i:图标）")
@click.option("--date", "-t", type=click.Choice(['d', 'w', 'm', 'y']), 
              help="时间范围筛选（d:24小时内，w:一周内，m:一月内，y:一年内）")
@click.option("--json", "-j", is_flag=True, help="以JSON格式输出结果")
def download(keyword: str, limit: int, save_dir: str, use_keyword_dir: bool, 
            if_exists: str, size: str, date: str, json: bool):
    """下载Google图片搜索结果"""
    logger.info(f"开始下载关键词 '{keyword}' 的图片")
    logger.info(f"限制数量：{limit}")
    logger.info(f"保存目录：{save_dir}")
    logger.info(f"使用关键词子目录：{use_keyword_dir}")
    logger.info(f"目录存在时处理方式：{if_exists}")
    if size:
        logger.info(f"尺寸筛选：{size}")
    if date:
        logger.info(f"时间范围：{date}")
    
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
            result = await crawler.crawl_images(keyword, size=size, date=date)
            await browser.close()
            
            # 输出结果
            if json:
                click.echo(result.to_dict())
            else:
                click.echo(str(result))
    
    asyncio.run(main())

def main():
    """主入口函数"""
    cli() 