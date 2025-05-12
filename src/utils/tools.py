import os
import json
from IPython.display import display, Markdown
from modules.python_inter import python_inter
from modules.fig_inter import fig_inter
from modules.sql_inter import sql_inter
from modules.extract_data import extract_data
from modules.get_answer import get_answer
from modules.get_answer_github import get_answer_github




def print_code_if_exists(function_args):
    """
    如果存在代码片段，则打印代码
    """
    def convert_to_markdown(code, language):
        return f"```{language}\n{code}\n```"
    
    # 如果是SQL，则按照Markdown中SQL格式打印代码
    if function_args.get('sql_query'):
        code = function_args['sql_query']
        markdown_code = convert_to_markdown(code, 'sql')
        print("即将执行以下代码：")
        display(Markdown(markdown_code))

    # 如果是Python，则按照Markdown中Python格式打印代码
    elif function_args.get('py_code'):
        code = function_args['py_code']
        markdown_code = convert_to_markdown(code, 'python')
        print("即将执行以下代码：")
        display(Markdown(markdown_code))




def create_function_response_messages(messages, response):
    
    """
    调用外部工具，并更新消息列表
    :param messages: 原始消息列表
    :param response: 模型某次包含外部工具调用请求的响应结果
    :return：messages，追加了外部工具运行结果后的消息列表
    """

    available_functions = {
        "python_inter": python_inter,
        "fig_inter": fig_inter,
        "sql_inter": sql_inter,
        "extract_data": extract_data,
        "get_answer": get_answer,
        "get_answer_github": get_answer_github,
    }
    
    # 提取function call messages
    function_call_messages = response.choices[0].message.tool_calls

    # 将function call messages追加到消息列表中
    messages.append(response.choices[0].message.model_dump())

    # 提取本次外部函数调用的每个任务请求
    for function_call_message in function_call_messages:
        
        # 提取外部函数名称
        tool_name = function_call_message.function.name
        # 提取外部函数参数
        tool_args = json.loads(function_call_message.function.arguments)       
        
        # 查找外部函数
        fuction_to_call = available_functions[tool_name]

        # 打印代码
        print_code_if_exists(function_args=tool_args)

        # 运行外部函数
        try:
            tool_args['g'] = globals()
            # 运行外部函数
            function_response = fuction_to_call(**tool_args)
        except Exception as e:
            function_response = "函数运行报错如下:" + str(e)

        # 拼接消息队列
        messages.append(
            {
                "role": "tool",
                "content": function_response,
                "tool_call_id": function_call_message.id,
            }
        )
        
    return messages




def save_markdown_to_file(content: str, filename_hint: str, directory="research_task"):
    # 在当前项目目录下创建 research_task 文件夹
    save_dir = os.path.join(os.getcwd(), directory)

    # 如果目录不存在则创建
    os.makedirs(save_dir, exist_ok=True)

    # 创建文件名（取前8个字符并加上...）
    filename = f"{filename_hint[:8]}....md"

    # 完整文件路径
    file_path = os.path.join(save_dir, filename)

    # 将内容保存为Markdown文档
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

    print(f"文件已成功保存到：{file_path}")