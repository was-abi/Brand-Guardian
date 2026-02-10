import operator
from typing import Annotated, Dict, List, Optional, Any, TypedDict

#Langgraph graph is TypedDict

#Schema for a single xompliance result
#Wehave yt brand ad videos, video is combo of text, speech, image
#url -> downlloaded cideo -> azure blob storage

#Error report
#If error report gets generated then this is how its going to look like
#If there is any violation or any issue then it is going to flag it under these 4 parameters
class ComplianceIssue(TypedDict):
    category: str #e.g ftc disclosure
    description: str #specific detail of violation
    severity: str #CRITICAL or WARNING
    timestamp: Optional[str]

#define global graph state
#This class defines state that gets passed around from one state to other in agentic workflow
class VideoAuditState(TypedDict):
    """Defines the data schema for langgraph execution content.
    Its a main container that holds the information about the audit right from the initial url to the report """
    #input parameters it will take required to start the process
    video_url: str
    video_id: str

    #ingestions and extraction data
    #These fields act as placeholder for the data that we are going to extract from the video
    local_file_path: Optional[str]
    video_metadata: Dict[str, Any] #{duration: 120, resolution: '1080p'}
    transript: Optional[str] #Fully extracted speech to text
    ocr_text : List[str] #list of text extracted from video frames

    #analysis output
    #stores the list of all the violations found by the AI
    #When a new issue is found it will keep on appending the compliance issue to the list which is called compliance result
    compliance_results : Annotated[List[ComplianceIssue],operator.add]

    #final deliverables
    #final decision the user sees in the termina
    final_status: str #PASS | FAIL
    final_report: Optional[str]

    #system observability
    #errors or api timeouts or system level errors then we are going to take that into consideration
    #stores the list of all the system level crashes or errors that happened during the process
    errors: Annotated[List[str], operator.add]