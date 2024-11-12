# Warning control
import warnings
warnings.filterwarnings('ignore')

from src.custom_functions import parse_websites
from src.json_gmail_send_email import EmailOutput

from crewai import Agent, Task, Crew, LLM
from crewai_tools import DOCXSearchTool
from composio_langchain import ComposioToolSet, Action
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage

import os

def send_personalized_emails(websites, offer_document):
    websites = parse_websites(websites)

    from dotenv import load_dotenv, find_dotenv
    _ = load_dotenv(find_dotenv()) # read local .env file

    ###################### LLM ######################
    langchain_llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    llm = LLM(
        model="gpt-4o",
        base_url=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.5
    )

    ###################### Tools ######################
    composio_toolset = ComposioToolSet(api_key=os.getenv("COMPOSIO_API_KEY"))
    researcher_tools = composio_toolset.get_tools(actions=[
        Action.FIRECRAWL_SCRAPE,
    ])
    email_writer_tools = [DOCXSearchTool()] # semantic search tool
    email_sender_tools = composio_toolset.get_tools(actions=[
        Action.GMAIL_SEND_EMAIL,
    ])

    ###################### Agents ######################
    researcher_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are a salesperson with expertise in searching the internet for email addresses 
            that can be potential customers."""),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        HumanMessagePromptTemplate.from_template("{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    researcher_agent = create_openai_functions_agent(langchain_llm, researcher_tools, researcher_prompt)
    researcher_agent_executor = AgentExecutor(agent=researcher_agent, tools=researcher_tools, verbose=True)

    email_writer = Agent(
        role="Email Writer",
        goal="Create personalized emails based from {document} for each email address in {customers}",
        backstory="You are an email writer with expertise in creating personalized emails "
                "to customers to sell services. You are effective in writing to convince customers "
                "that they need your services.",
        allow_delegation=False,
        verbose=True,
        tools=email_writer_tools,
        llm=llm
    )

    email_sender_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="You are an email sender with expertise in sending emails to customers."),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        HumanMessagePromptTemplate.from_template("{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    email_sender_agent = create_openai_functions_agent(langchain_llm, email_sender_tools, email_sender_prompt)
    email_sender_agent_executor = AgentExecutor(agent=email_sender_agent, tools=email_sender_tools, verbose=True)

    ###################### Tasks ######################
    researcher_task=f"""Get email addresses from websites in the list {websites} and return ONLY a list of email addresses.
    Format the output as a Python list of strings, like: ['email1@example.com', 'email2@example.com']"""

    email_writer_task = Task(
        description=(
            "Create personalized emails based from {document} for each email address in {customers}."
            "For each email, create a dictionary with: "
            "'recipient_email': recipient email address, "
            "'subject': engaging subject line, "
            "'body': personalized email body, "
            "'user_id': 'me', "
            "'is_html': True "
            "Sign all emails from 'JBellSolutions'"
        ),
        expected_output="A list of dictionaries, each containing email parameters (recipient_email, subject, body, user_id, is_html)",
        agent=email_writer,
        output_json=EmailOutput,
        verbose=True
    )

    ####################### Crew #######################
    crew = Crew(
        agents=[email_writer],
        tasks=[email_writer_task],
        verbose=True,
    )

    ####################### Run Crew #######################
    result = researcher_agent_executor.invoke({"input": researcher_task})
    researcher_result = result['output']

    result = crew.kickoff(inputs={
        "document": offer_document,
        # "customers": researcher_result,
        "customers": ["naynesmikel@gmail.com"],
        "verbose": True
    })
    email_writer_result = result['emails']

    email_sender_task=f"""Use the GMAIL_SEND_EMAIL tool to send emails to each of the items in the following list:
    {email_writer_result}"""
    result = email_sender_agent_executor.invoke({"input": email_sender_task})

if __name__=="__main__":
    send_personalized_emails()
