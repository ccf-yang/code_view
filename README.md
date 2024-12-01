# AI-Powered Code Viewer

A powerful code viewing and analysis tool that supports intelligent code parsing with multiple AI models.

## Features

### File System Navigation
- Dynamic directory and file listing
- Recursive directory browsing
- Real-time file content loading
- Hierarchical file tree display

### AI Code Analysis
- Multiple AI model support:
  - Novita AI (qwen/qwen-2-72b-instruct)
  - Zhipu AI (glm-4-plus)
- Chinese code explanations
- Automatic and manual analysis modes

### Analysis Persistence
- Save/load AI analysis results
- Editable analysis area
- Keyboard shortcut support (Ctrl+S)

### User Interface
- Elegant notification system
- Current file path display
- AI model selection
- Local directory and Git repository support (coming soon)

## Quick Start

1. Install Dependencies
```bash
pip install fastapi uvicorn openai zhipuai
```

2. Configure API Keys
- Novita AI key is pre-configured
- Configure Zhipu AI key (ZHIPU_API_KEY) in server.py

3. Start Server
```bash
python server.py
```

4. Access in Browser
```
http://localhost:8000
```

## Usage Guide

1. Input Project Path
   - Select input type (Local Directory/Git Repository)
   - Enter path or URL
   - Click "Load Project" or "Clone and Load"

2. Browse Code
   - Click directory to expand/collapse
   - Click file to view content
   - Current file path shown at top

3. AI Analysis
   - Select desired AI model
   - Click "AI Analysis" button
   - Wait for analysis generation

4. Save Analysis
   - Auto-save is disabled
   - Click "Save Analysis" button manually
   - Or use Ctrl+S shortcut

## Tech Stack

- Backend: Python (FastAPI)
- Frontend: Vanilla JavaScript
- AI: Novita AI, Zhipu AI

## Notes

- Requires Python 3.8+
- Internet connection required for AI services
- Git repository feature in development
- .ai files are filtered in directory listings

## Roadmap

- [ ] Git repository cloning
- [ ] Additional AI model integration
- [ ] Configuration file support
- [ ] Performance optimization
- [ ] Additional file type support

## Contributing

Issues and Pull Requests are welcome to help improve the project!
