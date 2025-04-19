import pytest
import asyncio
import sys

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 