# miniAgent -- 一个简单的基层工作小助手

![studio_graph.png](studio_graph.png)
## 项目核心功能

### multi-agent

- 基于LangGraph构建Supervisor架构的Multi-Agent系统

- Sub-Agent : Rag模块、NL2SQL模块、NL2Python模块、联网查询模块、邮件管理助手

- 构建长短期记忆管理模块，实现对话消息的动态裁剪、总结摘要

- 实现Human-in-the-Loop功能，在AI工作流的关键节点引入人工干预

                  multi-agent的核心架构如图所示
   ![alt text](multi-agent-frame.png)

   
### sub-agent

- 联网查询功能：接入Google search API, 通过selenium获取网络知识

- GitHub查询功能：接入GitHub API, 让Agent能够查询各种开源项目

- NL2Python 模块：将自然语言描述转化为Python代码

- NL2SQL 模块：将自然语言描述转化为SQL代码，实现本地数据库查询

- RAG 模块：查询本地向量知识库，为Agent提供私有知识

- 邮件管理助手

                  Supervisor架构的sub-agent如图所示
   ![alt text](sub-agent-frame.png)


## 项目结构
```
miniAgent
├─ .env
├─ .langgraph_api
├─ examples.ipynb
├─ graph.py
├─ langgraph.json
├─ multi-agent-frame.png
├─ requirements.txt
├─ src
│  ├─ data_agent
│  ├─ email_agent
│  ├─ HITL
│  ├─ LLMS
│  ├─ main.py
│  ├─ Memory
│  ├─ modules
│  ├─ rag_agent
│  ├─ supervisor_agent
│  ├─ utils
│  ├─ verify_info
│  └─ __init__.py
└─ README.md
```


## 项目背景

乡镇一线供电工作不仅要肩负着万家灯火保一方用电的重任，还要应付本单位的、上级单位的、当地从乡镇到省府的各种大大小小的工作。在现场抢修完就马上回办公室写报告和写完报告就立马赶往下一个抢修现场的来回奔波之际，我日思夜想都希望能有一个自动化式的工具能帮我应付这些乱七八糟的报表和报告。如今基于大模型的Agent技术似乎展现出了能替人类分担一些繁琐无意义工作的能力，故该项目尝试利用大模型Agent技术来寻找一个能分担基层工作人员压力的解决方案。

### 用户痛点

1. 基层工作中办公室工作和现场工作割裂
2. 信息系统中流程化工作繁琐极度消耗时间和精力，挤占现场工作时间
3. 每一次的信息系统中流程化工作高度重复，但有时候又会有一些小差异


### 解决方案

1. 信息系统相关的工作尽可能的交给Agentic AI来完成，人类主要负责物理世界的现场工作
2. 针对不同的信息系统中流程化工作开发不同的外部工具交给特定的sub_agent调用
3. 通过ReAct（思考-行动-观察）循环行为模式解决高度重复工作中小差异问题，必要时在关键节点引入人工干涉进行工作指导




## 项目启动

1. 创建虚拟环境
```bash
# 创建虚拟环境
conda create -n miniAgent python=3.11
# 创建虚拟环境
conda activate miniAgent
# 安装项目依赖
pip install -r requirements.txt
```

2. 在.env文件中配置环境变量

3. 安装`langgraph-cli`以及其他依赖
```bash
pip install -U "langgraph-cli[inmem]" -i https://pypi.tuna.tsinghua.edu.cn/simple
```

4. 创建`langgraph.json`文件

在项目文件夹中，新建一个`langgraph.json`文件，在该`json`文件中配置项目信息，遵循规范如下所示：
- 必须包含 `dependencies` 和 `graphs` 字段
- `graphs` 字段格式："图名": "文件路径:变量名"
- 配置文件必须放在与Python文件同级或更高级的目录

5. 项目启动
```bash
langgraph dev
```

## 项目效果

请看 ```examples.ipynb```

修改```.env```文件，即可通过OpenAI SDK接入在线大模型

直接在终端中运行main.py或者在Jupyter Notebook中运行main.py都可。

## 项目改进

未来准备将Agent助手与 Electrical RAG 项目进行整合，打造一个轻量化的便于一线产业工程师使用的AI大模型智能助手。



