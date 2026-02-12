#we have pdfs now they have to be splitted and chunked and stored in the vector database
#this script will read the PDFs from the data folder, split them into chunks, and upload them to Azure AI Search as vectors using the Azure OpenAI Embeddings model.
#
import os
import glob
import logging
from dotenv import load_dotenv
load_dotenv(override=True)

#document loaders and splitters
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

#azure components import
from langchain_openai import AzureOpenAIEmbeddings
from langhcain_community.vectorstores import AzureSearch

#logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger =logging.getLogger("indexer")

def index_docs():
    '''
        reads the PDFs, chunks them, and upload them to Azure AI Search
    '''

    #define paths, we look for data folder

    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(current_dir, "../../backend/data")

    #check for the env variables
    logger.info("="*60)
    logger.info("Checking environment variables...")
    logger.info(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    logger.info(f"AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')}")
    logger.info(f"Embedding Deployment: {os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT','text-embedding-3-small')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {os.getenv('AZURE_SEARCH_INDEX_NAME')}")
    logger.info("="*60)

    #validate the required env variables
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX_NAME"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set the missing environment variables and try again.")
        return

    #Initialize the embedding model: turns text into vectors
    try:
        logger.info("Initializing Azure OpenAI Embeddings...")
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT","text-embedding-3-small"),
            azure_endpoint =  os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key = os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION","2024-12-01-preview")
        )
        logger.info("Azure OpenAI Embeddings initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize the Embeddings: {e}")
        logger.error("Please verify the Azure OpenAI deplyment name and endpoint")
        return

    #Inititalize the azure search 
    try:
        logger.info("Initializing Azure AI Search Vector Store...")
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
        vector_store = AzureSearch(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key =  os.getenv("AZURE_SEARCH_API_KEY"),
            index_name = index_name,
            embedding_function = embeddings.embed_query
        )
        logger.info(f"Vector store initialized for the index:{index_name}")
    except Exception as e:
        logger.error(f"Failed to inititalize Azure Search: {e}")
        logger.error("Please verify the Azure Search endpoint, index name and API key")
        return


    #Find pdf files
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in the data folder: {data_folder}")
        return
    logger.info(f"Found {len(pdf_files)} PDF files in the data folder.")

    all_splits = []
    for pdf_path in pdf_files:
        try:
            logger.info(f"Loading: {os.path.basename(pdf_path)}")
            #Load the PDF
            loader = PyPDFLoader(pdf_path)
            raw_docs = loader.load()
            logger.info(f"Loaded {len(raw_docs)} pages from {pdf_path}")

            #Split the documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200) #single chunk of 1000 characters with 200 characters overlap
            splits = text_splitter.split_documents(raw_docs)
            for split in splits:
                split.metadata["source"] = os.path.basename(pdf_path) #add source metadata
            all_splits.extend(splits)
            logger.info(f"Split into {len(splits)} chunks for {pdf_path}")
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
    
    #Upload to Azure
    if all_splits:
        logger.info(f"Uploading {len(all_splits)} chunks to Azure AI Search Index: {index_name}...")
        try:
            #azure search accepts batches automatically via this method
            vector_store.add_documents(documents = all_splits)
            logger.info("="*60)
            logger.info(f"Successfully indexed {len(all_splits)} chunks to Azure AI Search Index: {index_name}, Knowledge base is ready for question answering!")
            logger.info("="*60)
        except Exception as e:
            logger.error(f"Failed to upload documents to Azure Search: {e}")
            logger.error("Please verify the Azure Search index configuration and retry")
    else:
        logger.warning("No document chunks to upload to Azure Search.")

if __name__ == "__main__":
    index_docs()
