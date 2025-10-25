# Personal AI Assistant - LangGraph Agent

## Overview
This is a Personal AI Assistant built with LangGraph that can help with various tasks:
- Writing and sending emails
- Reading and analyzing PDF files  
- Scheduling meetings via Google Calendar
- Searching the internet for information
- Ordering pizzas

The project uses LangGraph for stateful agent orchestration and LangChain for LLM integration with Ollama (local model).

## Current State
- Project imported from GitHub and configured for Replit environment
- All Python dependencies installed
- Ready to run as CLI application

## Recent Changes (October 25, 2025)
- Installed Python 3.11 and all required dependencies
- Created proper requirements.txt with langchain, langgraph, and tool dependencies
- Fixed import paths for running from project root
- Added .gitignore for Python project
- Added GeneralQueryTool to handle unclassified queries
- Created run.py entry point at project root

## Project Architecture

### Structure
```
langgraph-agent/
├── src/
│   ├── agents/          # Agent logic and decision making
│   │   └── base_agent.py
│   ├── tools/           # Tool implementations
│   │   ├── tool_registry.py
│   │   ├── email_manager.py
│   │   ├── pdf_reader.py
│   │   ├── calendar_manager.py
│   │   ├── internet_search.py
│   │   └── pizza_order.py
│   ├── graph/           # State management
│   │   └── state_manager.py
│   ├── privacy/         # Privacy and encryption
│   │   └── privacy_manager.py
│   └── config/          # Configuration
│       └── config.py
└── tests/               # Unit tests
```

### Key Components
- **BaseAgent**: Handles tool selection, uncertainty detection, and clarification
- **StateManager**: Manages LangGraph workflow and state transitions
- **ToolRegistry**: Registers and manages available tools
- **Privacy Manager**: Handles encryption for sensitive data

### Dependencies
- LangChain & LangGraph: Agent framework
- Ollama: Local LLM (mistral model)
- ChromaDB: Vector database for PDF embeddings
- BeautifulSoup4: Web scraping
- Google APIs: Calendar integration
- Cryptography: Data encryption

## Running the Application
The application runs as an interactive CLI:
```bash
python run.py
```

## Notes
- Uses Ollama for local LLM processing (requires Ollama to be running)
- Requires API keys/credentials for:
  - Google Calendar (credentials.json)
  - Email (SMTP settings via .env)
  - Search API (if using external search)
- Privacy-first design with local processing where possible
