import io
import logging
import sys
from flask import Flask, request,  Response
from flask_cors import CORS
from utils.search_web import Search
from utils.response import generate, search_generate
from utils.crawl_web import Crawl
from utils.rrf import Retrieval
import json
import time
from flask import stream_with_context


# 规定编码方式
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gb18030')  # 改变标准输出的编码方式，防止乱码出错导致搜索失败
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')

    @stream_with_context
    def generate_step(query):
        # 加载配置文件
        with open(r'./config/config.json', encoding='utf-8') as f:
            config = json.load(f)

        debug = config['debug']['value']
        app.logger.debug(f'debug:{debug}')
        if debug:
            app.logger.warning('Warning: 当前是debug模式，请将配置文件中的debug设置为false')
            yield "Error:please modify the debug value"
            return 0

        start_time = time.time()

        yield f"正在判断该问题是否需要搜索"
        search_engine = Search()
        search_result, grade, key_words = search_engine.search(query)

        if search_result:
            yield f"该问题需要搜索，搜索关键词：{key_words}"
        else:
            yield "该问题不需要搜索，准备回答..."
            yield from generate(query)
            return

        yield "爬取网页内容中，请耐心等待..."
        crawl = Crawl()
        web_pages = crawl.crawl(search_result)
        print(f"爬取网页条数{len(web_pages)}")
        yield f"网页爬取完成，共爬取 {len(web_pages)} 条网页"

        # grade=1表示问题较简单，不需要全部的网页，前5个就足够了
        if grade == 1:
            if len(web_pages) > 5:
                web_pages = web_pages[:5]

        yield f"文本召回中，马上就要完成了，冲鸭！"
        queries = [query, key_words]
        retrieval = Retrieval()
        retrieve_results = retrieval.retrieve(web_pages, queries)
        yield f"召回完成，共找到 {len(retrieve_results)} 条相关结果"

        end_time = time.time()
        yield f"整个过程用时: {end_time - start_time:.2f} 秒"

        yield "终于结束了，累鼠我了，答案为主人呈上..."
        yield from search_generate(query, retrieve_results)

    return Response(generate_step(query), content_type='text/plain')


if __name__ == '__main__':
    app.run(host='localhost', port=5000,debug=False)
