"""
Google图片爬虫模块
"""

import asyncio
import os
from typing import List, Optional
from loguru import logger
from playwright.async_api import Page, Browser, TimeoutError
from urllib.parse import quote_plus, unquote
import random
import re
from .config import SAVE_DIR
from .image_downloader import ImageDownloader
from .image_processor import ImageProcessor

class GoogleImageCrawler:
    def __init__(self, browser: Browser, max_images: int = 20, save_dir: str = "downloaded_images", proxy: str = None):
        """
        初始化Google图片爬虫
        
        Args:
            browser: Playwright浏览器实例
            max_images: 最大下载图片数量
            save_dir: 图片保存目录
            proxy: 代理服务器地址，格式如 "http://127.0.0.1:1080"
        """
        self.browser = browser
        self.max_images = max_images
        self.save_dir = save_dir
        self.proxy = proxy
        # 创建下载器，并传入代理配置
        self.downloader = ImageDownloader(save_dir=save_dir, max_concurrent=5, proxy=proxy)
        
    async def _wait_for_images(self, page: Page, timeout: int = 10000) -> bool:
        """等待图片加载完成"""
        try:
            # 等待图片容器加载
            await page.wait_for_selector('div[jsname="dTDiAc"]', timeout=timeout)
            # 等待图片元素加载
            await page.wait_for_selector('div[jsname="dTDiAc"] img', timeout=timeout)
            return True
        except TimeoutError:
            logger.warning("等待图片加载超时")
            return False
            
    async def _extract_real_url(self, href: str) -> Optional[str]:
        """从Google重定向链接中提取真实URL"""
        try:
            if 'url=' in href:
                # 提取url参数
                url_match = re.search(r'url=([^&]+)', href)
                if url_match:
                    real_url = unquote(url_match.group(1))
                    if real_url.startswith('http'):
                        return real_url
            return None
        except Exception as e:
            logger.error(f"提取真实URL时发生错误: {e}")
            return None
            
    async def _get_image_url(self, page: Page, element) -> Optional[str]:
        """点击图片并获取真实URL"""
        try:
            # 检查元素是否存在
            if not element:
                logger.warning("未找到图片元素")
                return None
                
            # 获取元素位置
            box = await element.bounding_box()
            if not box:
                logger.warning("无法获取图片元素位置")
                return None
                
            # 滚动到元素位置
            # await page.evaluate('''(y) => {
            #     window.scrollTo({
            #         top: y - window.innerHeight / 2,
            #         behavior: 'smooth'
            #     });
            # }''', box['y'])
            
            # # 等待滚动完成
            # await asyncio.sleep(1)
            
            # 点击图片
            try:
                await element.click(timeout=5000)
            except Exception as e:
                logger.warning(f"点击图片失败: {e}")
                return None
                
            # 等待大图加载，使用较短的超时时间
            try:
                await page.wait_for_selector('img[jsname="kn3ccd"]', timeout=3000)
            except TimeoutError:
                # 如果超时，尝试其他选择器
                try:
                    await page.wait_for_selector('img.sFlh5c.FyHeAf.iPVvYb', timeout=3000)
                except TimeoutError:
                    # 如果还是超时，尝试从链接获取
                    pass
            
            # 首先尝试从链接中获取URL
            image_url = await page.evaluate('''() => {
                const link = document.querySelector('a[data-ved]');
                return link ? link.getAttribute('href') : null;
            }''')
            
            if image_url:
                real_url = await self._extract_real_url(image_url)
                if real_url:
                    logger.debug(f"从链接中获取图片URL: {real_url}")
                    return real_url
            
            # 获取大图URL
            image_url = await page.evaluate('''() => {
                const img = document.querySelector('img[jsname="kn3ccd"]');
                return img ? img.src : null;
            }''')
            
            if image_url and image_url.startswith('http'):
                logger.debug(f"成功获取图片URL: {image_url}")
                return image_url
                
            # 尝试其他选择器
            image_url = await page.evaluate('''() => {
                const img = document.querySelector('img.sFlh5c.FyHeAf.iPVvYb');
                return img ? img.src : null;
            }''')
            
            if image_url and image_url.startswith('http'):
                logger.debug(f"通过备用选择器获取图片URL: {image_url}")
                return image_url
            
            # 如果所有方法都失败，尝试直接从缩略图获取URL
            image_url = await page.evaluate('''() => {
                const img = document.querySelector('div[jsname="dTDiAc"] img');
                return img ? img.src : null;
            }''')
            
            if image_url and image_url.startswith('http'):
                logger.debug(f"从缩略图获取图片URL: {image_url}")
                return image_url
                
            logger.warning("未找到有效的图片URL")
            return None
            
        except TimeoutError:
            logger.warning("获取图片URL超时，跳过当前图片")
            return None
        except Exception as e:
            logger.error(f"获取图片URL时发生错误: {e}")
            return None
            
    async def _scroll_page(self, page: Page, max_scrolls: int = 10):
        """滚动页面加载更多图片"""
        logger.info(f"开始滚动页面，最多滚动 {max_scrolls} 次")
        images = []
        for i in range(max_scrolls):
            try:
                # 滚动到底部
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                # 随机等待
                await asyncio.sleep(random.uniform(1, 2))
                
                # 检查是否有新图片加载
                new_images = await page.query_selector_all('div[jsname="dTDiAc"]')
                if new_images and len(new_images) - len(images) > 0:
                    logger.debug(f"第 {i+1} 次滚动，发现 {len(new_images)-len(images)} 张新图片")
                    images = new_images
                else:
                    logger.debug("没有发现新图片")
                    break
            except Exception as e:
                logger.error(f"滚动页面时发生错误: {e}")
                break
                
    async def _extract_image_urls(self, page: Page, start_index: int = 0) -> int:
        """
        提取图片URL列表并立即开始下载
        
        Args:
            page: 页面对象
            start_index: 开始提取的索引位置
            
        Returns:
            int: 下次开始提取的索引位置
        """
        processed_count = 0
        
        try:
            # 使用更稳定的选择器
            image_elements = await page.query_selector_all('div[jsname="dTDiAc"]')
            logger.info(f"找到 {len(image_elements)} 个图片元素，从索引 {start_index} 开始提取")
            
            # 从指定索引开始提取
            for i in range(start_index, len(image_elements)):
                # 检查是否已达到目标下载数量
                if self.downloader.get_downloaded_count() >= self.max_images:
                    logger.info(f"已达到目标下载数量: {self.downloader.get_downloaded_count()}/{self.max_images}")
                    return i  # 返回当前索引，下次从这继续
                    
                try:
                    # 直接使用元素而不是构建选择器
                    image_url = await self._get_image_url(page, image_elements[i])
                    if image_url:
                        # 立即添加下载任务
                        await self.downloader.add_download_task(image_url, processed_count)
                        processed_count += 1
                        logger.info(f"已处理 {processed_count} 张图片，已下载成功: {self.downloader.get_downloaded_count()}/{self.max_images}")
                        
                    # 随机等待，避免被检测
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    logger.error(f"处理第 {i+1} 张图片时发生错误: {e}")
                    continue
                    
            # 返回当前索引，下次从这继续
            return len(image_elements)
                    
        except Exception as e:
            logger.error(f"提取图片URL时发生错误: {e}")
            return start_index  # 出错时返回起始索引
            
    async def crawl_images(self, keyword: str, size: str = "", date: str = "") -> List[str]:
        """爬取Google图片搜索结果并下载图片"""
        all_image_urls = []
        
        try:
            # 构建搜索URL，不添加start参数
            search_url = f"https://www.google.com/search?q={quote_plus(keyword)}&udm=2"
            if size:
                search_url += f"&tbs=isz:{size}"
            if date:
                search_url += f"&tbs=qdr:{date}"
            logger.info(f"正在爬取图片: {search_url}, 目标数量: {self.max_images}")
            
            # 设置浏览器上下文选项
            context_options = {
                'ignore_https_errors': True,  # 忽略HTTPS证书错误
                'java_script_enabled': True,  # 启用JavaScript
            }
                
            context = await self.browser.new_context(**context_options)
            page = await context.new_page()
            
            try:
                # 访问搜索页面
                await page.goto(search_url, wait_until='networkidle')
                
                # 设置浏览器窗口为全屏
                await self._set_fullscreen(page)
                
                # 等待图片加载
                if not await self._wait_for_images(page):
                    logger.warning("页面加载失败")
                    return []
                    
                # 初始化提取位置
                current_index = 0
                
                # 循环提取和滚动，直到达到目标数量或无法加载更多
                scroll_count = 0
                while self.downloader.get_downloaded_count() < self.max_images and scroll_count < 10:  # 最多滚动10次
                    # 提取图片URL并立即开始下载，从上次位置继续
                    current_index = await self._extract_image_urls(page, current_index)
                    
                    # 如果已经提取完当前页面的所有图片，但下载数量还不够，则滚动加载更多
                    # 使用正确的方法获取元素数量
                    image_elements = await page.query_selector_all('div[jsname="dTDiAc"]')
                    total_images = len(image_elements)
                    
                    if current_index >= total_images:
                        logger.info("当前页面图片已全部提取，滚动加载更多")
                        await self._scroll_page(page)
                        scroll_count += 1
                        
                        # 检查是否有新图片加载
                        new_image_elements = await page.query_selector_all('div[jsname="dTDiAc"]')
                        new_count = len(new_image_elements)
                        if new_count <= current_index:
                            logger.info("没有更多图片可加载")
                            break
                            
                    logger.info(f"当前已处理到第 {current_index} 个图片元素，已下载成功: {self.downloader.get_downloaded_count()}/{self.max_images}")
                    
                logger.info(f"URL提取完成，已下载成功: {self.downloader.get_downloaded_count()}/{self.max_images}")
                
                # 等待所有下载任务完成或达到目标数量
                await self.downloader.wait_for_downloads(target_count=self.max_images)
                
            finally:
                await page.close()
                await context.close()
                
        except Exception as e:
            logger.error(f"爬取图片时发生错误: {e}")
            
        return all_image_urls[:self.max_images]  # 确保不超过请求的数量 
        
    async def _set_fullscreen(self, page: Page) -> None:
        """
        设置浏览器窗口为全屏
        
        Args:
            page: 页面对象
        """
        try:
            # 使用JavaScript设置全屏
            await page.evaluate('''() => {
                // 尝试使用Fullscreen API
                const elem = document.documentElement;
                if (elem.requestFullscreen) {
                    elem.requestFullscreen();
                } else if (elem.webkitRequestFullscreen) { /* Safari */
                    elem.webkitRequestFullscreen();
                } else if (elem.msRequestFullscreen) { /* IE11 */
                    elem.msRequestFullscreen();
                }
                
                // 设置窗口大小为屏幕大小
                window.resizeTo(screen.width, screen.height);
                
                // 最大化窗口
                if (window.screen && window.screen.availWidth && window.screen.availHeight) {
                    window.moveTo(0, 0);
                    window.resizeTo(window.screen.availWidth, window.screen.availHeight);
                }
            }''')
            
            # 使用Playwright API设置视口大小为最大
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            logger.info("已设置浏览器窗口为全屏")
        except Exception as e:
            logger.error(f"设置全屏时发生错误: {e}")

if __name__ == "__main__":
    
    async def main():
        # 导入必要的playwright模块
        from playwright.async_api import async_playwright
        
        # 设置代理地址
        proxy_server = "http://127.0.0.1:1080"  # 代理服务器地址
        
        # 初始化playwright
        async with async_playwright() as p:
            # 启动浏览器，在浏览器级别设置代理
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--start-fullscreen",  # 启动时全屏
                    "--kiosk",  # 启用kiosk模式（全屏无边框）
                    "--disable-infobars",  # 禁用信息栏
                    "--disable-notifications",  # 禁用通知
                    "--disable-extensions",  # 禁用扩展
                    "--window-size=1920,1080"  # 设置窗口大小
                ],
                proxy={"server": proxy_server}  # 在这里设置代理
            )
            
            try:
                # 设置搜索关键词和最大图片数量
                keyword = "猫咪"  # 示例关键词
                max_images = 100  # 最大获取图片数
                save_dir = "downloaded_images"  # 保存目录
                
                # 创建爬虫实例，传入代理配置
                crawler = GoogleImageCrawler(browser, max_images=max_images, save_dir=save_dir, proxy=proxy_server)
                
                # 执行搜索并获取图片URL，同时下载图片
                image_urls = await crawler.crawl_images(keyword)
                
                # 打印结果
                print(f"\n获取到的图片URL列表:")
                for i, url in enumerate(image_urls, 1):
                    print(f"{i}. {url}")
                    
            except Exception as e:
                print(f"运行过程中发生错误: {e}")
            finally:
                # 关闭浏览器
                await browser.close()

    # 运行主函数
    asyncio.run(main())
