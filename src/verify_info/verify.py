from pydantic import BaseModel, Field
from src.LLMS.llms import llm
from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage  
from langchain_core.runnables import RunnableConfig  
from typing_extensions import TypedDict  
from typing import Annotated, List  
from langgraph.graph.message import AnyMessage, add_messages  
from langgraph.managed.is_last_step import RemainingSteps 




class State(TypedDict):
    """  
    多智能体客户支持工作流的状态模式。
      
    这定义了在图中节点之间流动的共享数据结构，
    表示对话和智能体状态的当前快照。
    """  
    # 从帐户验证中检索到的用户标识符
    customer_id: str  
      
    # 具有自动消息聚合的对话历史记录
    messages: Annotated[list[AnyMessage], add_messages]  
      
    # 从长期内存存储加载的用户偏好和上下文
    loaded_memory: str  
      
    # 防止智能体工作流中无限递归的计数器
    remaining_steps: RemainingSteps



class UserInput(BaseModel):
    """用于解析员工提供的帐户信息的模式。"""  
    identifier: str = Field(description="标识符，可以是员工 ID、电子邮件或电话号码。")  


# 创建一个结构化的 LLM，其输出响应符合 UserInput 模式
structured_llm = llm.with_structured_output(schema=UserInput)  


# 用于提取员工标识符信息的系统提示
structured_system_prompt = """
你是一个客服代表，负责从对话历史中提取员工标识符信息。

你的任务是：
- 从对话中提取员工的标识符（如员工 ID、电子邮件或电话号码）；
- 如果员工尚未提供标识符，请返回空字符串；
- 请以 JSON 格式输出，必须包含字段 `identifier`；

示例输出：
{example1}

如果未提供标识符：
{example2}
"""

example1 = """
{
  "identifier": "1234567890"
}
"""

example2 = """
{
  "identifier": ""
}
"""


from typing import Optional   
# 客户识别辅助函数
def get_customer_id_from_identifier(identifier: str) -> Optional[int]:  
    """  
    使用标识符检索客户 ID，标识符可以是客户 ID、电子邮件或电话号码。
    此函数支持三种类型的标识符：
    1. 直接客户 ID（数字字符串）
    2. 电话号码（以“+”开头）
    3. 电子邮件地址（包含“@”）
    参数：
        identifier (str): 标识符可以是客户ID、电子邮件或电话号码。
    返回：
        Optional[int]: 如果找到则返回CustomerId，否则返回None。
    """ 
    # 检查标识符是否为直接客户ID（数字）
    if identifier.isdigit():  
        return int(identifier)  
    # # 检查标识符是否为电话号码（以"+"开头）
    # elif identifier[0] == "+":  
    #     query = f"SELECT CustomerId FROM Customer WHERE Phone = '{identifier}';"  
    #     result = db.run(query)  
    #     formatted_result = ast.literal_eval(result)  
    #     if formatted_result:  
    #         return formatted_result[0][0]  
    # # 检查标识符是否为电子邮件地址（包含"@"）
    # elif "@" in identifier:  
    #     query = f"SELECT CustomerId FROM Customer WHERE Email = '{identifier}';"  
    #     result = db.run(query)  
    #     formatted_result = ast.literal_eval(result)  
    #     if formatted_result:  
    #         return formatted_result[0][0]  
    # # 如果未找到匹配项，则返回None
    return None 
 


def verify_info(state: State, config: RunnableConfig):  
    """  
    通过解析客户输入并将其与数据库进行匹配来验证客户账户信息。
    此节点处理客户支持流程的第一步——客户身份认证。
    它从用户消息中提取客户标识符（ID、电子邮件或电话）并根据数据库进行验证。
    参数：
        state (State): 包含消息和潜在customer_id的当前状态
        config (RunnableConfig): 可运行执行的配置
    返回：
        dict: 如果已验证则包含customer_id的更新状态，或请求更多信息
    """  
    # 仅当customer_id尚未设置时才进行验证
    if state.get("customer_id") is None:   
        # 用于提示客户验证的系统指令
        system_instructions = """You are an agent, where you are trying to verify the customer identity   
        as the first step of the customer support process.   
        Only extract the customer's account information from the message history.   
        If they haven't provided the information yet, return an empty string for the identifier.   
        If they have provided the identifier but cannot be found, please ask them to revise it."""  
        # 获取最近的用户消息
        user_input = state["messages"][-1]   
        # 使用结构化LLM从消息中解析客户标识符
        parsed_info = structured_llm.invoke([SystemMessage(content=structured_system_prompt.format(
            example1=example1,  
            example2=example2
        ))] + [user_input])  
        # 从解析的响应中提取标识符
        identifier = parsed_info.identifier  
        # 将customer_id初始化为空
        customer_id = ""  
        # 尝试使用提供的标识符查找客户ID
        if (identifier):  
            customer_id = get_customer_id_from_identifier(identifier)  
        # 如果找到客户，则确认验证并在状态中设置customer_id
        if customer_id != "":  
            intent_message = SystemMessage(  
                content= f"Thank you for providing your information! I was able to verify your account with customer id {customer_id}."  
            )  
            return {  
                  "customer_id": customer_id,  
                  "messages" : [intent_message]  
                  }  
        else:  
            # 如果未找到客户，则请求正确的信息
            response = llm.invoke([SystemMessage(content=system_instructions)]+state['messages'])  
            return {"messages": [response]}  
    else:   
        # 客户已验证，无需操作
        pass