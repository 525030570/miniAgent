import os
import json
import tiktoken
from utils.web_search import get_search_text_github, extract_github_repos
from utils.web_search import google_search


def get_answer_github(q, g='globals()'):
    """
    当你无法回答某个问题时，调用该函数，能够获得答案
    :param q: 必选参数，询问的问题，字符串类型对象
    :param g: g，字符串形式变量，表示环境变量，无需设置，保持默认参数即可
    :return：某问题的答案，以字符串形式呈现
    """
    # 调用转化函数，将用户的问题转化为更适合在GitHub上搜索的关键词
    # q = convert_keyword_github(q)
    
    # 默认搜索返回5个答案
    print('正在接入谷歌搜索，查找和问题相关的答案...')
    search_results = google_search(query=q, num_results=5, site_url='https://github.com/')
    results = extract_github_repos(search_results)
    
    # 创建对应问题的子文件夹
    folder_path = './auto_search/%s' % q
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    print('正在读取相关项目说明文档...')
    num_tokens = 0
    content = ''
    
    for dic in results:
        title = get_search_text_github(q, dic)
        with open('./auto_search/%s/%s.json' % (q, title), 'r') as f:
            jd = json.load(f)
        num_tokens += jd[0]['tokens']
        if num_tokens <= 12000:
            content += jd[0]['content']
        else:
            break
    print('正在进行最后的整理...')
    return(content)


get_answer_github_tool = {
    "type": "function",
    "function": {
        "name": "get_answer_github",
        "description": (
            "GitHub联网搜索工具，当用户提出的问题超出你的知识库范畴时，或该问题你不知道答案的时候，请调用该函数来获得问题的答案。该函数会自动从GitHub上搜索得到问题相关文本，而后你可围绕文本内容进行总结，并回答用户提问。需要注意的是，当用户提问点名要求在GitHub进行搜索时，例如“请帮我介绍下GitHub上的Qwen2项目”，此时请调用该函数，其他情况下请调用get_answer外部函数并进行回答。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "一个满足GitHub搜索格式的问题，往往是需要从用户问题中提出一个适合搜索的项目关键词，用字符串形式进行表示。",
                    "example": "DeepSeek-R1"
                },
                "g": {
                    "type": "string",
                    "description": "Global environment variables, default to globals().",
                    "default": "globals()"
                }
            },
            "required": ["q"]
        }
    }
}