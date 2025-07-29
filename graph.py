from typing_extensions import TypedDict  
from typing import Annotated, List  
from langgraph.graph.message import AnyMessage, add_messages  
from langgraph.managed.is_last_step import RemainingSteps  
from langgraph.graph import StateGraph, START, END
from src.HITL.human_in_the_loop import human_input, should_interrupt
from src.verify_info.verify import verify_info
from src.Memory.memory import load_memory, create_memory
from langgraph.checkpoint.memory import MemorySaver  
from langgraph.store.memory import InMemoryStore  
from src.supervisor_agent.supervisor_agent import build_supervisor
import os



os.environ["LANGSMITH_TRACING"]  = "true"                     # 开启追踪
os.environ["LANGSMITH_API_KEY"]  = "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" 
os.environ["LANGSMITH_PROJECT"]  = "miniAgent"         # 任意项目名



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


supervisor_agent = build_supervisor()

def build_multi_agent_final_graph():
    multi_agent_final = StateGraph(State)  
    # 将所有现有节点和新节点添加到图中
    multi_agent_final.add_node("verify_info", verify_info)  
    multi_agent_final.add_node("human_input", human_input)  
    multi_agent_final.add_node("load_memory", load_memory)  
    multi_agent_final.add_node("supervisor", supervisor_agent) 
    multi_agent_final.add_node("create_memory", create_memory)  
    # 定义图的入口点：始终从信息验证开始
    multi_agent_final.add_edge(START, "verify_info")  
    # 验证后的条件路由：如果需要则中断，否则加载内存
    multi_agent_final.add_conditional_edges(  
        "verify_info",  
        should_interrupt, # 检查customer_id是否已验证
        {  
            "continue": "load_memory", # 如果已验证，则继续加载长期内存
            "interrupt": "human_input", # 如果未验证，则中断以获取人工输入
        },  
    )  
    # 人工输入后，始终循环回到verify_info
    multi_agent_final.add_edge("human_input", "verify_info")  
    # 加载内存后，将控制权传递给监督者
    multi_agent_final.add_edge("load_memory", "supervisor")  
    # 监督者完成后，保存任何新内存
    multi_agent_final.add_edge("supervisor", "create_memory")  
    # 创建/更新内存后，工作流结束
    multi_agent_final.add_edge("create_memory", END)  
    # 编译包含所有组件的最终图
    multi_agent_final_graph = multi_agent_final.compile(  
        name="multi_agent_verify",   
    )  
    return multi_agent_final_graph

graph = build_multi_agent_final_graph()





