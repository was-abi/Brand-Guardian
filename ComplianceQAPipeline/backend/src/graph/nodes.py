#define the nodes for the graph
import json
import os
import logging
import re
from typing import List, Dict, Any
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate #defining the prompt
from langchain_core.messages import SystemMessage, HumanMessage

#import state schema
from backend.src.graph.state import VideoAuditState, ComplianceIssue

#import service
from backend.src.services.video_indexer import VideoIndexerService

#configure the logger
logger = logging.getLogger("brand-guardian")
logging.basicConfig(level=logging.INFO)

#Node1: Indexer
#Function responsilbe for converting video to text
def index_video_node(state: VideoAuditState) -> Dict[str, Any]:
    """Downloads the video from the provided URL
    Uploads to the Azure Video Indexer
    extracts the insights"""
    video_url = state.get("video_url")
    video_id = state.get("video_id","video_demo")

    logger.info(f"------[Node: Indexer] Processing: {video_url}")

    local_filename = "temp_audit_video.mp4" #file where your video gets downloaded

    try:
        #instantiate the video indexer service
        vi_service = VideoIndexerService()
        #download: yt-dlp is a powerful video downloader that supports a wide range of websites, including YouTube. It can handle various video formats and resolutions, making it a versatile choice for downloading videos for processing. In this demo, we are only supporting YouTube URLs, but in a production system, you might want to support more sources and use different download strategies based on the URL pattern.
        #download the video if there's  youtube.com or youtu.be in the url
        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path = vi_service.download_youtube_video(video_url, output_path=local_filename)
        else:
            raise Exception("Unsupported video URL. Only YouTube URLs are supported in this demo.")
        #upload the video to Azure Video Indexer
        #this will basically send the video to Azure, where it will be processed and analyzed using Azure's AI capabilities. 
        azure_video_id = vi_service.upload_video(local_path, video_id)
        #then log it under "Upload success"
        logger.info(f"Upload success. Azure ID: {azure_video_id}")

        #cleanup
        if os.path.exists(local_path):
            os.remove(local_path)

        #wait
        #this will basically pause the core, it will keep asking azure "Are you done? Are you done?" every 30 secs until the video is processed.
        #This prevents the code from going forward until the results are ready
        raw_insights = vi_service.wait_for_processing(azure_video_id)

        #extract
        clean_data = vi_service.extract_data(raw_insights)
        logger.info("----Node:Indexer extraction complete----------")
        return clean_data
    except Exception as e:
        logger.error(f"Video Indexer failed: {e}")
        return {
            "errors": [str(e)],
            "final_status": "failed",
            "transcript": "",
            "ocr_text": [],
        }

#Node2: Compliance Auditor node
def audio_content_node(state: VideoAuditState) -> Dict[str, Any]:
    '''
    Performs Retrieval Augmented Generation to audit the content'''
    logger.info("------[Node: Compliance Auditor] querying the knowledge base and LLM------")
    transcript = state.get("transcript","")
    if not transcript:
        logger.warning("No transcript available for auditing.Skipping the audit....")
        return{
            "final_status" : "FAIL",
            "final_report": "Audit failed because video processing failed. (No transcript available)"

        }
    
    #Initialize the Azure clients
    llm = AzureChatOpenAI(
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature = 0.0
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment = "text-embedding-3-small",
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    vector_store = AzureSearch(
        azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key = os.getenv("AZURE_SEARCH_API_KEY"),
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function = embeddings.embed_query #whenever user gives a prompt we want that embedded too
    )

    #RAG Retrieval
    ocr_text = state.get("ocr_text",[])
    query_text = f"{transcript} {' '.join(ocr_text)}"
    docs = vector_store.similarity_search(query_text, k=3)
    retrieved_rules = "\n\n".join([doc.page_content for doc in docs]) #page content is what gets vectorized

    system_prompt = f"""
        You are a senior Brand Compliance Auditor and there are some official regulartory rules that you need to follow
        OFFICIAL REGULATORY RULES:
        {retrieved_rules}
        INSTRUCTIONS:
        1. Analyze the transcript and ocr text below.
        2. Identify if there are any violations in the rules
        3. return strictly json in the following format:
        {{
            "compliance_results: [
            {{
                "category" : "Claim Validation",
                "severity" : "CRITICAL",
                "description" : "Explanation of the violation...",
            }}
            ],
            "status":"FAIL",
            "final_report": "Summary of the audit findings..."
        }}
        If no violations are found, set "status" to "PASS" and "compliance_results" to []. 
        """
    
    user_message = f"""
                    VIDEO_METADATA:{state.get('video_metadata',{})}
                    TRANSCRIPT: {transcript}
                    ONSCREEN_TEXT (OCR): {ocr_text}
                    """
    try: 
        response=llm.invoke([
            SystemMessage(content=system_prompt), 
            HumanMessage(content=user_message)
        ])
        content = response.content
        #Sometimes AI basically tries to write markdowns in backticks, so if there are any such backticks we have to delete them and extract the json inside. This is a common issue when dealing with LLMs, as they often format their responses in markdown for better readability, but in this case, we need to ensure that we are extracting the raw JSON data correctly for further processing.
        if "```" in content:
            content = re.search(r"```(?:json)?(.?)```", content, re.DOTALL).group(1)
        audit_data = json.loads(content.strip())
        return {
            "compliance_results": audit_data.get("compliance_results",[]),
            "final_status": audit_data.get("status","FAIL"),
            "final_report": audit_data.get("final_report","No report generated.")
        }
    except Exception as e:
        logger.error(f"System Error in Auditor Node: {str(e)}")
        #logging the raw response
        logger.error(f"Raw LLM response: {response.content if 'response' in locals() else 'None'}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL",
        }

