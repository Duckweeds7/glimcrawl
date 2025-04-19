import os
import pytest
from PIL import Image
import io
from glimcrawl.image_processor import ImageProcessor

@pytest.fixture
def image_processor(tmp_path):
    """创建测试用的图片处理器实例"""
    return ImageProcessor(base_dir=str(tmp_path))

@pytest.fixture
def sample_image():
    """创建测试用的示例图片"""
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def test_sanitize_folder_name(image_processor):
    """测试文件夹名称清理功能"""
    assert image_processor.sanitize_folder_name("test/folder") == "test_folder"
    assert image_processor.sanitize_folder_name("test\\folder") == "test_folder"
    assert image_processor.sanitize_folder_name("test*folder") == "test_folder"
    assert image_processor.sanitize_folder_name("  test  ") == "test"
    assert image_processor.sanitize_folder_name("") == "default"

def test_get_folder_path(image_processor, tmp_path):
    """测试文件夹路径获取功能"""
    folder_path = image_processor.get_folder_path("test folder")
    assert folder_path == os.path.join(str(tmp_path), "test folder")
    assert os.path.exists(folder_path)

def test_process_image(image_processor, sample_image):
    """测试图片处理功能"""
    processed_data, image_hash = image_processor.process_image(sample_image)
    assert isinstance(processed_data, bytes)
    assert isinstance(image_hash, str)
    assert len(image_hash) == 32  # MD5哈希长度

def test_save_image(image_processor, sample_image, tmp_path):
    """测试图片保存功能"""
    save_path = image_processor.save_image(sample_image, "test", 1)
    assert save_path is not None
    assert os.path.exists(save_path)
    assert save_path.startswith(str(tmp_path))
    assert save_path.endswith(".jpg")

def test_save_image_invalid_data(image_processor):
    """测试保存无效图片数据"""
    save_path = image_processor.save_image(b"invalid data", "test", 1)
    assert save_path is None 