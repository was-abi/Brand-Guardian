'''
Connector: Python and Azure Video Indexer
'''
import os, time, logging, requests
import yt_dlp
from azure.identity import DefaultAzureCredential

logger = logging.getLogger("video_indexer")

class VideoIndexerService:
    def __init__(self):
        self.account_id = os.getenv("AZURE_VI_ACCOUNT_ID")
        self.location = os.getenv("AZURE_VI_LOCATION")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        self.vi_name = os.getenv("AZURE_VI_NAME")
        self.credential = DefaultAzureCredential()
    
    def get_access_token(self):
        '''
            Get the access token for Azure Video Indexer API using Azure AD credentials.
            Generates an ARM Access token 
            Without this you wont be able to establish a connection between your python/VScode and Azure VI Indexer, wont be able to communicate with it
        '''
        try:
            token_object = self.credential.get_token("https://management.azure.com/.default")
            return token_object.token
        except Exception as e:
            logger.error(f"Failed to obtain access token: {e}")
            raise
    
    def get_account_token(self, arm_access_token):
        """Exchanges ARM token for Video Indexer Account Token."""
        url = (
            f"https://management.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.VideoIndexer/accounts/{self.vi_name}"
            f"/generateAccessToken?api-version=2024-01-01"
        )
        headers = {"Authorization": f"Bearer {arm_access_token}"}
        payload = {"permissionType": "Contributor", "scope": "Account"}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to get VI Account Token: {response.text}")
        return response.json().get("accessToken")
    
    #function to download the youtube video
    def download_yt_video(self, url, output_path = "temp_video.mp4"):
        '''
            Downloads the YouTube video using yt_dlp library and saves it to the specified output path.
            downloads youtube video to a local file
        '''

        logger.info(f"Downloading video from URL: {url}")
        
        ydl_opts = {
            'format': "best[ext=mp4]",
            'outtmpl': output_path,
            'quiet': True,
            'overwrites': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info(f"Video downloaded successfully to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            raise
    
    #Upload the video to Azure Video Indexer
    def upload_video(self, video_path, video_name):
        '''
            Uploads the video to Azure Video Indexer using the account token for authentication.
            Returns the video ID assigned by Azure VI after successful upload.
        '''
        arm_token = self.get_access_token()
        vi_token = self.get_account_token(arm_token)

        api_url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"

        params = {
            "accessToken": vi_token,
            "name": video_name,
            "privacy": "Private",
            "indexingPreset": "Default"
        }

        logger.info(f"Uploading video {video_path} to Azure Video Indexer: {video_name}")

        #open the file in binary and stream it on azure
        with open(video_path, "rb") as video_file:
            files = {"file":video_file}
            response = requests.post(api_url, params=params, files=files)

        if response.status_code != 200:
            logger.error(f"Failed to upload video: {response.text}")
            raise Exception(f"Failed to upload video: {response.text}")
    
    def wait_for_processing(self, video_id):
        logger.info(f"Waiting for video processing to complete for video ID: {video_id}")
        while True:
            arm_token = self.get_access_token()
            vi_token = self.get_account_token(arm_token)
            
            url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"
            params = {"accessToken": vi_token}
            response = requests.get(url, params=params)
            data = response.json()

            state = data.get("state")
            if state == "Processed":
                return data
            elif state == "Failed":
                raise Exception(f"Video processing failed for video ID: {video_id}")
            elif state == "Quarantined": #if there a copyuright/ Content policy violation, the video gets quarantined and wont be processed, you need to check the video and remove the violation and reupload
                raise Exception(f"Video is quarantined for video ID: {video_id}")
            logger.info(f"Status {state} ............. wainting for 30 seconds before next check")
            time.sleep(30)
    
    def extract_data(self, vi_json):
        '''
        passes the JSON into our state format
        from the entire json file we only want the transcript
        we only want the text from the transcript, we can ignore the timestamps and other metadata for now
        ocr text too same thing'''
        transcript_lines= []
        for v in vi_json.get("videos", []):
            for insight in v.get("insights",{}).get("(Transcript", []):
                transcript_lines.append(insight.get("text"))

        ocr_lines = []
        for v in vi_json.get("videos", []):
            for insight in v.get("insights",{}).get("ocr", []):
                ocr_lines.append(insight.get("text"))
        
        return {
            "transcript": "".join(transcript_lines),
            "ocr_text": ocr_lines,
            "video_metadata": {
                "duration": vi_json.get("summarizedInsights", {}).get("duration"),
                "platform" : "youtube"
            }
        }
        

    
    
            