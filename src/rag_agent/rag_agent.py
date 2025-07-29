from __future__ import annotations
import os
import asyncio
from typing import Literal
from dotenv import load_dotenv
load_dotenv(override=True)
from langchain_community.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field
from src.LLMS.llms import llm, embeddings



# ---------------------------------------------------------------------------
# LLM & Embeddings
# ---------------------------------------------------------------------------
MODEL_NAME = "deepseek-chat"
model = llm
grader_model = llm
embed = embeddings
db_path = os.getenv("db_path")



# ---------------------------------------------------------------------------
# Vector store & Retriever tool
# ---------------------------------------------------------------------------
VS_PATH = db_path
vector_store = FAISS.load_local(
folder_path=VS_PATH,
embeddings=embed,
allow_dangerous_deserialization=True,
)
retriever_tool = create_retriever_tool(
vector_store.as_retriever(search_kwargs={"k": 3}),
name="retrieve",
description="Search and return relevant sections from the Documentation.",
)




# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
SYSTEM_INSTRUCTION = (
"You are a data analysis assistant. You can answer ONLY questions related to the "
"data Analytics , including topics such as customer churn prediction, "
"data dictionary, modeling strategies, visualization analysis, business insights, and feature engineering. "
"If the user's question is NOT related to this document, reply exactly: '我只能回答与给定文档相关的问题。' "
"You may call the provided tool `retrieve` when you need more context from the document."
)
GRADE_PROMPT = (
"You are a grader assessing relevance of a retrieved document to a user question.\n"
"Retrieved document:\n{context}\n\nUser question: {question}\n"
"Return 'yes' if relevant, otherwise 'no'."
)
REWRITE_PROMPT = (
"You are a data domain expert assistant.\n"
"Given a user's question about document, "
"your task is to rewrite or expand it in a way that captures the underlying intent clearly, "
"while improving its recall ability for document-based retrieval. Use formal and unambiguous wording.\n\n"
"Original question:\n{question}\n\n"
"Improved version:"
)
ANSWER_PROMPT = (
"You are an expert assistant trained on the data Analytics Handbook.\n"
"Please use the provided context to answer the question in a detailed, structured manner.\n"
"Your answer should ideally include:\n"
"- A concise summary of the relevant concept or finding\n"
"- An explanation of its background or rationale\n"
"- Practical implications or usage suggestions\n"
"- Any supporting statistics or examples from the document\n\n"
"If the context lacks relevant information, reply with: '很抱歉，我无法从文档中找到相关信息。'\n\n"
"Question:\n{question}\n\n"
"Context:\n{context}\n\n"
"Answer:"
)




# ---------------------------------------------------------------------------
# LangGraph Nodes
# ---------------------------------------------------------------------------

async def generate_query_or_respond(state: MessagesState):
    # LLM decides to answer directly or call retriever tool.
    response = await model.bind_tools([retriever_tool]).ainvoke(
    [
    {"role": "system", "content": SYSTEM_INSTRUCTION},
    *state["messages"],
    ]
    )
    return {"messages": [response]}


class GradeDoc(BaseModel):
    binary_score: str = Field(description="Relevance score 'yes' or 'no'.")


async def grade_documents(state: MessagesState) -> Literal["generate_answer",
"rewrite_question"]:
    question = state["messages"][0].content # original user question
    ctx = state["messages"][-1].content # retriever output
    prompt = GRADE_PROMPT.format(question=question, context=ctx)
    result = await grader_model.with_structured_output(GradeDoc).ainvoke([
        {"role": "user", "content": prompt}
    ])
    return "generate_answer" if result.binary_score.lower().startswith("y") else "rewrite_question"


async def rewrite_question(state: MessagesState):
    question = state["messages"][0].content
    prompt = REWRITE_PROMPT.format(question=question)
    resp = await model.ainvoke([{"role": "user", "content": prompt}])
    return {"messages": [{"role": "user", "content": resp.content}]}


async def generate_answer(state: MessagesState):
    question = state["messages"][0].content
    ctx = state["messages"][-1].content
    prompt = ANSWER_PROMPT.format(question=question, context=ctx)
    resp = await model.ainvoke([{"role": "user", "content": prompt}])
    return {"messages": [resp]}


# ---------------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------------

def build_rag_agent():
    """Build the RAG agent."""
    workflow = StateGraph(MessagesState)
    workflow.add_node("generate_query_or_respond", generate_query_or_respond)
    workflow.add_node("retrieve", ToolNode([retriever_tool]))
    workflow.add_node("rewrite_question", rewrite_question)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_edge(START, "generate_query_or_respond")
    workflow.add_conditional_edges(
    "generate_query_or_respond", tools_condition, {"tools": "retrieve", END: END}
    )
    workflow.add_conditional_edges("retrieve", grade_documents)
    workflow.add_edge("generate_answer", END)
    workflow.add_edge("rewrite_question", "generate_query_or_respond")
    rag_agent = workflow.compile(name="rag_agent")

    return rag_agent