import os
import smtplib
from email.mime.text import MIMEText
from typing import Optional

from dotenv import dotenv_values, load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_groq import ChatGroq
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pydantic import BaseModel

# Integrating Langsmith with the system for troubleshooting and debugging
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "Chatbot Doc Mapping"

# loading env variables
config = dotenv_values(".env")
load_dotenv()

# Initiating Fast api
app = FastAPI(title="RAG FUSION MAPPING SEMANTICS")

# handling CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def send_gmail(subject, body, sender, recipients, password):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipients
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")


# Defining Request model
class RequestModel(BaseModel):
    query: str
    context: Optional[list[str]] = None
    session_id: str


class EmailModel(BaseModel):
    subject: str
    chat: dict
    session_id: str
    ip_address: str
    user_info: dict


# creating vector db with pinecone
pinecone_api_key = os.environ.get("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)

# declaring embedding
embeddings = OpenAIEmbeddings()
# declaring index name for vector db which will be used for retrieval
index_name = "jellyfish-vector-db"

# existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

# if index_name not in existing_indexes:
#     pc.create_index(
#         name=index_name,
#         dimension=1536,
#         metric="cosine",
#         spec=ServerlessSpec(cloud="aws", region="us-east-1"),
#     )
#     while not pc.describe_index(index_name).status["ready"]:
#         time.sleep(1)

# index = pc.Index(index_name)


# docs = []
# for i in range(len(text)):
#     docs.append(Document(page_content=text[i], metadata={}))

# gpt = ChatOpenAI(
#     temperature=0.0,
#     api_key=os.getenv("OPENAI_API_KEY"),
#     model_name="gpt-3.5-turbo",
# )

# summaries = []
# for i in docs:
#     chain = (
#         ChatPromptTemplate.from_template("Summarize the following document:\n\n{doc}")
#         | gpt
#         | StrOutputParser()
#     )
#     summaries.append(chain.invoke({"doc": i.page_content}))


# summary_docs = [
#     Document(page_content=summaries[i], metadata={"original_content": text[i]})
#     for i in range(len(summaries))
# ]

# #inserting data
# docsearch = PineconeVectorStore.from_documents(
#     summary_docs, embeddings, index_name=index_name
# )

# # Add more data
# vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
# vectorstore.add_documents(documents=summary_docs)


# retrieving context
def context_retriever(query):
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    docs = vectorstore.similarity_search(query, k=1)
    if len(docs) != 0:
        content = docs[0].metadata["original_content"]
    else:
        content = "Frame a professional answer which shows the positive image of the company and should be relevant to the query"
    return content


user_message = """

<|Storyline|>
You are Jelly, an Assistant of Jellyfish Technologies Website.\
Throughout your interactions, you aim to ask relevant question to understand their requirements and highlight how Jellyfish Technologies can meet those needs.\
Your primary goal is to guide users to contact the company through the contact form or contact details to discuss their needs and how Jellyfish Technologies can help them.\
Each response should be a step towards encouraging the user to get in touch with the company.\
Your mission is to ensure every visitor is impressed with Jellyfish Technologies and eager to take advantage of your services.\
Start by greeting the user warmly, then proceed to ask questions that help identify their needs. Highlight the benefits of Jellyfish Technologies' services and guide the user to the contact form to make a deal.\
Here are some key points to include in your responses:
- Highlight Jellyfish Technologies' expertise and certifications.
- Mention the company's global presence and successful projects.
- Emphasize the importance of getting a tailored solution from the sales team.
- Always direct the user to the contact form for further assistance.

<|Instructions|>
Always give professional and formal answers.\
Strictly provide relevant urls with every repsonse.\
Don't try to connect the user to us, on your own. Always make the user contact us on their own through contact form or provided contact details of jft.\
Don't ask too much specifications about the query simply ask three to four follow up then direct them to contact us page without anything else in the response.\
If any question is unproffesional or irrevelant to the benefits of the company like song, bomb threat, illegal activities, reply "Your question does not align with professional standards. If you have any inquiries related to Jellyfish Technologies, please feel free to ask. I am happy to help."\
Make sure you always provide a positive image of Jellyfish, do not provide unnecessary details.\
Only use the context provided below, to provide an answer in about 70 words kind of summary without missing any important information present in the context. Don't write according to the context. Stick to the role.\
If you don't know the answer, just say that you are still learning and improving yourself. \
Strictly don't provide response in markdown\

<|Context|>
CTO of JFT: Amit Kumar Pandey, CEO of the Company: Gaurav Chauhan, COO of Jellyfish: Neeraj Kumar. \ 
Global Presence/Branches/Addresses/Locations : 59, West Broadway #200 Salt Lake City Utah-84101, United States: US office Location, URL: https://www.google.com/maps/search/jellyfish+technologies+salt+lake/@40.761821,-116.5041917,7z?entry=ttu, D-5, Third Floor, Logix Infotech, Sector-59, Noida-201301, India: Location, URL: https://www.google.com/maps/place/Jellyfish+Technologies+%7C+Software+Development+Company/@28.6080993,77.3696763,17z/data=!3m1!4b1!4m6!3m5!1s0x390ceff2a400bb77:0xf4123d7195e9427a!8m2!3d28.6080993!4d77.3722512!16s%2Fg%2F11bxg37vwc?entry=ttu\
Contact form: https://www.jellyfishtechnologies.com/contact-us/\
Awards/Recognition/Certifications/Greeting bagged by Jellyfish/ reasons to choose jellyfish: 5/5 verified rating on Goodfirms, Top Developers on Clutch, Salesforce Certified Developer, Best Company by Goodfirms, Great Place to Work Certified\
Contact Details: Email: enquiry@jellyfishtechnologies.com, hr@jellyfishtechnologies.com, Phone: +1-760-514-0178, linekdin: https://www.linkedin.com/company/teamjft/mycompany/ 

{context}\
Strictly Answer in less than 70 words\
Strictly provide all the relevant urls with every response.\
Strictly frame your responses in such a way that it diverts the user to the contact form page along with the relevant url associated with the information.\
"""

human_message_template = """
<|Question|>
{question}
"""

# creating prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", user_message),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)

# declaring llm
llm = ChatGroq(
    temperature=0.0,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama3-70b-8192",
)

# llm = ChatOpenAI(temperature=0.0, api_key=os.getenv('OPENAI_API_KEY'), model='gpt-4o-mini')


# funtion for history retrieval using redis
def get_message_history(session_id: str) -> RedisChatMessageHistory:
    return RedisChatMessageHistory(session_id, url=os.getenv("REDIS_URL"))


@app.get("/")
async def greet():
    return "Hi, welcome!"


@app.post("/query")
async def answer_query(req: RequestModel):
    try:

        rag_chain = prompt | llm | StrOutputParser()
        with_message_history = RunnableWithMessageHistory(
            rag_chain,
            get_message_history,
            input_messages_key="input",
            history_messages_key="history",
        )
        final_response = await with_message_history.ainvoke(
            {"context": context_retriever(req.query), "input": req.query},
            config={"configurable": {"session_id": req.session_id}},
        )
        return final_response

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sendMail")
async def send_email(email: EmailModel):
    try:
        sender = os.getenv("SENDER")
        password = os.getenv("PASSWORD")
        recipients = os.getenv("RECIPENT")
        subject = email.subject
        email_body = "Chat History with User:\n\n"
        for person, message in email.chat.items():
            email_body += f"{person} - {message}\n"
        email_body += f"\nUser IP Address: {email.ip_address}\n"
        email_body += "\nUser IP Address Information:\n"
        for key, value in email.user_info.items():
            email_body += f"{key} - {value}\n"
        send_gmail(subject, email_body, sender, recipients, password)
        return {"message": f"Email sent successfully to {recipients}"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


# # Tried with chroma
# # vectorstore = Chroma(
# #     collection_name="summaries",
# #     embedding_function=OpenAIEmbeddings(),
# #     persist_directory="chroma_store",
# # )

# # store = InMemoryByteStore()
# # id_key = "doc_id"

# # retriever = MultiVectorRetriever(
# #     vectorstore=vectorstore,
# #     byte_store=store,
# #     id_key=id_key,
# # )

# # with open("docstore.pkl", "rb") as f:
# #     store.store = pickle.load(f)


# # def doc_context(question):
# #     query = question
# #     sub_docs = vectorstore.similarity_search(query, k=1)
# #     print(sub_docs[0])
# #     metadata = sub_docs[0].metadata
# #     doc_id = metadata.get("doc_id")
# #     original_docs = retriever.docstore.store.mget(
# #         [retriever.docstore.key_encoder(doc_id)]
# #     )
# #     print(original_docs[0])
# #     original_doc = original_docs[0]
# #     data = json.loads(original_doc.decode("utf-8"))
# #     context = data["kwargs"]["page_content"]
# #     return context
