"""轻量记忆幻觉检测。

这是启发式日志工具：允许漏报，不拦截回复，不改变用户体验。
"""

from __future__ import annotations

import re


STOP_PHRASES = {
    "我记得",
    "不太清楚",
    "告诉我",
    "更多吗",
    "没关系",
    "慢慢说",
    "我们先",
    "我陪你",
}

LOCATION_SUFFIXES = ("省", "市", "县", "区", "镇", "村", "街", "路", "菜场", "学校", "医院", "公园", "老家")


def _extract_phrases(text: str) -> list[str]:
    """用正则粗略提取人名、地名、时间和事件关键词。"""
    value = str(text or "")
    candidates: list[str] = []

    patterns = [
        r"\d{4}年",
        r"\d{1,2}月\d{1,2}日",
        r"(?:上午|下午|晚上|早上|中午)?\d{1,2}点(?:半|左右)?",
        r"\d{1,2}:\d{2}",
        r"[\u4e00-\u9fff]{2,8}(?:省|市|县|区|镇|村|街|路|菜场|学校|医院|公园|老家|张家界)",
        r"[\u4e00-\u9fff]{2,8}(?:服装厂|工厂|公司|单位|小学|中学|大学)",
        r"(?:女儿|儿子|老伴|丈夫|妻子|妈妈|爸爸|母亲|父亲)[\u4e00-\u9fff]{2,4}",
        r"(?:张|王|李|赵|陈|刘|杨|黄|周|吴|徐|孙|胡|朱|高|林|何|郭|马|罗|梁|宋|郑|谢|韩|唐|冯|于|董|萧|程|曹|袁|邓|许|傅|沈|曾|彭|吕|苏|卢|蒋|蔡|贾|丁|魏|薛|叶|阎|余|潘|杜|戴|夏|钟|汪|田|任|姜|范|方|石|姚|谭|廖|邹|熊|金|陆|郝|孔|白|崔|康|毛|邱|秦|江|史|顾|侯|邵|孟|龙|万|段|雷|钱|汤|尹|黎|易|常|武|乔|贺|赖|龚|文)[\u4e00-\u9fff]{1,3}",
    ]
    for pattern in patterns:
        candidates.extend(re.findall(pattern, value))

    unique: list[str] = []
    for phrase in candidates:
        cleaned = str(phrase or "").strip("，。！？、,.!?；;：:（）() ")
        if len(cleaned) < 2 or cleaned in STOP_PHRASES:
            continue
        if cleaned not in unique:
            unique.append(cleaned)
    return unique


def _phrase_supported(phrase: str, approved_blob: str, approved_phrases: list[str]) -> bool:
    """判断短语是否被已审批记忆支持，允许地点短语带少量前缀。"""
    if phrase in approved_blob:
        return True
    if any(approved_phrase and approved_phrase in phrase for approved_phrase in approved_phrases):
        return True
    for suffix in LOCATION_SUFFIXES:
        if phrase.endswith(suffix) and len(phrase) > len(suffix) + 2:
            tail = phrase[-(len(suffix) + 2):]
            if tail in approved_blob:
                return True
    return False


def check_memory_leak(response_text: str, approved_memory_texts: list[str]) -> dict:
    """检查回复中是否出现未被已审批记忆支持的具体事实短语。"""
    approved_blob = "\n".join(str(item or "") for item in approved_memory_texts)
    approved_phrases = _extract_phrases(approved_blob)
    flagged = [
        phrase
        for phrase in _extract_phrases(response_text)
        if phrase
        and not _phrase_supported(phrase, approved_blob, approved_phrases)
    ]
    return {
        "suspicious": bool(flagged),
        "flagged_phrases": flagged,
    }
