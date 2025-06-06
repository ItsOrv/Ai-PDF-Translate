"""
Prompt templates for different translation domains.
"""

from typing import Dict
from src.config.constants import Constants


class PromptTemplates:
    """
    Provides prompt templates for different translation domains.
    """
    
    # General purpose translation prompt
    GENERAL = """Translate the following English text to Persian (Farsi). Only provide the translation, no explanations or additional text, just translate the text directly:

{text}"""
    
    # Scientific domain translation prompt
    SCIENTIFIC = """متن زیر را از زبان انگلیسی به زبان فارسی به صورت حرفه‌ای و دقیق ترجمه کن. در ترجمه به موارد زیر توجه کن:

1. استفاده از اصطلاحات و واژگان تخصصی دقیق در حوزه علمی مربوطه و رعایت استانداردهای علمی پذیرفته‌شده.
2. حفظ سبک علمی، دانشگاهی و تخصصی متن اصلی بدون تغییر معنا یا ابهام در مفاهیم.
3. اطمینان از صحت ساختار جملات به گونه‌ای که هم از نظر دستوری و هم از نظر مفهومی به بهترین نحو به زبان فارسی منتقل شود.
4. در صورت وجود اصطلاح یا مفهوم دشوار، در صورت امکان ارائه معادل تخصصی مربوطه.
5. رعایت تناسب و انسجام متن به گونه‌ای که همخوانی مفهومی و ساختاری حفظ شود.

فقط متن ترجمه شده را بازگردان، بدون هیچ توضیح اضافی:

{text}"""
    
    # Genetic domain translation prompt
    GENETIC = """متن زیر را از زبان انگلیسی به زبان فارسی به صورت حرفه‌ای و دقیق ترجمه کن. در ترجمه به موارد زیر توجه کن:

1. استفاده از اصطلاحات و واژگان تخصصی دقیق در حوزه ژنتیک (مانند DNA، RNA، ژن، اپی‌ژنتیک، موتاسیون و سایر مفاهیم مرتبط) و رعایت استانداردهای علمی پذیرفته‌شده.
2. حفظ سبک علمی، دانشگاهی و تخصصی متن اصلی بدون تغییر معنا یا ابهام در مفاهیم.
3. اطمینان از صحت ساختار جملات به گونه‌ای که هم از نظر دستوری و هم از نظر مفهومی به بهترین نحو به زبان فارسی منتقل شود.
4. در صورت وجود اصطلاح یا مفهوم دشوار، در صورت امکان ارائه معادل تخصصی مربوطه.
5. رعایت تناسب و انسجام متن به گونه‌ای که همخوانی مفهومی و ساختاری حفظ شود.

فقط متن ترجمه شده را بازگردان، بدون هیچ توضیح اضافی:

{text}"""
    
    # Medical domain translation prompt
    MEDICAL = """متن زیر را از زبان انگلیسی به زبان فارسی به صورت حرفه‌ای و دقیق ترجمه کن. در ترجمه به موارد زیر توجه کن:

1. استفاده از اصطلاحات و واژگان تخصصی دقیق در حوزه پزشکی و علوم زیستی و رعایت استانداردهای علمی پزشکی پذیرفته‌شده.
2. حفظ سبک علمی، دانشگاهی و تخصصی پزشکی متن اصلی بدون تغییر معنا یا ابهام در مفاهیم.
3. اطمینان از صحت ساختار جملات به گونه‌ای که هم از نظر دستوری و هم از نظر مفهومی به بهترین نحو به زبان فارسی منتقل شود.
4. در صورت وجود اصطلاح یا مفهوم دشوار پزشکی، در صورت امکان ارائه معادل تخصصی مربوطه.
5. رعایت تناسب و انسجام متن به گونه‌ای که همخوانی مفهومی و ساختاری حفظ شود.

فقط متن ترجمه شده را بازگردان، بدون هیچ توضیح اضافی:

{text}"""
    
    # Legal domain translation prompt
    LEGAL = """متن زیر را از زبان انگلیسی به زبان فارسی به صورت حرفه‌ای و دقیق ترجمه کن. در ترجمه به موارد زیر توجه کن:

1. استفاده از اصطلاحات و واژگان تخصصی دقیق در حوزه حقوقی و قانونی و رعایت استانداردهای حقوقی پذیرفته‌شده.
2. حفظ سبک رسمی، حقوقی و تخصصی متن اصلی بدون تغییر معنا یا ابهام در مفاهیم قانونی.
3. اطمینان از صحت ساختار جملات به گونه‌ای که هم از نظر دستوری و هم از نظر مفهومی به بهترین نحو به زبان فارسی منتقل شود.
4. در صورت وجود اصطلاح یا مفهوم دشوار حقوقی، در صورت امکان ارائه معادل تخصصی مربوطه.
5. رعایت تناسب و انسجام متن به گونه‌ای که همخوانی مفهومی و ساختاری حفظ شود.

فقط متن ترجمه شده را بازگردان، بدون هیچ توضیح اضافی:

{text}"""
    
    # Technical domain translation prompt
    TECHNICAL = """متن زیر را از زبان انگلیسی به زبان فارسی به صورت حرفه‌ای و دقیق ترجمه کن. در ترجمه به موارد زیر توجه کن:

1. استفاده از اصطلاحات و واژگان تخصصی دقیق در حوزه فنی و مهندسی و رعایت استانداردهای فنی پذیرفته‌شده.
2. حفظ سبک فنی و تخصصی متن اصلی بدون تغییر معنا یا ابهام در مفاهیم مهندسی.
3. اطمینان از صحت ساختار جملات به گونه‌ای که هم از نظر دستوری و هم از نظر مفهومی به بهترین نحو به زبان فارسی منتقل شود.
4. در صورت وجود اصطلاح یا مفهوم دشوار فنی، در صورت امکان ارائه معادل تخصصی مربوطه.
5. رعایت تناسب و انسجام متن به گونه‌ای که همخوانی مفهومی و ساختاری حفظ شود.

فقط متن ترجمه شده را بازگردان، بدون هیچ توضیح اضافی:

{text}"""
    
    @classmethod
    def get_templates(cls) -> Dict[str, str]:
        """
        Get all prompt templates as a dictionary.
        
        Returns:
            Dictionary of prompt templates by domain
        """
        return {
            Constants.DOMAIN_GENERAL: cls.GENERAL,
            Constants.DOMAIN_SCIENTIFIC: cls.SCIENTIFIC,
            Constants.DOMAIN_GENETIC: cls.GENETIC,
            Constants.DOMAIN_MEDICAL: cls.MEDICAL,
            Constants.DOMAIN_LEGAL: cls.LEGAL,
            Constants.DOMAIN_TECHNICAL: cls.TECHNICAL
        }
    
    @classmethod
    def get_template(cls, domain: str) -> str:
        """
        Get a specific prompt template for the given domain.
        
        Args:
            domain: Translation domain
            
        Returns:
            Prompt template string
        """
        templates = cls.get_templates()
        return templates.get(domain, cls.GENERAL) 