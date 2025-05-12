import os
import json
import requests
import base64
import tiktoken
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils.common import windows_compatible_name




def google_search(query, num_results=10, site_url=None):
    
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_id = os.getenv("CSE_ID")
    
    url = "https://www.googleapis.com/customsearch/v1"

    # API 请求参数
    if site_url == None:
        params = {
        'q': query,          
        'key': api_key,      
        'cx': cse_id,        
        'num': num_results   
        }
    else:
        params = {
        'q': query,         
        'key': api_key,      
        'cx': cse_id,        
        'num': num_results,  
        'siteSearch': site_url
        }

    # 发送请求
    response = requests.get(url, params=params)
    response.raise_for_status()

    # 解析响应
    search_results = response.json().get('items', [])

    # 提取所需信息
    results = [{
        'title': item['title'],
        'link': item['link'],
        'snippet': item['snippet']
    } for item in search_results]

    return results


def get_search_text(q, url):

    # 启动 WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    # 打开网页
    driver.get(url)

    # 等待页面加载完成
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
    except Exception as e:
        print("页面加载超时:", e)

    # 获取网页的 HTML 内容
    html_content = driver.page_source

    # 使用 BeautifulSoup 解析 HTML 内容
    soup = BeautifulSoup(html_content, 'html.parser')

    # 获取 title 标签的内容
    title = soup.title.string
    print("网页标题:", title)
    
    # 提取所有文本内容
    text = soup.get_text()
    #print("网页的所有文本内容:")
    #print(text)

    # 关闭 WebDriver
    driver.quit()

    if title == None:
        return None
    
    else:
        title = windows_compatible_name(title)

        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")     
        json_data = [
            {
                "link": url,
                "title": title,
                "content": text,
                "tokens": len(encoding.encode(text))
            }
        ]
        
        # 自动创建目录，如果不存在的话
        dir_path = f'./auto_search/{q}'
        os.makedirs(dir_path, exist_ok=True)
    
        with open('./auto_search/%s/%s.json' % (q, title), 'w') as f:
            json.dump(json_data, f)

        return title




def get_github_readme(dic):
    
    github_token = os.getenv('GITHUB_TOKEN')
    user_agent = os.getenv('search_user_agent')
    
    owner = dic['owner']
    repo = dic['repo']

    headers = {
        "Authorization": github_token,
        "User-Agent": user_agent
    }

    response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/readme", headers=headers)

    readme_data = response.json()
    encoded_content = readme_data.get('content', '')
    decoded_content = base64.b64decode(encoded_content).decode('utf-8')
    
    return decoded_content


def extract_github_repos(search_results):
    # 使用列表推导式筛选出项目主页链接
    repo_links = [result['link'] for result in search_results if '/issues/' not in result['link'] and '/blob/' not in result['link'] and 'github.com' in result['link'] and len(result['link'].split('/')) == 5]

    # 从筛选后的链接中提取owner和repo
    repos_info = [{'owner': link.split('/')[3], 'repo': link.split('/')[4]} for link in repo_links]

    return repos_info


def get_search_text_github(q, dic):
    
    title = dic['owner'] + '_' + dic['repo']
    title = windows_compatible_name(title)

    # 创建问题答案正文
    text = get_github_readme(dic)

    # 写入本地json文件
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")     
    json_data = [
        {
            "title": title,
            "content": text,
            "tokens": len(encoding.encode(text))
        }
    ]
    
    # 自动创建目录，如果不存在的话
    dir_path = f'./auto_search/{q}'
    os.makedirs(dir_path, exist_ok=True)
    
    with open('./auto_search/%s/%s.json' % (q, title), 'w') as f:
        json.dump(json_data, f)

    return title