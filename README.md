# My Personal Secretary

A Python-based personal assistant designed to help manage tasks, meetings, and daily scheduling with intelligent time estimation and learning capabilities.

## 🎯 Project Overview

This project serves as a personal secretary with the following core objectives:

- **Task & Meeting Management**: Keep track of all tasks and meetings
- **Smart Scheduling**: Help organize your day with intelligent time-blocking
- **Time Estimation**: Estimate time required for tasks and learn from actual completion times
- **Continuous Monitoring**: Run on a scheduler with 5-minute check-ins and calendar refresh
- **AI-Powered Assistance**: Intelligent task management and productivity recommendations

## 🏗️ Architecture

### Calendar Integration
- **Self-hosted Calendar**: Uses Radicale for local calendar management
- **CalDAV Protocol**: Standard calendar protocol for connecting to calendar services
- **Independent Implementation**: Separate calendar system to avoid complex external service integrations
- **Local Storage**: All data stored locally for privacy and reliability

### AI Agent
- **OpenAI Integration**: Uses OpenAI Agents for intelligent task management
- **Tool-Based Architecture**: Agent has access to task and calendar management tools
- **Learning System**: Improves recommendations based on historical data
- **Productivity Analysis**: Provides insights and recommendations

## 🛠️ Technology Stack

### Package Management
- **UV**: Fast Python package manager (superior to pip, faster than Poetry)
- **Dependencies**: Managed through `pyproject.toml`

### Configuration Management
- **Dynaconf**: Dynamic configuration management with multiple environment support
- **Settings**: Environment-specific configurations (development, production, testing)
- **Security**: Secure handling of sensitive configuration data

### Calendar Server
- **Radicale**: Self-hostable calendar server with local filesystem storage
- **CalDAV**: Standard protocol for calendar access and synchronization
- **Configuration**: No authentication required for local development
- **Data Storage**: Local filesystem-based collections

### AI & Machine Learning
- **OpenAI Agents**: Intelligent task management and recommendations
- **GPT-4o-mini**: Cost-effective language model for productivity assistance
- **Tool Integration**: Seamless access to task and calendar data

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- UV package manager
- OpenAI API key (optional, for AI features)

### Installation
1. Clone the repository
2. Install dependencies: `uv sync`
3. Configure Dynaconf settings (see Configuration section below)
4. Start the Radicale calendar server:
   ```bash
   python3 -m radicale --storage-filesystem-folder=~/.var/lib/radicale/collections --auth-type none
   ```

### Configuration
The application uses Dynaconf for configuration management:

```bash
# Create configuration files
touch .secrets.toml
touch settings.toml
```

Example configuration structure:
```toml
# settings.toml
[default]
calendar_url = "http://localhost:5232"
openai_api_key = "your-openai-api-key-here"  # Optional
check_interval = 300  # 5 minutes in seconds

[development]
debug = true

[production]
debug = false
```

### Running the Application

#### Main Application
```bash
python main.py
```

#### Command Line Interface
The application includes a comprehensive CLI for task management and AI assistance:

```bash
# Basic task management
python cli.py list                    # List all tasks
python cli.py list --status PENDING   # List pending tasks only
python cli.py add "Review docs" --description "Go through documentation" --due "2024-01-15 14:00" --category "work"
python cli.py complete 1 --duration 45
python cli.py status                  # Show system status
python cli.py sync                    # Sync with calendar

# AI Agent commands (requires OpenAI API key)
python cli.py chat "What should I work on next?"           # Chat with AI agent
python cli.py summary                                      # Get intelligent summary
python cli.py analyze --days 7                             # Analyze productivity
python cli.py recommend                                    # Get recommendations
```

## 📋 Features

- **Task Tracking**: Monitor and manage daily tasks
- **Meeting Management**: Keep track of scheduled meetings
- **Time Estimation**: AI-powered time estimation for tasks
- **Learning System**: Improve estimates based on actual completion times
- **Calendar Integration**: Seamless CalDAV calendar management
- **Configuration Management**: Environment-specific settings with Dynaconf
- **Continuous Monitoring**: 5-minute check-in intervals
- **Command Line Interface**: Easy task management via CLI
- **AI-Powered Assistance**: Intelligent task management and recommendations
- **Productivity Analysis**: Insights and personalized recommendations
- **Natural Language Interface**: Chat with the AI agent for task management

## 🔧 Development

### Project Structure
```
secretary/
├── main.py              # Main application entry point
├── cli.py               # Command line interface
├── config.py            # Dynaconf configuration setup
├── settings.toml        # Application configuration
├── .secrets.toml        # Sensitive configuration (gitignored)
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Locked dependency versions
├── secretary/           # Main package
│   ├── __init__.py     # Package initialization
│   ├── calendar_manager.py  # CalDAV calendar operations
│   ├── task_manager.py      # Task management and learning
│   ├── scheduler.py         # Main scheduler and coordination
│   └── agent.py             # AI agent for intelligent assistance
└── README.md           # Project documentation
```

### Dependencies
- See `pyproject.toml` for complete dependency list
- **Radicale**: Self-hosted calendar server
- **CalDAV**: Calendar protocol implementation
- **Dynaconf**: Configuration management
- **OpenAI Agents**: AI-powered task management
- Additional packages for task management and scheduling

### Configuration Management
- **Dynaconf**: Handles multiple environments (development, production, testing)
- **Environment Variables**: Support for environment-based configuration
- **Secret Management**: Secure handling of API keys and sensitive data
- **Validation**: Configuration validation and type checking

### AI Agent Tools
The AI agent has access to the following tools:
- **Task Management**: Create, list, complete, and estimate task duration
- **Calendar Integration**: Get events and tasks from calendar
- **Productivity Analysis**: Analyze patterns and provide insights
- **Recommendations**: Personalized productivity recommendations

## 📝 License

This is a personal project for individual use.

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome through issues or pull requests.
