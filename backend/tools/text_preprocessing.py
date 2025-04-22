# File: backend/tools/text_preprocessor.py

import re
import tiktoken

def clean_text(text: str) -> str:
    """
    基础清理文本：
    - 移除多余空格
    - 合并多余换行
    - 去除首尾空白
    """
    text = re.sub(r'\n{3,}', '\n\n', text)  # 三个以上连续换行变两个
    text = re.sub(r'\s+', ' ', text)         # 多空格合并成一个
    text = text.strip()
    return text

def split_into_paragraphs(text: str) -> list:
    """
    按自然段落（双换行）切分文本
    """
    paragraphs = text.split('\n\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]  # 移除空段
    return paragraphs

def group_paragraphs_by_chars(paragraphs: list, max_chars: int = 4000) -> list:
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_chars:
            current_chunk += para + "\n\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def group_paragraphs_by_tokens(paragraphs: list, max_tokens: int = 3000, model: str = "gpt-3.5-turbo") -> list:
    enc = tiktoken.encoding_for_model(model)

    chunks = []
    current_chunk = ""
    current_tokens = 0

    for para in paragraphs:
        tokens = len(enc.encode(para))
        if current_tokens + tokens <= max_tokens:
            current_chunk += para + "\n\n"
            current_tokens += tokens
        else:
            chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
            current_tokens = tokens

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def preprocess_text(text: str, max_chars: int = 4000, max_tokens: int = 3000, token_based: bool = False) -> list:
    """
    综合处理：清理 -> 切段 -> 分组
    返回：分好的chunks列表
    """
    cleaned_text = clean_text(text)
    paragraphs = split_into_paragraphs(cleaned_text)
    if token_based:
        return group_paragraphs_by_tokens(paragraphs, max_tokens=max_tokens)
    else:
        return group_paragraphs_by_chars(paragraphs, max_chars=max_chars)
