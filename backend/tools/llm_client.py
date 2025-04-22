# File: backend/tools/llm_client.py

import os
import requests
from dotenv import load_dotenv
from backend.tools.text_preprocessing import preprocess_text
from concurrent.futures import ThreadPoolExecutor
from typing import List
import tiktoken

load_dotenv()


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def create_deepseek_request(messages, model="deepseek/deepseek-chat-v3-0324:free", temperature=0.3):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "tradingai-news-summarizer",
        "X-Title": "TradingAI Summarizer",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
    )

    if response.status_code != 200:
        raise Exception(f"OpenRouter API Error: {response.status_code} {response.text}")

    result = response.json()
    return result["choices"][0]["message"]["content"]


def summarize_single_chunk(chunk_text):
    prompt = f"""
        You are a senior equity analyst at a hedge fund. Your job is to summarize the following financial news content for internal investment discussions.

        Please extract key *market-relevant* points, including:
        - Key financial numbers and their trends
        - Expected vs actual performance
        - Forward guidance or management outlook
        - Political, regulatory, or macroeconomic implications
        - Possible market reaction or risk factors

        Avoid generic summaries and focus on what *matters to investors*.

        Raw Content:
        {chunk_text}
        """
    messages = [
        {"role": "system", "content": "You are a professional stock market analyst."},
        {"role": "user", "content": prompt}
    ]
    return create_deepseek_request(messages)


def summarize_content_with_deepseek(content: str, max_tokens: int = 3000, max_workers: int = 4) -> str:
    print(f"🧮 Original content length: {len(content)} characters")

    # Step 1: preprocess text
    chunks = preprocess_text(content, max_tokens=max_tokens, token_based=True)
    print(f"🧩 Split into {len(chunks)} token-aware chunks.")

    # Step 2: parallel chunk summarization
    mini_summaries = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(summarize_single_chunk, chunks)
        for idx, summary in enumerate(results):
            print(f"✅ Finished chunk {idx+1}/{len(chunks)}")
            mini_summaries.append(summary)

    # Step 3: final summary synthesis
    combined_text = "\n\n".join(mini_summaries)
    final_prompt = f"""
        You are a portfolio strategist. Based on the following key points extracted from news,
        summarize the net investor takeaways in 5 points. Focus on possible market impact,
        sector rotation, sentiment shift, and high-level strategic risks.

        Raw summarized chunks:
        {combined_text}
        """
    final_messages = [
        {"role": "system", "content": "You are a professional stock market analyst."},
        {"role": "user", "content": final_prompt}
    ]

    final_summary = create_deepseek_request(final_messages)
    return final_summary


def summarize_multiple_articles(article_list: List[str]) -> List[dict]:
    print(f"📚 Summarizing {len(article_list)} articles...")
    results = []
    for idx, article in enumerate(article_list):
        print(f"\n🔖 Article {idx+1}:")
        summary = summarize_content_with_deepseek(article)
        results.append({
            "index": idx + 1,
            "summary": summary
        })
    return results
