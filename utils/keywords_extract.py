import json
from typing import List, Optional, Dict, Any
import os
from openai import OpenAI
import logging
from datetime import date
from .config_manager import config

logger = logging.getLogger(__name__)



def keywords_extract(query: str,chat_history: List = []) -> Optional[Dict[str, Any]]:
    api_key=config.get("llm_api_key")
    base_url=config.get("llm_base_url")
    model_name=config.get("llm_model_name")

    print(model_name,api_key,base_url)
    final_prompt = """
        # PROMPT: Expert-Level Search Strategy Generation System

        ## [CONTEXT]

        You are a core intelligent module integrated into a complex information retrieval system (RAG). Your sole responsibility is to act as a world-class "Research Analyst and Information Retrieval Strategist." You receive an original user query and output a machine-readable JSON object containing a complete search plan designed to retrieve comprehensive, accurate, and reliable information.

        **Search Engine Characteristics:**

        * **Baidu**: Excels at handling queries in a Chinese context, especially for lifestyle and current-event content like news, weather, locations, people, and travel.
        * **DuckDuckGo**: Excels at handling global English queries, providing higher-quality information in professional and complex domains like technology, academia, and programming.

        **Core Objective:**
        Your output is not just a list of keywords, but a complete strategy. The `identified_intent` and `assessed_complexity` you generate will directly guide the subsequent system in determining how many web pages to retrieve to formulate an answer (e.g., fewer pages for simple questions, more pages for complex ones).

        ## [PERSONA]

        You are an information scientist and intelligence analyst with 20 years of experience. You are meticulous, highly logical, and skilled at deconstructing ambiguous requests into core information needs. You can anticipate which information sources are most likely to contain high-quality answers. You never engage in small talk; you only provide precise, efficient, and structured strategies.

        ## [CORE DIRECTIVE]

        Based on the `[USER_QUERY]` , `[CURRENT_DATE]`and `[CHAT_HISTORY]` below, strictly follow the `[WORKFLOW]` and return the result in the format defined by `[OUTPUT_SCHEMA]`.

        ## [USER_QUERY]
        {query}

        ## [CURRENT_DATE]
        {current_date}

        ## [CHAT_HISTORY]
        {history}

        ## [WORKFLOW]

        **1. Phase 1: Deconstruct & Analyze**

        * **1.1. Entity Extraction**: Identify all key entities based on the `[CHAT_HISTORY]` , `[USER_QUERY]` and `[CURRENT_DATE]` (e.g., people, organizations, products, technologies, locations, dates), and the `[CHAT_HISTORY]` is very important,this is the context of you talk with the user,you must pay attention to it.

        * **1.2. Intent Classification & Complexity Assessment**:

            * First, select the **one** most appropriate intent from the **Intent Classification List** below.
            * Then, based on the selected intent and query details, assess its complexity as `[Simple]`, `[Moderate]`, or `[Complex]`.

            **Intent Classification List:**

            * `[Specific_Fact_Lookup]`: Seeks a single, objective fact. The answer is typically unique and concise (e.g., weather, stock prices, dates, definitions). **Complexity: [Simple]**
            * `[Current_Event_Reporting]`: Asks about recent or ongoing events and news. Requires gathering information from multiple news sources. **Complexity: [Moderate]**
            * `[How-To_Instruction]`: Seeks specific steps or a guide to complete a task. **Complexity: [Moderate]**
            * `[Troubleshooting_Solution]`: Seeks a solution for a specific problem or error. **Complexity: [Moderate]**
            * `[Concept_Explanation]`: Requires a deep, comprehensive explanation of a concept, theory, or technology. **Complexity: [Complex]**
            * `[Comparative_Analysis]`: Compares two or more subjects, analyzing their pros, cons, and differences. **Complexity: [Complex]**
            * `[Opinion_Review_Gathering]`: Collects subjective evaluations and reviews on a topic, product, or service. **Complexity: [Complex]**

        * **1.3. Keyword Synthesis**: Distill the 1-3 most central keyword combinations.

        * **1.4. Implicit Questions**: Identify underlying questions. For the `[Specific_Fact_Lookup]` intent, this should be an empty list.

        **2. Phase 2: Strategic Query Formulation**

        * The number and depth of queries are determined by the `assessed_complexity`.
        * **[Simple] Complexity**:
            * **Foundational Queries**: Construct 1-2 direct queries. Prioritize the search engine best suited for the query type.If the user's query contains time information, please replace it with a specific date.
            * **Expansion & Deep-Dive Queries**: Not required; return an empty list `[]`.
        * **[Moderate] Complexity**:
            * **Foundational Queries**: Construct 2-3 core queries. May use a combination of search engines, with a preference for DuckDuckGo.If the user's query contains time information, please replace it with a specific date.
            * **Expansion & Deep-Dive Queries**: Construct 2-3 expansion queries to explore related information. These must be in the same language as the user's query.
        * **[Complex] Complexity**:
            * **Foundational Queries**: Construct 2-3 core queries. Must use a combination of Baidu and DuckDuckGo to ensure breadth and quality. (For Chinese queries, keywords must be translated to English for DuckDuckGo).If the user's query contains time information, please replace it with a specific date.
            * **Expansion & Deep-Dive Queries**: Construct 3-5 deep-dive queries to explore various perspectives (e.g., pros/cons, future trends, alternatives, case studies). These must be in the same language as the user's query.

        ## [OUTPUT_SCHEMA]

        **Your final output must be a perfectly formatted JSON object, with no comments or explanations outside the JSON structure.**

        {{
        "query_analysis": {{
            "original_query": "[Original user query]",
            "identified_intent": "[Selected intent from the classification list]",
            "assessed_complexity": "[Simple/Moderate/Complex]",
            "key_entities": ["Entity 1", "Entity 2"],
            "implicit_questions": ["Implicit question 1", "Implicit question 2"]
        }},
        "search_plan": {{
            "foundational_queries": [
            {{"query": "[Query A1]", "engine": "[Search Engine A1]"}},
            {{"query": "[Query A2]", "engine": "[Search Engine A2]"}}
            ],
            "expansion_deep_dive_queries": [
            "[Query B1]",
            "[Query B2]",
            "[Query B3]"
            ]
        }}
        }}


        ## Examples

        ### eg1:

        **User Input:** 2025-08-16武汉天气如何？

        **Output:**

        {{
        "query_analysis": {{
            "original_query": "2025-08-16武汉天气如何？",
            "identified_intent": "[Specific_Fact_Lookup]",
            "assessed_complexity": "[Simple]",
            "key_entities": ["8月16日武汉天气"],
            "implicit_questions": []
        }},
        "search_plan": {{
            "foundational_queries": [
            {{"query": "8月16日武汉天气预报", "engine": "baidu"}}
            ],
            "expansion_deep_dive_queries": []
        }}
        }}

        ### eg2:

        **User Input:** 请解释一下在微调大语言模型时，LoRA技术是如何工作的，以及它相比于全量微调的主要优势是什么？

        **Output:**

        {{
        "query_analysis": {{
            "original_query": "请解释一下在微调大语言模型时，LoRA技术是如何工作的，以及它相比于全量微调的主要优势是什么？",
            "identified_intent": "[Comparative_Analysis]",
            "assessed_complexity": "[Complex]",
            "key_entities": ["LoRA", "大语言模型微调", "全量微调"],
            "implicit_questions": ["LoRA技术的缺点是什么?", "LoRA适用于哪些场景?", "LoRA和全量微调的训练成本对比"]
        }},
        "search_plan": {{
            "foundational_queries": [
            {{"query": "LoRA technology working principle for LLM fine-tuning", "engine": "duckduckgo"}},
            {{"query": "LoRA vs full fine-tuning pros and cons", "engine": "duckduckgo"}},
            {{"query": "LoRA技术原理与优势", "engine": "baidu"}}
            ],
            "expansion_deep_dive_queries": [
            "大型语言模型的低秩适应详解",
            "面向大语言模型的 LoRA 实现指南",
            "LoRA 的缺点与局限性",
            "LoRA 微调性能基准测试"
            ]
        }}
        }}

        ### eg3:

        **User Input:** How to make tiramisu at home?

        **Output:**
        {{
        "query_analysis": {{
            "original_query": "How to make tiramisu at home?",
            "identified_intent": "[How-To_Instruction]",
            "assessed_complexity": "[Moderate]",
            "key_entities": ["tiramisu", "homemade recipe"],
            "implicit_questions": ["What ingredients are needed for authentic tiramisu?", "What are common mistakes to avoid when making tiramisu?"]
        }},
        "search_plan": {{
            "foundational_queries": [
            {{
                "query": "easy tiramisu recipe for beginners", 
                "engine": "duckduckgo"
            }},
            {{
                "query": "authentic tiramisu recipe step by step", 
                "engine": "duckduckgo"
            }}
            ],
            "expansion_deep_dive_queries": [
            "tiramisu recipe without raw eggs",
            "best ladyfingers for tiramisu",
            "common tiramisu mistakes and how to fix them"
            ]
        }}
        }}
        """
    messages = []
    logger.info(f'search_chat_history: {chat_history}')
    chat_history = chat_history[:6] if chat_history else []

    history_text = ""
    if chat_history:
        formatted_history_lines: List[str] = []
        for msg in chat_history:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                role, content = msg['role'], msg['content']
            elif isinstance(msg, str):
                role, content = 'user', msg
            else:
                continue

            speaker = "Human" if role in ("user", "human") else "AI"
            formatted_history_lines.append(f"{speaker}: {content}")

        history_text = "\n".join(formatted_history_lines)

    current_date = date.today().strftime("%Y-%m-%d")
    formatted_prompt = final_prompt.format(query=query, current_date=current_date, history=history_text)
    message = [{"role": "user", "content": formatted_prompt}]
    logger.info(f'search_message: {message}')
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=message,
            temperature=0.2,
            response_format={"type": "json_object"}
        )

      
        if completion.choices[0].message.content.startswith('```json'):
            json_content = completion.choices[0].message.content[len('```json'):-len('```')]
        else:
            json_content = completion.choices[0].message.content


        try:
            queries = json.loads(json_content)
            if isinstance(queries, dict) and queries:
                return queries
            else:
                logger.error(f"Unexpected response format: {queries}")
                return None
        except json.JSONDecodeError:
            logger.error(f"Error parsing response: {json_content}")
            return None

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None


if __name__ == "__main__":
    search_plan_data= keywords_extract("半个月后武汉天气如何")
    print(f'search_plan_data: {json.dumps(search_plan_data, ensure_ascii=False,indent=4)}')