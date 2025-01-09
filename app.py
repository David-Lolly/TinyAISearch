import streamlit as st
import requests
import json
from datetime import datetime


# 更新的CSS样式
st.markdown("""
<style>
    /* 主容器样式 */
    .main {
        padding: 0;
        max-width: 1200px;
        margin: 0 auto;
        padding-bottom: 100px;
    }
    /* 消息容器样式 */
    .chat-container {
        backgroud-color:#8ed5b5
        max-height: calc(100vh - 180px);
        overflow-y: auto;
        padding: 2rem;
        # margin-bottom: 120px;
        scroll-behavior: smooth;
        transition: all 0.3s ease;
    }

    /* 基础输入框容器样式 */
    div[data-testid="stForm"] {
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 800px;  /* 默认宽度 */
        max-width: 90%;
        background-color: #f8f9fa;
        padding: 1rem;
        z-index: 999;
        border-top: 1px solid #e0e0e0;
        box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }

    /* 输入框样式 */
    .stTextInput > div > div > input {
        width: 100%;
        padding: 12px 45px 12px 15px;
        border-radius: 5px;
        font-size: 16px;
        background-color: white;
        transition: all 0.3s ease;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* 打字机效果的光标 */
    .typing-cursor {
        display: inline-block;
        width: 2px;
        height: 15px;
        background-color: #000;
        animation: blink 1s infinite;
        margin-left: 2px;
        vertical-align: middle;
    }

    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }

    /* 进度条加载动画 */
    .progress-bar {
        width: 100%;
        height: 2px;
        background-color: #f3f3f3;
        position: relative;
        overflow: hidden;
        margin: 10px 0;
    }

    .progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 20%;
        height: 100%;
        background-color: #2d7bf4;
        animation: progress 1s infinite linear;
    }

    @keyframes progress {
        0% { left: -20%; }
        100% { left: 100%; }
    }

    /* 时间戳和状态标签 */
    .message-metadata {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        color: #666;
        margin-bottom: 5px;
    }
    
    .input-metadata {
        display: flex;
        justify-content: space-between;
        align-items: center;
        # font-size: 18px;
        font-weight: 400;
        text-size-adjust: 100%;
        color: black;
        margin-bottom: 5px;
    }
    
    .status-label {
        display: flex;
        align-items: center;
        gap: 5px;
    }

    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #2d7bf4;
    }

    /* 标题容器样式 */
    .title-container {
        text-align: center;
        margin-bottom: 30px;
    }

    .caption {
        color: #666;
        margin-top: 0;
    }

    @media (max-width: 768px) {
        div[data-testid="stForm"],
        body.sidebar-collapsed div[data-testid="stForm"],
        body:not(.sidebar-collapsed) div[data-testid="stForm"] {
            width: 95%;
            left: 50%;
            padding: 0.5rem;
        }
    }
</style>

""", unsafe_allow_html=True)

custom_css = """
<style>
    .stButton > button {
        background-color: #000000;
        color: white;
        border: none;
        padding: 8px 16px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #333333;
        color: #ffffff;
        transform: translateY(-2px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    .stButton > button:active {
        transform: translateY(0px);
    }
</style>
"""

# 注入自定义CSS
st.markdown(custom_css, unsafe_allow_html=True)

st.markdown("""
    <style>
    /* 修改按钮的背景颜色和文字颜色 */
    div.stButton > button:first-child {
        background-color: black;
        color: white;
    }
    /* 修改按钮在鼠标悬停时的背景颜色 */
    div.stButton > button:first-child:hover {
        background-color: gray;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
    /* 步骤信息样式 */
    .search-step {
        background-color: #f4f4f4;
        border-left: 4px solid #2d7bf4;
        padding: 10px;
        margin: 10px 0;
        font-size: 14px;
        color: #333;
        animation: fadeInStep 0.5s ease;
    }

    @keyframes fadeInStep {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .search-step-icon {
        margin-right: 10px;
        display: inline-block;
    }

    .search-step-text {
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

def search_llm(query):
    data = {'query': query}
    headers = {'Content-Type': 'application/json'}
    url = "http://localhost:5000/search"

    try:
        with st.chat_message("assistant"):
            # 创建消息占位符
            message_placeholder = st.empty()
            final_steps_display = st.empty()

            # 显示思考中状态
            message_placeholder.markdown("""
                <div class="message-metadata">
                    <div class="status-label">
                        <div class="status-dot"></div>
                        正在处理您的搜索请求...
                    </div>
                </div>
                <div class="progress-bar"></div>
            """, unsafe_allow_html=True)

            response = requests.post(url, json=data, headers=headers, stream=True, timeout=60)

            if response.status_code == 200:
                full_response = ""
                steps = []
                content_info = ''
                for chunk in response.iter_content(chunk_size=2048):
                    if chunk:
                        try:
                            decoded_chunk = chunk.decode('utf-8')
                            if len(steps)<9 and "该问题不需要搜索，准备回答..." not in steps and "Error:" not in decoded_chunk:

                                if "正在判断该问题是否需要搜索" in decoded_chunk:
                                    final_steps_display.markdown(f"""
                                        <div class="search-step">
                                            <span class="search-step-icon">🤔</span>
                                            <span class="search-step-text">{decoded_chunk}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    steps.append(decoded_chunk)

                                elif "该问题不需要搜索，准备回答" in decoded_chunk:
                                    final_steps_display.markdown(f"""
                                        <div class="search-step">
                                            <span class="search-step-icon">🎉</span>
                                            <span class="search-step-text">{decoded_chunk}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    steps.append(decoded_chunk)

                                elif "该问题需要搜索，搜索关键词" in decoded_chunk:
                                    final_steps_display.markdown(f"""
                                        <div class="search-step">
                                            <span class="search-step-icon">🔍</span>
                                            <span class="search-step-text">{decoded_chunk}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    steps.append(decoded_chunk)

                                    # 类似地为其他步骤添加图标
                                elif "爬取网页内容中" in decoded_chunk:
                                    final_steps_display.markdown(f"""
                                        <div class="search-step">
                                            <span class="search-step-icon">🌐</span>
                                            <span class="search-step-text">{decoded_chunk}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    steps.append(decoded_chunk)

                                elif "网页爬取完成" in decoded_chunk:
                                    final_steps_display.markdown(f"""
                                        <div class="search-step">
                                            <span class="search-step-icon">💡</span>
                                            <span class="search-step-text">{decoded_chunk}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    steps.append(decoded_chunk)

                                elif "文本召回中，马上就要完成了，冲鸭！" in decoded_chunk:
                                    final_steps_display.markdown(f"""
                                        <div class="search-step">
                                            <span class="search-step-icon">🔥</span>
                                            <span class="search-step-text">{decoded_chunk}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    steps.append(decoded_chunk)

                                elif "召回完成，共找到" in decoded_chunk:
                                    final_steps_display.markdown(f"""
                                        <div class="search-step">
                                            <span class="search-step-icon">✅</span>
                                            <span class="search-step-text">{decoded_chunk}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    steps.append(decoded_chunk)
                                elif "整个过程用时:" in decoded_chunk:
                                    final_steps_display.markdown(f"""
                                        <div class="search-step">
                                            <span class="search-step-icon">⏱️</span>
                                            <span class="search-step-text">{decoded_chunk}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    steps.append(decoded_chunk)

                                elif "终于结束了，累鼠我了，答案为主人呈上" in decoded_chunk:
                                    final_steps_display.markdown(f"""
                                        <div class="search-step">
                                            <span class="search-step-icon">🎉</span>
                                            <span class="search-step-text">{decoded_chunk}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    steps.append(decoded_chunk)
                                elif "参考信息：" in decoded_chunk and not content_info:
                                    # content_info = list(decoded_chunk[5:])
                                    json_data = decoded_chunk.split("参考信息：", 1)[1]

                                    # 解析 JSON 数据
                                    content_info = json.loads(json_data)
                                    print(f'json:{content_info}')
                                    # 输出解析后的参考信息
                                    for item in content_info:
                                        for title, url in item.items():
                                            print(f"标题: {title}, 链接: {url}")

                                    print(f'content_info:{content_info}')
                                    steps.append(content_info)

                            else:
                                # 累积最终响应文本
                                final_steps_display.empty()
                                full_response += decoded_chunk
                                timestamp = datetime.now().strftime("%H:%M")

                                # 更新消息内容，包含打字机光标
                                message_placeholder.markdown(
                                    f"""
                                    <div class="message-metadata">
                                        <span class="timestamp">{timestamp}</span>
                                        <div class="status-label">
                                            <div class="status-dot"></div>
                                            正在生成回答...
                                        </div>
                                    </div>
                                    {full_response}<span class="typing-cursor"></span>
                                    """,
                                    unsafe_allow_html=True
                                )
                        except json.JSONDecodeError as e:
                            st.error(f"JSON 解码错误: {e}")
                            return

                # 最终消息，移除打字机光标
                timestamp = datetime.now().strftime("%H:%M")
                reference_html = ''
                if content_info:
                    reference_html = "<br>**参考信息**：<ul>"
                    for item in content_info:
                        print(f'item:{item}')
                        for title, url in item.items():
                            reference_html += f'<li><a href="{url}" target="_blank">{title}</a></li>'
                    reference_html += "</ul><br>"

                message_placeholder.markdown(
                    f"""
                    <div class="message-metadata">
                        <span class="timestamp">{timestamp}</span>
                        <div class="status-label">完成</div>
                    </div>
                    {full_response+'<br>'}
                    {reference_html}
                    """,
                    unsafe_allow_html=True
                )
                print(full_response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response+'<br>'+reference_html,
                    "timestamp": timestamp
                })
    except Exception as e:
        st.error(f"搜索过程发生错误: {str(e)}")

def search_web():
    st.title("🔍 TinyAISearch")
    st.caption("🚀 用AI进行网络搜索")

    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": 'What Can I Search For You?',
        }]
    if "input_key" not in st.session_state:
        st.session_state.input_key = 0

    # 创建聊天历史显示区域
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in st.session_state.messages:
            timestamp = message.get("timestamp", datetime.now().strftime("%H:%M"))
            if message['role'] == 'user':
                with st.chat_message(message["role"]):
                    st.markdown(
                        message['content'],
                    )
            else:
                with st.chat_message(message["role"]):
                    st.markdown(
                        f"""
                        <div class="message-metadata">
                            <span class="timestamp">{timestamp}</span>
                        </div>
                        {message['content']}
                        """,
                        unsafe_allow_html=True
                    )

    # 使用表单确保输入框固定在底部
    with st.form(key=f"chat_form_{st.session_state.input_key}", clear_on_submit=True):
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            user_input = st.text_input(
                '输入你的问题',
                key=f"user_input_{st.session_state.input_key}",
                placeholder="在这里输入你的问题，按Enter发送...",
                label_visibility="collapsed"
            )
            with col2:
                submitted = st.form_submit_button("发送" )
    if user_input:
        timestamp = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })

    if submitted and user_input:
        with st.chat_message('user'):
            st.markdown(
                user_input,
            )

        search_llm(user_input)


def main():
    search_web()

if __name__ == '__main__':
    main()