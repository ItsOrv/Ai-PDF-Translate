#!/usr/bin/env python3

"""
Persian PDF Translator - اسکریپت ترجمه PDF از انگلیسی به فارسی

این اسکریپت PDF‌های انگلیسی را به فارسی ترجمه می‌کند و ساختار و تصاویر سند را حفظ می‌کند.
"""

import os
import logging
import argparse
import time
from dotenv import load_dotenv

from src.config.app_config import AppConfig
from src.extractor.pdf_extractor import PDFExtractor
from src.translator.translator import GeminiTranslator
from src.generator.pdf_generator import PDFGenerator
from src.utils.file_utils import FileUtils

# پیکربندی لاگینگ
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def translate_pdf(input_path, output_path=None, domain="scientific", batch_size=3, use_dummy_translation=False):
    """
    ترجمه یک فایل PDF از انگلیسی به فارسی.
    
    Args:
        input_path: مسیر فایل PDF ورودی
        output_path: مسیر فایل PDF خروجی (اختیاری)
        domain: دامنه ترجمه (general، scientific، medical و غیره)
        batch_size: تعداد متن‌ها برای ترجمه در هر بسته
        use_dummy_translation: استفاده از ترجمه ساختگی برای تست
    
    Returns:
        مسیر فایل PDF ترجمه شده
    """
    start_time = time.time()
    
    # پیکربندی
    config = AppConfig()
    
    # تولید مسیر خروجی اگر مشخص نشده باشد
    if output_path is None:
        output_path = FileUtils.get_output_path(input_path)
    
    logger.info(f"در حال ترجمه PDF: {input_path} -> {output_path}")
    logger.info(f"دامنه ترجمه: {domain}")
    
    # استخراج متن از PDF
    logger.info("استخراج متن از PDF...")
    extractor = PDFExtractor(input_path)
    text_elements = extractor.extract_text_with_layout()
    logger.info(f"تعداد {len(text_elements)} متن استخراج شد")
    
    # نمایش نمونه متن‌های استخراج شده
    if text_elements:
        logger.info("نمونه متن‌ها:")
        for i, element in enumerate(text_elements[:2]):
            position_info = {
                'x0': element.x0, 'y0': element.y0,
                'x1': element.x1, 'y1': element.y1,
                'width': element.width, 'height': element.height
            }
            logger.info(f"متن {i+1}: {element.text[:50]}... در موقعیت {position_info}")
    
    # ترجمه متن‌ها
    if use_dummy_translation:
        # ترجمه ساختگی برای تست (بدون نیاز به API)
        logger.info("استفاده از ترجمه ساختگی برای تست...")
        for element in text_elements:
            # Persian placeholder text
            fake_translation = f"متن ترجمه شده برای: {element.text[:20]}..." if element.text else ""
            element.set_translated_text(fake_translation)
    else:
        # ترجمه واقعی با استفاده از API
        logger.info("راه‌اندازی مترجم...")
        # تنظیم مدل سبک‌تر با تنظیم محیطی
        os.environ["MODEL_NAME"] = "gemini-1.5-flash"
        translator = GeminiTranslator(domain=domain)
        
        # ترجمه متن‌ها
        logger.info(f"ترجمه متن‌ها در بسته‌های {batch_size} تایی...")
        
        # اصلاح برای استفاده از TextElement API فعلی
        try:
            for element in text_elements:
                if element.text and not element.text.isspace():
                    translated_text = translator.translate_text(element.text)
                    element.set_translated_text(translated_text)
                    logger.info(f"ترجمه: '{element.text[:20]}...' -> '{translated_text[:20]}...'")
        except Exception as e:
            logger.error(f"خطا در ترجمه: {str(e)}")
    
    # نمایش نمونه متن‌های ترجمه شده
    if text_elements:
        logger.info("نمونه ترجمه‌ها:")
        for i, element in enumerate(text_elements[:2]):
            if element.translated_text:
                logger.info(f"متن {i+1} ترجمه: {element.translated_text[:50]}...")
            else:
                logger.warning(f"متن {i+1} ترجمه نشده!")
    
    # تولید PDF ترجمه شده
    logger.info("تولید PDF ترجمه شده...")
    generator = PDFGenerator()
    success = generator.generate_translated_pdf(input_path, output_path, text_elements)
    
    if success:
        # افزودن متادیتا
        metadata = extractor.get_document_metadata()
        metadata["producer"] = "Persian PDF Translator"
        metadata["creator"] = "Persian PDF Translator"
        metadata["title"] = f"{metadata.get('title', 'سند ترجمه شده')} (فارسی)"
        generator.add_metadata(output_path, metadata)
        
        elapsed_time = time.time() - start_time
        logger.info(f"ترجمه با موفقیت انجام شد ({elapsed_time:.1f} ثانیه): {output_path}")
        return output_path
    else:
        logger.error("خطا در تولید PDF ترجمه شده")
        return None


def translate_sample_files():
    """ترجمه فایل‌های نمونه موجود در پوشه samples."""
    samples_dir = "samples"
    outputs_dir = "outputs"
    
    # اطمینان از وجود پوشه خروجی
    FileUtils.ensure_directory_exists(outputs_dir)
    
    # تعیین مستقیم فایل‌های PDF
    pdf_files = [
        "samples/yeki.pdf",
        "samples/kiii.pdf"
    ]
    
    # بررسی وجود فایل‌ها
    pdf_files = [f for f in pdf_files if os.path.exists(f)]
    
    if not pdf_files:
        logger.error("هیچ فایل PDF در پوشه samples یافت نشد.")
        return
    
    logger.info(f"تعداد {len(pdf_files)} فایل PDF یافت شد:")
    for pdf_file in pdf_files:
        logger.info(f" - {pdf_file}")
    
    # ترجمه هر فایل 
    for pdf_file in pdf_files:
        # اگر فایل با test_ شروع شود، آن را نادیده بگیر
        if os.path.basename(pdf_file).startswith("test_"):
            logger.info(f"رد کردن فایل تست: {pdf_file}")
            continue
            
        # تعیین مسیر خروجی
        filename = os.path.basename(pdf_file)
        output_filename = f"translated_{filename}"
        output_path = os.path.join(outputs_dir, output_filename)
        
        logger.info(f"درحال ترجمه {filename}...")
        # استفاده از پارامتر use_dummy_translation=True برای جلوگیری از rate limit
        translate_pdf(pdf_file, output_path, domain="scientific", use_dummy_translation=True)


def main():
    """اجرای مترجم PDF فارسی."""
    # خواندن متغیرهای محیطی (اطمینان از وجود GEMINI_API_KEY در فایل .env)
    load_dotenv()
    
    # بررسی وجود کلید API
    config = AppConfig()
    if not config.get_api_key():
        logger.error("کلید API Gemini یافت نشد. لطفا فایل .env را بررسی کنید.")
        return
    
    # ترجمه فایل‌های نمونه
    translate_sample_files()


if __name__ == "__main__":
    main() 