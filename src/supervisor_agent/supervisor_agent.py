from langgraph_supervisor import create_supervisor
from src.data_agent.data import built_data_agent, built_data_agent_2
from src.email_agent.email import build_overall_workflow
from src.LLMS.llms import llm
from langgraph.graph import StateGraph, END, START
from typing import Annotated, List  
from langgraph.graph.message import AnyMessage, add_messages  
from langgraph.managed.is_last_step import RemainingSteps 
from typing_extensions import TypedDict 
from src.rag_agent.rag_agent import build_rag_agent



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


sql_agent = built_data_agent()
python_agent = built_data_agent_2()
email_agent = build_overall_workflow()
rag_agent = build_rag_agent()


def build_supervisor():
    """
    构建一个监督者智能体，负责管理SQL、Python和电子邮件代理。
    该智能体将根据任务类型分配工作给相应的代理。
    """

    agent = create_supervisor(
        model=llm,
        agents=[sql_agent, python_agent, email_agent, rag_agent],
        prompt=(
            "You are a supervisor managing four agents:\n"
            "- a SQL agent. Assign SQL-related tasks to this agent\n"
            "- a Python agent. Assign Python-related tasks to this agent\n"
            "- an email agent. Assign email-related tasks to this agent\n"
            "- a RAG agent. Assign RAG-related tasks to this agent\n"
            "Assign work to one agent at a time, do not call agents in parallel.\n"
            "Do not do any work yourself."
            "If the task is complete and no further action is needed, respond with: {'next': 'create_memory'}"
        ),
        add_handoff_back_messages=True,
        output_mode="full_history",
        supervisor_name="supervisor",
    ).compile()
    return agent
