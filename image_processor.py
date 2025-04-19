import os
import hashlib
import re
from PIL import Image
import io
from loguru import logger
from typing import Optional, Tuple

class ImageProcessor:
    """图片处理类，用于处理下载的图片，包括哈希命名、格式转换和优化"""
    
    def __init__(self, base_dir: str = "downloaded_images"):
        """
        初始化图片处理器
        
        Args:
            base_dir: 基础存储目录
        """
        self.base_dir = base_dir
        # 确保基础目录存在
        os.makedirs(base_dir, exist_ok=True)
        
    def sanitize_folder_name(self, folder_name: str) -> str:
        """
        处理文件夹名称，移除不合法字符
        
        Args:
            folder_name: 原始文件夹名称
            
        Returns:
            str: 处理后的文件夹名称
        """
        # 替换不合法字符为下划线
        sanitized = re.sub(r'[\\/*?:"<>|]', '_', folder_name)
        # 移除前后空格
        sanitized = sanitized.strip()
        # 如果为空，使用默认名称
        if not sanitized:
            sanitized = "default"
        return sanitized
        
    def get_folder_path(self, keyword: str) -> str:
        """
        根据关键词获取文件夹路径
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            str: 文件夹路径
        """
        # 处理文件夹名称
        folder_name = self.sanitize_folder_name(keyword)
        # 构建完整路径
        folder_path = os.path.join(self.base_dir, folder_name)
        # 确保文件夹存在
        os.makedirs(folder_path, exist_ok=True)
        return folder_path
        
    def calculate_image_hash(self, image_data: bytes) -> str:
        """
        计算图片数据的哈希值
        
        Args:
            image_data: 图片二进制数据
            
        Returns:
            str: 图片哈希值
        """
        return hashlib.md5(image_data).hexdigest()
        
    def process_image(self, image_data: bytes, max_size: Tuple[int, int] = (1920, 1080), 
                     quality: int = 85) -> Tuple[bytes, str]:
        """
        处理图片：转换为JPG格式，调整大小，优化质量
        
        Args:
            image_data: 原始图片二进制数据
            max_size: 最大尺寸 (宽, 高)
            quality: JPG质量 (1-100)
            
        Returns:
            Tuple[bytes, str]: 处理后的图片数据和哈希值
        """
        try:
            # 打开图片
            img = Image.open(io.BytesIO(image_data))
            
            # 转换为RGB模式（处理PNG等带透明通道的图片）
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[3])  # 使用alpha通道作为mask
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
                
            # 调整大小，保持宽高比
            img.thumbnail(max_size, Image.LANCZOS)
            
            # 保存为JPG格式
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            processed_data = output.getvalue()
            
            # 计算哈希值
            image_hash = self.calculate_image_hash(processed_data)
            
            return processed_data, image_hash
            
        except Exception as e:
            logger.error(f"处理图片时发生错误: {e}")
            # 如果处理失败，返回原始数据和哈希
            return image_data, self.calculate_image_hash(image_data)
            
    def save_image(self, image_data: bytes, keyword: str, index: int) -> Optional[str]:
        """
        保存处理后的图片
        
        Args:
            image_data: 图片二进制数据
            keyword: 搜索关键词
            index: 图片索引
            
        Returns:
            Optional[str]: 保存的文件路径，如果保存失败则返回None
        """
        try:
            # 获取文件夹路径
            folder_path = self.get_folder_path(keyword)
            
            # 处理图片
            processed_data, image_hash = self.process_image(image_data)
            
            # 构建文件路径
            file_path = os.path.join(folder_path, f"{image_hash}.jpg")
            
            # 保存图片
            with open(file_path, 'wb') as f:
                f.write(processed_data)
                
            logger.info(f"图片已保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存图片时发生错误: {e}")
            return None 