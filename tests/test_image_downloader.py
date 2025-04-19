import pytest
import aiohttp
import asyncio
from unittest.mock import Mock, patch
from glimcrawl.image_downloader import ImageDownloader

@pytest.fixture
def image_downloader(tmp_path):
    """创建测试用的图片下载器实例"""
    return ImageDownloader(save_dir=str(tmp_path), max_concurrent=2)

@pytest.fixture
def mock_response():
    """创建模拟的HTTP响应"""
    mock = Mock()
    mock.status = 200
    mock.read = asyncio.coroutine(lambda: b"fake image data")
    return mock

@pytest.fixture
def mock_session(mock_response):
    """创建模拟的aiohttp会话"""
    mock = Mock()
    mock.get = asyncio.coroutine(lambda *args, **kwargs: mock_response)
    mock.__aenter__ = asyncio.coroutine(lambda: mock)
    mock.__aexit__ = asyncio.coroutine(lambda *args: None)
    return mock

@pytest.mark.asyncio
async def test_add_download_task(image_downloader, mock_session):
    """测试添加下载任务"""
    with patch('aiohttp.ClientSession', return_value=mock_session):
        await image_downloader.add_download_task("http://example.com/image.jpg", 1)
        assert len(image_downloader.download_tasks) == 1
        assert image_downloader.total_count == 1

@pytest.mark.asyncio
async def test_download_single_image_success(image_downloader, mock_session):
    """测试成功下载单张图片"""
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await image_downloader._download_single_image(
            "http://example.com/image.jpg", 1
        )
        assert result is True
        assert image_downloader.downloaded_count == 1

@pytest.mark.asyncio
async def test_download_single_image_failure(image_downloader, mock_session):
    """测试下载单张图片失败"""
    mock_session.get.return_value.status = 404
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await image_downloader._download_single_image(
            "http://example.com/image.jpg", 1
        )
        assert result is False
        assert image_downloader.failed_count == 1

@pytest.mark.asyncio
async def test_wait_for_downloads(image_downloader, mock_session):
    """测试等待下载完成"""
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # 添加多个下载任务
        for i in range(3):
            await image_downloader.add_download_task(
                f"http://example.com/image{i}.jpg", i
            )
        
        # 等待所有下载完成
        await image_downloader.wait_for_downloads()
        
        assert image_downloader.downloaded_count == 3
        assert image_downloader.failed_count == 0
        assert image_downloader.total_count == 3

@pytest.mark.asyncio
async def test_stop_and_resume_download(image_downloader):
    """测试停止和恢复下载"""
    image_downloader.stop_download()
    assert not image_downloader._download_event.is_set()
    
    image_downloader.resume_download()
    assert image_downloader._download_event.is_set()

def test_get_counts(image_downloader):
    """测试获取计数"""
    assert image_downloader.get_downloaded_count() == 0
    assert image_downloader.get_failed_count() == 0
    assert image_downloader.get_total_count() == 0 