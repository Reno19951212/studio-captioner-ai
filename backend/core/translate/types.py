"""Translator type enums"""

from enum import Enum


class TranslatorType(Enum):
    """Translator type"""

    LLM = "llm"


class TargetLanguage(Enum):
    """Target language enum"""

    SIMPLIFIED_CHINESE = "简体中文"
    TRADITIONAL_CHINESE = "繁体中文"
    ENGLISH = "英语"
    ENGLISH_US = "英语(美国)"
    ENGLISH_UK = "英语(英国)"
    JAPANESE = "日本語"
    KOREAN = "韩语"
    CANTONESE = "粤语"
    THAI = "泰语"
    VIETNAMESE = "越南语"
    INDONESIAN = "印尼语"
    MALAY = "马来语"
    TAGALOG = "菲律宾语"
    FRENCH = "法语"
    GERMAN = "德语"
    SPANISH = "西班牙语"
    SPANISH_LATAM = "西班牙语(拉丁美洲)"
    RUSSIAN = "俄语"
    PORTUGUESE = "葡萄牙语"
    PORTUGUESE_BR = "葡萄牙语(巴西)"
    PORTUGUESE_PT = "葡萄牙语(葡萄牙)"
    ITALIAN = "意大利语"
    DUTCH = "荷兰语"
    POLISH = "波兰语"
    TURKISH = "土耳其语"
    GREEK = "希腊语"
    CZECH = "捷克语"
    SWEDISH = "瑞典语"
    DANISH = "丹麦语"
    FINNISH = "芬兰语"
    NORWEGIAN = "挪威语"
    HUNGARIAN = "匈牙利语"
    ROMANIAN = "罗马尼亚语"
    BULGARIAN = "保加利亚语"
    UKRAINIAN = "乌克兰语"
    ARABIC = "阿拉伯语"
    HEBREW = "希伯来语"
    PERSIAN = "波斯语"
