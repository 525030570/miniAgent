
from langgraph.store.base import BaseStore  
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig  
from src.LLMS.llms import llm
from typing import List, Optional
from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage  
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





# 用于定义内存存储的用户配置文件结构的Pydantic模型
class UserProfile(BaseModel):  
    customer_id: str = Field(  
        description="客户的客户ID"  
    )  
    preferences: List[str] = Field(  
        description="客户的偏好"  
    )



# 用于格式化用户内存数据以用于LLM提示的辅助函数
def format_user_memory(user_data):  
    """如果可用，则格式化用户的偏好。"""  
    # 访问保存UserProfile对象的'memory'键
    profile = user_data['memory']   
    result = ""  
    # 检查preferences属性是否存在且不为空
    if hasattr(profile, 'preferences') and profile.preferences:  
        result += f"Preferences: {', '.join(profile.preferences)}"  
    return result.strip()  



# 节点：load_memory
def load_memory(state: State, config: RunnableConfig, store: BaseStore):  
    """  
    从给定用户的长期内存存储中加载偏好。
    此节点获取先前保存的用户偏好，为当前对话提供上下文，从而实现个性化响应。
    """  
    # 从配置的可配置部分获取user_id
    # 在我们的评估设置中，我们可能会通过配置传递user_id
    user_id = config["configurable"].get("user_id", state["customer_id"]) # 如果配置中没有user_id，则使用customer_id
    # 定义用于在存储中访问内存的命名空间和键
    namespace = ("memory_profile", user_id)  
    key = "user_memory"  
    # 检索用户的现有内存
    existing_memory = store.get(namespace, key)  
    formatted_memory = ""  
    # 如果检索到的内存存在且有内容，则对其进行格式化
    if existing_memory and existing_memory.value:  
        formatted_memory = format_user_memory(existing_memory.value)  
    # 使用加载并格式化的内存更新状态
    return {"loaded_memory": formatted_memory}




# create_memory智能体的提示，指导其更新用户内存
create_memory_prompt = """你是一位专家分析师，正在观察客户与客户支持助理之间的对话。利用多智能体团队来回答客户的请求。
你的任务是分析客户与客户支持助理之间的对话，并更新与客户关联的内存配置文件。内存配置文件可能为空。如果为空，你应该为客户创建一个新的内存配置文件。
你特别关注保存客户分享的任何兴趣，尤其是他们的偏好到他们的内存配置文件中。
为了帮助你完成此任务，我附上了客户与客户支持助理之间的对话，以及与客户关联的现有内存配置文件，你应该根据对话更新或创建该配置文件。
客户的内存配置文件应包含以下字段：
- customer_id: 客户的客户ID
- preferences: 客户的偏好
这些是你应该在内存配置文件中跟踪和更新的字段。如果没有新的信息，则不应更新内存配置文件。如果你没有新的信息来更新内存配置文件，这完全没问题。在这种情况下，只需保持现有值不变。
*以下是重要信息*
你应该分析的客户与客户支持助理之间的对话如下：
{conversation}
你应该根据对话更新或创建的与客户关联的现有内存配置文件如下：
{memory_profile}
确保你的响应是一个包含以下字段的对象：
- customer_id: 客户的客户ID
- preferences: 客户的偏好
示例输出：
{example}
对于对象中的每个键，如果没有新信息，则不要更新值，只需保留已有的值。如果有新信息，则更新值。
"""

example = """
{
  "customer_id": "user_123",
  "preferences": ["music", "technology", "sports"]
}
"""


# 节点：create_memory
def create_memory(state: State, config: RunnableConfig, store: BaseStore):  
    """  
    分析对话历史并更新用户的长期内存配置文件。
    此节点提取客户在对话期间分享的新偏好，并将其持久化到InMemoryStore中以供将来交互使用。
    """  
    # 从配置的可配置部分或状态中获取user_id
    user_id = str(state["customer_id"])
    # 定义内存配置文件的命名空间和键
    namespace = ("memory_profile", user_id)  
    key = "user_memory"  
    # 检索用户的现有内存配置文件
    existing_memory = store.get(namespace, key)  
    # 为LLM提示格式化现有内存
    formatted_memory = ""  
    if existing_memory and existing_memory.value:  
        existing_memory_dict = existing_memory.value  
        # 确保'music_preferences'被视为列表，即使它可能缺失或为None
        music_prefs = existing_memory_dict.get('music_preferences', [])  
        if music_prefs:  
            formatted_memory = f"Music Preferences: {', '.join(music_prefs)}"  
    # 准备用于LLM更新内存的系统消息
    formatted_system_message = SystemMessage(content=create_memory_prompt.format(  
        conversation=state["messages"],   
        memory_profile=formatted_memory,
        example=example,
    ))  
    # 使用UserProfile模式调用LLM以获取结构化的更新内存
    updated_memory = llm.with_structured_output(UserProfile).invoke([formatted_system_message])  
    # 存储更新后的内存配置文件
    store.put(namespace, key, {"memory": updated_memory})