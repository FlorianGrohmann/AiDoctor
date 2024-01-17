from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.prompts import PromptTemplate
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
import chainlit as cl
from oobabooga import Oobabooga

DB_FAISS_PATH = 'aidoctor/db_faiss'

custom_prompt_template = """Sie sind ein medizinischer Bot, der dazu verwendet wird, Informationen aus der Frage des Benutzers zu erfassen und sie klinisch und klar zu beantworten.
Verwenden Sie die folgenden Informationen, um die Frage des Benutzers zu beantworten. Wenn die Informationen nicht zur Frage passen, ignorieren Sie sie einfach.

Kontext: {context}
Frage: {question}

Geben Sie nur die hilfreiche Antwort die einen Einblick in das Problem erschafft zurück und nichts anderes.
Unterlassen Sie Tipps wie der Patient soll einen Arzt aufsuchen, Sie sind der Arzt. Es geht ausschließlich um eine Erstdiagnose.
Hilfreiche Antwort:
"""

def set_custom_prompt():
    """
    Prompt template for QA retrieval for each vectorstore
    """
    prompt = PromptTemplate(template=custom_prompt_template,
                            input_variables=['context', 'question'])
    return prompt

#Retrieval QA Chain
def retrieval_qa_chain(llm, prompt, db):
    qa_chain = RetrievalQA.from_chain_type(llm=llm,
                                       chain_type='stuff',
                                       retriever=db.as_retriever(search_kwargs={'k': 2}),
                                       return_source_documents=True,
                                       chain_type_kwargs={'prompt': prompt}
                                       )
    return qa_chain

#Loading the model
def load_llm():
    # Load the locally downloaded model here
    llm = Oobabooga(url="http://64.247.206.234:19695/v1/completions", model_name="oobabooga")
    return llm

#QA Model Function
def qa_bot():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    db = FAISS.load_local(DB_FAISS_PATH, embeddings)
    llm = load_llm()
    qa_prompt = set_custom_prompt()
    qa = retrieval_qa_chain(llm, qa_prompt, db)

    return qa

#output function
def final_result(query):
    qa_result = qa_bot()
    response = qa_result({'query': query})
    return response

#chainlit code
@cl.on_chat_start
async def start():
    chain = qa_bot()
    msg = cl.Message(content="Starting the bot...")
    await msg.send()
    msg.content = "Hallo, willkommen bei Medical Bot. Was ist Ihre Anfrage?"
    await msg.update()

    cl.user_session.set("chain", chain)

@cl.on_message
async def main(message: cl.Message):
    chain = cl.user_session.get("chain") 
    cb = cl.AsyncLangchainCallbackHandler(
        stream_final_answer=True, answer_prefix_tokens=["FINAL", "ANSWER"]
    )
    cb.answer_reached = True
    res = await chain.acall(message.content, callbacks=[cb])
    answer = res["result"]
    sources = res["source_documents"]

    if sources:
        answer += f"\nSources:" + str(sources)
    else:
        answer += "\nNo sources found"

    await cl.Message(content=answer).send()

