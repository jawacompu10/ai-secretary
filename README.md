# My Personal Secretary

A Python-based personal assistant designed to help manage tasks, meetings, and daily scheduling with intelligent time estimation and learning capabilities.

## 🎯 Project Overview

This project serves as a personal secretary with the following core objectives:

- **Task & Meeting Management**: Keep track of all tasks and meetings
- **Smart Scheduling**: Help organize your day with intelligent time-blocking
- **Time Estimation**: Estimate time required for tasks and learn from actual completion times
- **Continuous Monitoring**: Run on a scheduler with 5-minute check-ins and calendar refresh

## 🏗️ Architecture

### Calendar Integration
- **Self-hosted Calendar**: Uses Radicale for local calendar management
- **Independent Implementation**: Separate calendar system to avoid complex external service integrations
- **Local Storage**: All data stored locally for privacy and reliability

## 🛠️ Technology Stack

### Package Management
- **UV**: Fast Python package manager (superior to pip, faster than Poetry)
- **Dependencies**: Managed through `pyproject.toml`

### Calendar Server
- **Radicale**: Self-hostable calendar server with local filesystem storage
- **Configuration**: No authentication required for local development
- **Data Storage**: Local filesystem-based collections

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- UV package manager

### Installation
1. Clone the repository
2. Install dependencies: `uv sync`
3. Start the Radicale calendar server:
   ```bash
   python3 -m radicale --storage-filesystem-folder=~/.var/lib/radicale/collections --auth-type none
   ```

### Running the Application
```bash
python hello.py
```

## 📋 Features

- **Task Tracking**: Monitor and manage daily tasks
- **Meeting Management**: Keep track of scheduled meetings
- **Time Estimation**: AI-powered time estimation for tasks
- **Learning System**: Improve estimates based on actual completion times
- **Calendar Integration**: Seamless calendar management
- **Continuous Monitoring**: 5-minute check-in intervals

## 🔧 Development

### Project Structure
```
secretary/
├── hello.py          # Main application entry point
├── pyproject.toml    # Project configuration and dependencies
├── uv.lock          # Locked dependency versions
└── README.md        # Project documentation
```

### Dependencies
- See `pyproject.toml` for complete dependency list
- Radicale for calendar functionality
- Additional packages for task management and scheduling

## 📝 License

This is a personal project for individual use.

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome through issues or pull requests.
