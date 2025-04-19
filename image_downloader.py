import asyncio
import os
import aiohttp
import aiofiles
from typing import List, Dict, Optional, Callable
from loguru import logger
from urllib.parse import urlparse
from image_processor import ImageProcessor

class ImageDownloader:
    """异步图片下载器，支持并行下载和进度跟踪"""
    
    def __init__(self, save_dir: str = "downloaded_images", max_concurrent: int = 5, proxy: str = None):
        """
        初始化下载器
        
        Args:
            save_dir: 图片保存目录
            max_concurrent: 最大并发下载数
            proxy: 代理服务器地址，格式如 "http://127.0.0.1:1080"
        """
        self.save_dir = save_dir
        self.max_concurrent = max_concurrent
        self.proxy = proxy
        self.downloaded_count = 0
        self.failed_count = 0
        self.total_count = 0
        self.download_tasks = {}
        self._download_semaphore = asyncio.Semaphore(max_concurrent)
        self._download_event = asyncio.Event()
        self._download_event.set()  # 初始状态为允许下载
        self.image_processor = ImageProcessor(base_dir=save_dir)
        
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
        
    async def _download_single_image(self, url: str, index: int, keyword: str = "default") -> bool:
        """
        下载单张图片
        
        Args:
            url: 图片URL
            index: 图片索引
            keyword: 搜索关键词，用于创建子文件夹
            
        Returns:
            bool: 下载是否成功
        """
        try:
            # 使用信号量限制并发数
            async with self._download_semaphore:
                # 检查是否应该停止下载
                if not self._download_event.is_set():
                    logger.info(f"下载已停止，跳过图片: {url}")
                    return False
                
                # 配置代理
                proxy = self.proxy
                if proxy:
                    logger.debug(f"使用代理下载图片: {proxy}")
                
                # 下载图片
                async with aiohttp.ClientSession() as session:
                    # 设置代理
                    if proxy:
                        async with session.get(url, timeout=30, proxy=proxy) as response:
                            if response.status == 200:
                                # 读取图片数据
                                image_data = await response.read()
                                
                                # 使用图片处理器处理和保存图片
                                save_path = self.image_processor.save_image(image_data, keyword, index)
                                
                                if save_path:
                                    logger.info(f"成功下载并处理图片: {save_path}")
                                    return True
                                else:
                                    logger.warning(f"处理图片失败: {url}")
                                    return False
                            else:
                                logger.warning(f"下载图片失败，状态码: {response.status}, URL: {url}")
                                return False
                    else:
                        async with session.get(url, timeout=30) as response:
                            if response.status == 200:
                                # 读取图片数据
                                image_data = await response.read()
                                
                                # 使用图片处理器处理和保存图片
                                save_path = self.image_processor.save_image(image_data, keyword, index)
                                
                                if save_path:
                                    logger.info(f"成功下载并处理图片: {save_path}")
                                    return True
                                else:
                                    logger.warning(f"处理图片失败: {url}")
                                    return False
                            else:
                                logger.warning(f"下载图片失败，状态码: {response.status}, URL: {url}")
                                return False
                            
        except Exception as e:
            logger.error(f"下载图片时发生错误: {e}, URL: {url}")
            return False
            
    async def add_download_task(self, url: str, index: int, keyword: str = "default") -> None:
        """
        添加下载任务
        
        Args:
            url: 图片URL
            index: 图片索引
            keyword: 搜索关键词，用于创建子文件夹
        """
        if not self._download_event.is_set():
            logger.info(f"下载已停止，不再添加新任务: {url}")
            return
            
        self.total_count += 1
        task = asyncio.create_task(self._download_single_image(url, index, keyword))
        self.download_tasks[url] = task
        
        # 添加回调以更新计数
        task.add_done_callback(self._task_done_callback)
        
    def _task_done_callback(self, task):
        """任务完成回调，更新下载计数"""
        try:
            result = task.result()
            if result:
                self.downloaded_count += 1
            else:
                self.failed_count += 1
        except Exception as e:
            logger.error(f"任务回调处理错误: {e}")
            self.failed_count += 1
            
    def stop_download(self) -> None:
        """停止所有下载任务"""
        self._download_event.clear()
        logger.info("已停止所有下载任务")
        
    def resume_download(self) -> None:
        """恢复下载任务"""
        self._download_event.set()
        logger.info("已恢复下载任务")
        
    async def wait_for_downloads(self, target_count: Optional[int] = None) -> None:
        """
        等待下载任务完成
        
        Args:
            target_count: 目标下载数量，如果达到此数量则停止
        """
        if not self.download_tasks:
            logger.info("没有下载任务")
            return
            
        while True:
            # 检查是否达到目标数量
            if target_count is not None and self.downloaded_count >= target_count:
                logger.info(f"已达到目标下载数量: {self.downloaded_count}/{target_count}")
                self.stop_download()
                break
                
            # 检查是否所有任务都已完成
            if all(task.done() for task in self.download_tasks.values()):
                logger.info("所有下载任务已完成")
                break
                
            # 等待一段时间再检查
            await asyncio.sleep(1)
            
        # 等待所有任务完成
        if self.download_tasks:
            await asyncio.gather(*self.download_tasks.values(), return_exceptions=True)
            
        logger.info(f"下载完成，成功: {self.downloaded_count}, 失败: {self.failed_count}, 总计: {self.total_count}")
        
    def get_downloaded_count(self) -> int:
        """获取已下载成功的图片数量"""
        return self.downloaded_count
        
    def get_failed_count(self) -> int:
        """获取下载失败的图片数量"""
        return self.failed_count
        
    def get_total_count(self) -> int:
        """获取总任务数量"""
        return self.total_count 