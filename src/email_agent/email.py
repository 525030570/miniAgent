import os
import sys
from typing import Literal
from datetime import datetime
from langchain_core.tools import tool
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from src.LLMS.llms import llm
from langgraph.graph import END
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END
from datetime import datetime
from IPython.display import Markdown
from dotenv import load_dotenv
load_dotenv("../.env")
sys.path.append("..")





class State(MessagesState):
    email_input: dict
    classification_decision: Literal["ignore", "respond", "notify"]


class RouterSchema(BaseModel):
    """Analyze the unread email and route it according to its content."""
    
    reasoning: str = Field(
        description="Step-by-step reasoning behind the classification."
    )
    classification: Literal["ignore", "respond", "notify"] = Field(
        description="The classification of an email: 'ignore' for irrelevant emails, "
        "'notify' for important information that doesn't need a response, "
        "'respond' for emails that need a reply",
    )



llm_router = llm.with_structured_output(RouterSchema)





def read_email() -> dict:
    """read the latest email."""
    # Placeholder response - in real app would read email
    return {
    "author": "System Admin <sysadmin@company.com>",
    "to": "Development Team <dev@company.com>",
    "subject": "Scheduled maintenance - database downtime",
    "email_thread": "Hi team,\n\nThis is a reminder that we'll be performing scheduled maintenance on the production database tonight from 2AM to 4AM EST. During this time, all database services will be unavailable.\n\nPlease plan your work accordingly and ensure no critical deployments are scheduled during this window.\n\nThanks,\nSystem Admin Team"
}

@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write and send an email."""
    # Placeholder response - in real app would send email
    return f"Email sent to {to} with subject '{subject}' and content: {content}"

@tool
def schedule_meeting(
    attendees: list[str], subject: str, duration_minutes: int,
    preferred_day: datetime, start_time: int
) -> str:
    """Schedule a calendar meeting."""
    # Placeholder response - in real app would check calendar and schedule
    date_str = preferred_day.strftime("%A, %B %d, %Y")
    return f"Meeting '{subject}' scheduled on {date_str} at {start_time} for {duration_minutes} minutes with {len(attendees)} attendees"

@tool
def check_calendar_availability(day: str) -> str:
    """Check calendar availability for a given day."""
    # Placeholder response - in real app would check actual calendar
    return f"Available times on {day}: 9:00 AM, 2:00 PM, 4:00 PM"

@tool
class Done(BaseModel):
    """E-mail has been sent."""
    done: bool




# Email assistant triage prompt 
triage_system_prompt = """

< Role >
Your role is to triage incoming emails based upon instructs and background information below.
</ Role >

< Background >
{background}. 
</ Background >

< Instructions >
Categorize each email into one of three categories:
1. IGNORE - Emails that are not worth responding to or tracking
2. NOTIFY - Important information that worth notification but doesn't require a response
3. RESPOND - Emails that need a direct response
Classify the below email into one of these categories.
</ Instructions >

< output_format >
请以 JSON 格式输出结果，必须包含 "reasoning" 和 "classification" 字段。"classification" 值可以是 "ignore", "respond", "notify"。
</ output_format >

< Rules >
{triage_instructions}
</ Rules >
"""

# Email assistant triage user prompt 
triage_user_prompt = """
你是一个邮件分类助手，请根据邮件内容判断其类型。

请以 JSON 格式输出结果，必须包含以下两个字段：
- "classification"：值可以是 "ignore"、"respond" 或 "notify"
- "reasoning"：一段简短的文字，说明你做出该分类的理由

请确保输出是标准的 JSON 格式，不要包含其他额外内容。

示例输出：
{example}

以下是邮件内容，请进行分类：
Please determine how to handle the below email thread:

From: {author}
To: {to}
Subject: {subject}
{email_thread}"""

# Default background information 
default_background = """ 
I'm Victor, a software engineer.
"""

example = """
{
  "classification": "respond",
  "reasoning": "这封邮件中包含一个需要我回复的技术问题。"
}
"""


# Default triage instructions 
default_triage_instructions = """
Emails that are not worth responding to:
- Marketing newsletters and promotional emails
- Spam or suspicious emails
- CC'd on FYI threads with no direct questions

There are also other things that should be known about, but don't require an email response. For these, you should notify (using the `notify` response). Examples of this include:
- Team member out sick or on vacation
- Build system notifications or deployments
- Project status updates without action items
- Important company announcements
- FYI emails that contain relevant information for current projects
- HR Department deadline reminders
- Subscription status / renewal reminders
- GitHub notifications

Emails that are worth responding to:
- Direct questions from team members requiring expertise
- Meeting requests requiring confirmation
- Critical bug reports related to team's projects
- Requests from management requiring acknowledgment
- Client inquiries about project status or features
- Technical questions about documentation, code, or APIs (especially questions about missing endpoints or features)
- Personal reminders related to family (wife / daughter)
- Personal reminder related to self-care (doctor appointments, etc)
"""




def triage_router(state: State) -> Command[Literal["response_agent", "__end__"]]:
    """Analyze email content to decide if we should respond, notify, or ignore."""
    
    state["email_input"] = read_email()

    # 从输入的邮件信息中提取对应的字段
    author, to, subject, email_thread = parse_email(state["email_input"])
    
    # 格式化完整的system prompt和user prompt
    system_prompt = triage_system_prompt.format(
        background=default_background,
        triage_instructions=default_triage_instructions,
    )
    
    user_prompt = triage_user_prompt.format(
        author=author, to=to, subject=subject, email_thread=email_thread, example=example,
    )
    
    
    # 调用配置了结构化输出的LLM
    result = llm_router.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])
    
    # 根据分类结果决定下一步行动
    match result.classification:
        case"respond":
            goto = "response_agent"
            update = {
                "messages": [{
                    "role": "user",
                    "content": f"Respond to the email: \n\n{format_email_markdown(subject, author, to, email_thread)}",
                }],
                "classification_decision": result.classification,
            }
        case"ignore":
            goto = END
            update = {"classification_decision": result.classification}
        case"notify":
            goto = END
            update = {"classification_decision": result.classification}
        case _:
            raise ValueError(f"Invalid classification: {result.classification}")
    
    return Command(goto=goto, update=update)


def parse_email(email_input: dict) -> dict:
    """Parse an email input dictionary.

    Args:
        email_input (dict): Dictionary containing email fields:
            - author: Sender's name and email
            - to: Recipient's name and email
            - subject: Email subject line
            - email_thread: Full email content

    Returns:
        tuple[str, str, str, str]: Tuple containing:
            - author: Sender's name and email
            - to: Recipient's name and email
            - subject: Email subject line
            - email_thread: Full email content
    """
    return (
        email_input["author"],
        email_input["to"],
        email_input["subject"],
        email_input["email_thread"],
    )


def format_email_markdown(subject, author, to, email_thread, email_id=None):
    """Format email details into a nicely formatted markdown string for display
    
    Args:
        subject: Email subject
        author: Email sender
        to: Email recipient
        email_thread: Email content
        email_id: Optional email ID (for Gmail API)
    """
    id_section = f"\n**ID**: {email_id}" if email_id else ""
    
    return f"""

**Subject**: {subject}
**From**: {author}
**To**: {to}{id_section}

{email_thread}

---"""






# Email assistant prompt 
agent_system_prompt = """
< Role >
You are a top-notch executive assistant who cares about helping your executive perform as well as possible.
</ Role >

< Tools >
You have access to the following tools to help manage communications and schedule:
{tools_prompt}
</ Tools >

< Instructions >
When handling emails, follow these steps:
1. Carefully analyze the email content and purpose
2. IMPORTANT --- always call a tool and call one tool at a time until the task is complete: 
3. For responding to the email, draft a response email with the write_email tool
4. For meeting requests, use the check_calendar_availability tool to find open time slots
5. To schedule a meeting, use the schedule_meeting tool with a datetime object for the preferred_day parameter
   - Today's date is """ + datetime.now().strftime("%Y-%m-%d") + """ - use this for scheduling meetings accurately
6. If you scheduled a meeting, then draft a short response email using the write_email tool
7. After using the write_email tool, the task is complete
8. If you have sent the email, then use the Done tool to indicate that the task is complete
</ Instructions >

< Background >
{background}
</ Background >

< Response Preferences >
{response_preferences}
</ Response Preferences >

< Calendar Preferences >
{cal_preferences}
</ Calendar Preferences >
"""



# Default response preferences 
default_response_preferences = """
Use professional and concise language. If the e-mail mentions a deadline, make sure to explicitly acknowledge and reference the deadline in your response.

When responding to technical questions that require investigation:
- Clearly state whether you will investigate or who you will ask
- Provide an estimated timeline for when you'll have more information or complete the task

When responding to event or conference invitations:
- Always acknowledge any mentioned deadlines (particularly registration deadlines)
- If workshops or specific topics are mentioned, ask for more specific details about them
- If discounts (group or early bird) are mentioned, explicitly request information about them
- Don't commit 

When responding to collaboration or project-related requests:
- Acknowledge any existing work or materials mentioned (drafts, slides, documents, etc.)
- Explicitly mention reviewing these materials before or during the meeting
- When scheduling meetings, clearly state the specific day, date, and time proposed

When responding to meeting scheduling requests:
- If times are proposed, verify calendar availability for all time slots mentioned in the original email and then commit to one of the proposed times based on your availability by scheduling the meeting. Or, say you can't make it at the time proposed.
- If no times are proposed, then check your calendar for availability and propose multiple time options when available instead of selecting just one.
- Mention the meeting duration in your response to confirm you've noted it correctly.
- Reference the meeting's purpose in your response.
"""



# Default calendar preferences 
default_cal_preferences = """
30 minute meetings are preferred, but 15 minute meetings are also acceptable.
"""



# Tool descriptions for agent workflow without triage
AGENT_TOOLS_PROMPT = """
1. write_email(to, subject, content) - Send emails to specified recipients
2. schedule_meeting(attendees, subject, duration_minutes, preferred_day, start_time) - Schedule calendar meetings where preferred_day is a datetime object
3. check_calendar_availability(day) - Check available time slots for a given day
4. Done - E-mail has been sent
"""



full_agent_system_prompt = agent_system_prompt.format(
                        tools_prompt=AGENT_TOOLS_PROMPT,
                        background=default_background,
                        response_preferences=default_response_preferences,
                        cal_preferences=default_cal_preferences, 
                    )



# collect the tools
tools = [write_email, schedule_meeting, check_calendar_availability, Done]
tools_by_name = {tool.name: tool for tool in tools}

# Initialize the llm and enforce tool use
llm_with_tools = llm.bind_tools(tools, tool_choice="any", parallel_tool_calls=False)


def llm_call(state: State):
    """LLM decides whether call a tool or not"""

    # Invoke the LLM
    output = llm_with_tools.invoke(
                # Add the system prompt
                [   
                    {"role": "system", "content": full_agent_system_prompt},
                ]
                # Add the current messages to the prompt
                + state["messages"]
            )

    return {"messages": [output]}



def tool_handler(state: State):
    """Perform the tool call."""

    # list for tool results
    result = []

    # iterate excute tool call
    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call["name"]
        tool = tools_by_name[tool_name]
        observation = tool.invoke(tool_call["args"])
        result.append({
            "role": "tool",
            "content": observation,
            "tool_call_id": tool_call["id"]
        })

    return {"messages": result}



def should_continue(state: State) -> Literal["tool_handler", "__end__"]:
    """Route to tool handler, or end if Done tool called"""

    # get the last message
    messages = state["messages"]
    last_message = messages[-1]

    # Check if it's a Done tool call
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls: 
            if tool_call["name"] == "Done":
                return END
            else:
                return "tool_handler"
            

def build_agent():
    """Build the agent workflow."""
    # build workflow
    overall_workflow = StateGraph(State)

    # add node
    overall_workflow.add_node('llm_call', llm_call)
    overall_workflow.add_node('tool_handler', tool_handler)

    # add edge
    overall_workflow.add_edge(START, 'llm_call')
    overall_workflow.add_conditional_edges(
        'llm_call',
        should_continue,
        {
            "tool_handler": "tool_handler",
            END: END
        }
    )
    overall_workflow.add_edge('tool_handler', 'llm_call')

    # compile
    agent = overall_workflow.compile()

    return agent



def build_overall_workflow():
    """Build the overall workflow."""

    agent = build_agent()
    overall_workflow = (
        StateGraph(State)
        .add_node('email_router', triage_router)
        .add_node('response_agent', agent)
        .add_edge(START, "email_router")
    ).compile(name="emailoverall_workflow")

    return overall_workflow
