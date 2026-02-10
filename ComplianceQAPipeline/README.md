# Compliance QA Pipeline

A comprehensive video compliance auditing system that analyzes YouTube advertisements against regulatory guidelines and generates compliance reports.

## Project Overview

This system takes a YouTube video URL, downloads the video, processes it through Azure Video Indexer to extract transcripts and OCR data, performs vector search against regulatory documents, and uses AI to generate compliance reports indicating whether the video meets regulatory requirements.

## Architecture

![Architecture Diagram](attachment:2339ce3b-ab43-4a18-b369-1fcd9b425994:image.png)

## Technology Stack

### Backend
- **FastAPI**: Primary backend framework
- **Python**: Main programming language

### Azure Services
- **Azure Blob Storage**: Video file storage
- **Azure Video Indexer**: Transcript and OCR extraction
- **Azure AI Search**: Vector database for regulatory documents
- **Azure Application Insights**: Monitoring and logging

### AI/ML
- **Azure OpenAI**: LLM for compliance analysis
- **Azure OpenAI Embeddings**: Vector embeddings for search

### Development Tools
- **LangGraph**: Agentic workflow orchestration
- **LangSmith**: Observability and debugging

## Core Workflow

1. **Video Input**: User provides YouTube video URL
2. **Video Download**: Python script downloads the video
3. **Video Processing**: 
   - Video sent to Azure Video Indexer
   - Extracts transcript and OCR (text in video)
4. **Regulatory Document Processing**:
   - PDF documents are indexed
   - Vector embeddings created for search
5. **Vector Search**: Find relevant regulatory pages based on video content
6. **Compliance Analysis**: 
   - GPT compares video content with regulations
   - Identifies violations or misleading claims
7. **Report Generation**: PASS/FAIL verdict with detailed summary
8. **Monitoring**: Track all operations through Application Insights and LangSmith

## Key Components

### Video Processor
- Downloads YouTube videos
- Sends to Azure Video Indexer
- Receives transcript and OCR data
- Stores processed video in Azure Blob Storage

### Retrieval Engine
- Uses Azure AI Search (vector database)
- Performs hybrid vector search
- Retrieves relevant regulatory document pages
- Matches video content with regulatory requirements

### Compliance Auditor
- Uses Azure OpenAI LLM
- Compares video transcript with regulations
- Identifies violations and misleading claims
- Generates detailed compliance reports

### Monitoring System
- **Azure Application Insights**: Tracks errors, latency, user activity
- **LangSmith**: Traces agentic workflow, debugging
- Provides live maps and health checks

## Installation & Setup

### Prerequisites
- Python 3.8+
- Azure subscription
- YouTube API credentials
- Azure OpenAI API key

### Setup Steps
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Set up Azure services
5. Run the application: `python main.py`

## Usage Guide

### Basic Usage
1. Start the FastAPI server
2. Send POST request with YouTube URL
3. Receive compliance report

### API Endpoints

#### POST /audit-video
- **Description**: Initiate video compliance audit
- **Request**: `{ "video_url": "https://youtube.com/watch?v=..." }`
- **Response**: Compliance report with PASS/FAIL verdict

#### GET /status/{job_id}
- **Description**: Check audit status
- **Response**: Current status and progress

#### GET /report/{job_id}
- **Description**: Retrieve final compliance report
- **Response**: Detailed compliance analysis

## Monitoring & Observability

### Azure Application Insights
- Tracks all system operations
- Monitors errors and latency
- Provides live operational maps
- Health checks and diagnostics

### LangSmith
- Traces agentic workflow execution
- Shows information flow to LLM
- Debugs incorrect responses
- Monitors throughput and performance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository.