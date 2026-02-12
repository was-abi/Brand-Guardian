'''Main execution entry point for Compliance QA Pipeline'''

import uuid
import json, logging
from pprint import pprint

from dotenv import load_dotenv
load_dotenv(override=True)

from backend.src.graph.workflow import app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("brand-guardian-runner")

def run_cli_simulation():
    '''
    Simulates the video compliance audit request'''
    
    #generates the session ID
    session_id = str(uuid.uuid4())
    logger.info(f"Generated session ID: {session_id}")

    #define the initial state for the workflow
    initial_inputs = {
        "video_url": "",
        "video_id": f"vid_{session_id[:8]}",
        "compliance_results": [],
        "errors": []
    }

    print("n.................Initialing workdlow execution.................n")
    print(f"Input Payload : {json.dumps(initial_inputs, indent=2)}")

    try:
        final_state = app.invoke(initial_inputs)
        print("n.................Workflow execution completed.................n")

        print("\n Compliance Audit Report")
        print(f"Video ID: {final_state.get('video_id')}")
        print(f"Status: {final_state.get('final_status')}")
        print("\n [ VIOLATIONS DETECTED]")
        results = final_state.get("compliance_results", [])
        if results:
            for issue in results:
                print(f" - [{issue.get('severity')}] [{issue.get('category')}] [{issue.get('description')}]")
            else:
                print("No violations detected......")
        print("\n [FINAL SUMMARY]")
        print(final_state.get("final_report"))
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        print("Workflow execution failed. Please check the logs for details.")
        raise e

if __name__ == "__main__":
    run_cli_simulation()