import sys
from utils.search_web import Search
from utils.response import generate,search_generate
from utils.crawl_web import Crawl
from utils.rrf import Retrieval
import json
import time



if __name__ == '__main__':
    # 该文件用于调试代码时使用，你可以直接在运行后看到对应的输出，便于你观察代码运行情况，代码调试完成后你可以运行search_api.py文件，然后到前端查看效果

    # 加载配置文件
    with open(r'./config/config.json',encoding='utf-8') as f:
        config = json.load(f)

    # 是否使用本地大语言模型
    debug = config['debug']['value']
    print(f'debug:{debug}')
    if not debug:
        print('Warning: 当前不是debug模式，请将配置文件中的debug设置为true')
        sys.exit(0)

    start_time = time.time()
    # 输入你的问题
    query='蔡徐坤个人基本信息介绍'

    print(f'------搜索中-----')
    search_engine = Search()
    search_result,grade,key_words=search_engine.search(query)
    if search_result :
        print(f'搜索网页情况：{len(search_result)}')


    # 该问题不需要搜索或者搜索结果为空，直接回答
    if search_result == 0 or len(search_result)==0:
        generate(query)
        sys.exit(0)

    print('-----爬取网页内容-----')
    crawl = Crawl()
    web_pages = crawl.crawl(search_result)
    print(f'web_pages:{web_pages}')
    print(f'爬取网页条数{len(web_pages)}')

    # grade=1表示问题较简单，不需要全部的网页，前5个就足够了，加快处理速度
    if grade == 1:
        if len(web_pages)>5:
            web_pages = web_pages[:5]

    queries = [query, key_words] # 把用户问题和提取出的搜索关键词作为检索的问题，使用多问题召回，提高召回率
    retrieval = Retrieval()
    retrieve_results = retrieval.retrieve(web_pages,queries)

    end_time = time.time()
    print(f'搜索召回用时{end_time-start_time}')
    print('-----回答------')
    search_generate(query,retrieve_results) # 使用云端大模型回答

