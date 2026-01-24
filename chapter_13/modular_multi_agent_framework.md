# Modular Multi-agent Framework

## 1. Objective

AI agent is becoming more and more popular. 
For example, Claude Code has become an essential daily tool that software engineers rely on heavily. 

There are many open-source frameworks to build custom agent system.  

1. [CrewAI](https://github.com/crewAIInc/crewAI) and [Dify](https://github.com/glzjin/dify):

   Pro: Very easy to use, with nice web UI.
   
   Con: Difficult for custom developement. Hard to fix bugs.

2. [SuperAGI](https://github.com/TransformerOptimus/SuperAGI):

   Pro: Well designed system architecture, with many tools covering many functionalities, well documented.

   Con: Learning curve is steep, a tightly coupled package that is hard for bespoke customization.

3. [LangChain/LangGraph](https://github.com/langchain-ai/langgraph):

   Pro: Rich tools convering many functionalities, well documented, very popular.

   Con: A rich but fragmented collection of functional modules that lacks a integrated, holistic system framework.

The objective of this chapter is to build an AI agent framework that resides between `SuperAGI` and `LangChain/LangGraph`. 

1. It is based on `LangChain/LangGraph`.

2. It integrates `LangChain/LangGraph` into a modular loosely decoupled framework, ready for the easy plug-and-play of new modules.
