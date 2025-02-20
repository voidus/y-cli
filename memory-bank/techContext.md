# Technical Context: y-cli

## Technology Stack

### Core Technologies
- Python 3.x
- Command Line Interface
- JSON for data storage
- MCP (Model Context Protocol)

### Development Tools
- Poetry for dependency management
- UV for package management
- Git for version control

### Key Dependencies
Based on pyproject.toml and project structure:
- Click/Typer (inferred) for CLI framework
- Requests/HTTPX for API calls
- JSON for data serialization
- Type hints for better code quality

## Development Setup

### Environment Requirements
- Python 3.x
- UV package manager
- Git

### Project Structure
```
y-cli/
├── src/
│   ├── bot/           # Bot management
│   ├── chat/          # Chat functionality
│   │   ├── importer/  # Chat import tools
│   │   ├── provider/  # Chat providers
│   │   └── utils/     # Chat utilities
│   ├── cli/           # CLI implementation
│   │   └── commands/  # Command modules
│   └── mcp_server/    # MCP server integration
├── build/             # Build artifacts
└── memory-bank/       # Project documentation
```

## Technical Constraints

### Performance
- CLI response time
- Memory usage
- Storage efficiency
- Network latency handling

### Security
- API key management
- Data persistence security
- Input validation
- Safe error handling

### Compatibility
- Python version compatibility
- OS compatibility (cross-platform)
- Chat provider API versions
- MCP protocol versions

## Dependencies

### Direct Dependencies
- Core Python libraries
- CLI framework
- HTTP client
- JSON handling

### External Services
- Chat providers
  - OpenAI format providers
  - Dify service
  - Topia orchestration
- MCP servers
  - Tool providers
  - Resource providers

## Configuration Management

### System Configuration
- CLI settings
- Provider configurations
- MCP server settings
- Storage locations

### User Configuration
- Bot configurations
- Chat preferences
- Provider credentials
- Custom settings

## Development Practices

### Code Style
- PEP 8 compliance
- Type hints usage
- Docstring documentation
- Clear naming conventions

### Testing
- Unit testing
- Integration testing
- Command testing
- Mock implementations

### Documentation
- Code documentation
- API documentation
- User guides
- Development guides

### Version Control
- Git workflow
- Branch management
- Version tagging
- Change tracking

## Deployment

### Package Distribution
- PyPI packaging
- Version management
- Dependency resolution
- Installation process

### Updates
- Version updates
- Dependency updates
- Configuration updates
- Data migration

## Monitoring & Debugging

### Logging
- Error logging
- Activity logging
- Debug information
- Performance metrics

### Debugging
- Debug modes
- Error tracking
- Performance profiling
- Issue reproduction

## Future Considerations

### Scalability
- Additional providers
- New bot features
- MCP extensions
- Storage scaling

### Maintenance
- Code maintenance
- Dependency updates
- Security patches
- Performance optimization
