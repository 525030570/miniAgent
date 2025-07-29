from langgraph.types import interrupt
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



def human_input(state: State, config: RunnableConfig):  
    """  
    用于请求用户输入的人工介入节点，实现工作流中断机制。
    此节点在工作流中创建中断点，允许系统暂停并等待人工输入后再继续执行。
    它通常用于客户验证或需要其他信息的场景。
    参数：
        state (State): 包含消息和工作流数据的当前状态
        config (RunnableConfig): 可运行执行的配置
    返回：
        dict: 包含用户输入消息的更新状态
    """  
    # 中断工作流并提示用户输入
    user_input = interrupt("Please provide input.")  
    # 将用户输入作为新消息返回到状态中
    return {"messages": [user_input]}



def should_interrupt(state: State, config: RunnableConfig):  
    """  
    确定工作流是否应中断并请求人工输入的条件判断函数。
    如果customer_id存在于状态中（表示验证已完成），
    则工作流继续执行。否则，它会中断以获取人工输入进行验证。
    """  
    if state.get("customer_id") is not None:  
        return "continue" # 客户ID已验证，继续下一步（监督者）
    else:  
        return "interrupt" # 客户ID未验证，中断以获取人工输入