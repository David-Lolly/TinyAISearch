# 🔍 TinyAISearch

TinyAISearch is a lightweight AI search project designed for large language model enthusiasts. It encompasses a complete workflow including keyword rewriting, web crawling, content retrieval, and streaming response display. The RAG (Retrieval-Augmented Generation) module integrates multiple retrieval strategies (similarity-based retrieval, BM25 reranking, multi-question retrieval, etc.), allowing users to flexibly choose and understand the pros and cons of different approaches. The project supports various mainstream large language models (such as Qwen, GLM, DeepSeek, OpenAI, etc.) and local Ollama models. The code includes detailed comments, making it easy to learn and customize. It's particularly suitable for beginners to quickly get started with AI application development, master large model RAG technology, and modify the project to explore more possibilities. We hope you enjoy learning and experimenting with it! Have fun! 😘

Chat Example:

<img src="./images/img.png" width="600" />

---
### 📖 Getting Started Guide

The following guide will help you install and run the project on your local machine for local conversations.

###### 🔧 Prerequisites

1. Install Anaconda or Miniconda
2. Python 3.10 virtual environment

###### 🛠️ Installation Steps

1. Clone the repository
```sh
git clone https://github.com/David-Lolly/TinyAISearch.git
cd TinyAISearch
```

2. Install dependencies
```sh
conda create -n TinyAISearch python=3.10
conda activate TinyAISearch 
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
# Using conda to install faiss as pip installation can be problematic
conda install faiss 
# Complete the initialization steps for crawl4ai package
crawl4ai-setup 
# Verify successful installation
crawl4ai-doctor 
```

---

### 🚀 Quick Start

1. 📝 Fill in the config.json file. It supports all large language models with OpenAI-compatible interfaces (Qwen, GLM, DeepSeek, etc.). I use the Embedding and Rerank models from [Silicon Flow](https://cloud.siliconflow.cn/account/ak) (free 🤩). Here's an example:

Below is an example using the DeepSeek model. You just need to fill in the API key obtained from [DeepSeek](https://platform.deepseek.com/api_keys) in the corresponding location, and the API key from [Silicon Flow](https://cloud.siliconflow.cn/account/ak) in the cloud_embedding and cloud_rerank sections.

```json
{  
  "local_embedding_model": false,  
  "local_rerank_model": false,  
  "LLM": {
    "model_name": "deepseek-chat",  
    "base_url": "https://api.deepseek.com/v1",  
    "api_key": "sk-xxxxx",  
    "description": "Fill in the model name in model_name, the provider's base_url in base_url, and your API key in api_key"
  },  
  "embedding_model": {  
    "local_embedding": {  
      "model_path": "D:\\model\\huggingface_model\\BAAI\\bge_large_zh",  
      "description": "Cloud embedding model is used by default, path can be empty. If local_embedding_model is true, local embedding model will be used. Fill in local embedding model path in model_path"  
    },  
    "cloud_embedding": {  
      "model_name": "BAAI/bge-large-zh-v1.5",  
      "base_url": "https://api.siliconflow.cn/v1/embeddings",  
      "api_key": "sk-xxxxxx",  
      "description": "Fill in embedding model name, provider's base_url, and your API key"  
    }  
  },  
  "rerank_model": {  
    "local_rerank": {  
      "model_path": "D:\\model\\huggingface_model\\Rerank",  
      "description": "Cloud rerank model is used by default, path can be empty. If local_rerank_model is true, local rerank model will be used. Fill in local rerank model path in model_path"  
    },  
    "cloud_rerank": {  
      "model_name": "BAAI/bge-reranker-v2-m3",  
      "base_url": "https://api.siliconflow.cn/v1/rerank",  
      "api_key": "sk-xxxxxx",  
      "description": "Fill in rerank model name, provider's base_url, and your API key"  
    }  
  },  
  "retrieval": {  
    "quality": "high",  
    "method": {  
      "similarity": {  
        "activate": true,  
        "top_k": 10,  
        "description": "Uses similarity+rerank method for retrieval. Set activate to true to use this method. top_k controls the number of retrieved texts"  
      },  
      "rank": {  
        "activate": false,  
        "top_k": 10,  
        "description": "Uses rank+BM25 method for retrieval. Set activate to true to use this method. Only one retrieval method can be selected. top_k controls the number of retrieved texts"  
      }  
    },  
    "description": "quality can be 'high' or 'higher'. 'high' offers balanced quality and speed; 'higher' provides better quality but slower speed. Two retrieval methods available: similarity and rank, controlled by activate value. top_k controls the number of retrieved texts"  
  },  
  "search_engine": {  
    "name": "baidu",  
    "api_key": "",  
    "cse": "",  
    "description": "Choose between baidu, google, and serper. Baidu uses Python library, no API key needed. Google needs both api_key and cse. Serper only needs api_key. Google and serper provide better search results"  
  },  
  "debug": {  
    "value": true,  
    "description": "Set to true for debugging code when encountering errors or making modifications. Run search.py for IDE debugging. Set to false when ready to view results in frontend"  
  }  
}
```

**Notes**:
- Debug mode is for testing purposes. Remember to set it to false when you want to check results in the frontend
- Retrieval quality can be set to 'high' or 'higher'. 'High' balances precision and speed, with **similarity** retrieval using similarity+rerank and **rank** retrieval using rank+BM25 dual-path retrieval. 'Higher' prioritizes precision, using dual-query retrieval (user query and search keywords) with similarity+BM25 for **similarity** retrieval and rank+BM25 for **rank** retrieval.
- **local_embedding_model** and **local_rerank_model** control whether to use local embedding and rerank models. Cloud models are used by default (local models might be faster)
- Google is recommended as the search engine for better results (100 free uses per day 😋)
- For other details, please read the descriptions in the config file

2. 💡 After completing the configuration file, test if it runs properly
```sh
python AISearch.py
```

3. 🔥 After successful testing, set debug to false in the config file and run the following commands
```sh
python AISearch_api.py
# In a new command window, enter:
streamlit run app.py
```

4. ✅ If everything goes well, you should see the following interface

<img src="./images/success.png" width="600" />

Congratulations on successfully running the project! 🎉🎉🎉

---
### 📐 Structure Overview

Higher retrieval diagram:

<img src="./images/multi_query_retrieval.png" width="900" />

File structure:

```
│  app.py  # Frontend chat interface
│  LICENSE.txt
│  README.md
│  README_EN.md
│  requirements.txt
│  search.py # Local debug code to test functionality
│  search_api.py # AI search API for frontend services
│
├─config
│      config.json # Configuration file   
│
├─images
│      img.png
│      multi_query_retrieval.png
│      success.png
│
└─utils
        crawl_web.py # Web crawler
        keywords_extract.py # Extract search keywords from user query
        response.py # Model responses
        retrieval.py # Different retrieval strategies
        rrf.py # Combine different retrieval results using RRF algorithm
        search_web.py # Search related content using search engines
        __init__.py
```

---

### 🧐 How to Develop Further
For those who like to explore, you can build upon this project by modifying prompts, changing retrieval methods, using more advanced language models, and more. Feel free to experiment!

You can:
- Customize search engines in search_web.py
- Implement custom retrieval methods in rrf.py to compare different approaches
- And much more...

---
### License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE.txt) file for details.