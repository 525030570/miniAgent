from utils.tools import create_function_response_messages
from modules.python_inter import python_inter_tool
from modules.fig_inter import fig_inter_tool
from modules.sql_inter import sql_inter_tool
from modules.extract_data import extract_data_tool
from modules.get_answer import get_answer_tool
from modules.get_answer_github import get_answer_github_tool




tools = [python_inter_tool,fig_inter_tool,sql_inter_tool,extract_data_tool,get_answer_tool,get_answer_github_tool]


def chat_base(messages, client, model):
    """
    获得一次模型对用户的响应。若其中需要调用外部函数，
    则会反复多次调用create_function_response_messages函数获得外部函数响应。
    """
    
    client = client
    model = model
    
    try:
        response = client.chat.completions.create(
            model=model,  
            messages=messages,
            tools=tools,
        )
        
    except Exception as e:
        print("模型调用报错" + str(e))
        return None

    if response.choices[0].finish_reason == "tool_calls":
        while True:
            messages = create_function_response_messages(messages, response)
            response = client.chat.completions.create(
                model=model,  
                messages=messages,
                tools=tools,
            )
            if response.choices[0].finish_reason != "tool_calls":
                break
    
    return response