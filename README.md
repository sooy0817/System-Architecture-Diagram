# Diagram Agent

An AI-powered diagram generation and management system that creates intelligent, interactive diagrams from structured data and natural language descriptions.

## Features

- **Intelligent Diagram Generation**: Automatically create diagrams from data inputs
- **Multi-Step Workflow**: Structured process from session initialization to export
- **Entity Extraction**: Advanced NLP-based entity and relationship extraction
- **Graph Processing**: Sophisticated graph analysis and structure matching
- **Multiple Export Formats**: Support for JSON, SVG, PNG, PDF, and Mermaid formats
- **RESTful API**: Complete API for integration with other systems
- **Extensible Architecture**: Modular design for easy customization and extension

## Architecture

The system is built with a modular architecture consisting of:

### Core Components

- **API Layer** (`api/`): FastAPI-based REST endpoints
- **Core Services** (`core/`): Configuration, logging, and external service clients
- **Graph Engine** (`graph/`): State management, building, and routing logic
- **Processing Nodes** (`nodes/`): Individual workflow step implementations
- **Data Extraction** (`extract/`): Entity extraction and pattern matching
- **Schemas** (`schemas/`): Data models and validation

### Workflow Steps

1. **Session Initialization**: Create and configure diagram sessions
2. **Data Prefilling**: Populate initial data structures
3. **Corporate Center**: Process organizational data
4. **Networks**: Configure network topologies
5. **Zone Details**: Define security and organizational zones
6. **User Management**: Handle user entities and permissions
7. **Edge Processing**: Create relationships and connections
8. **Composition**: Assemble diagram elements
9. **Review**: Validate and optimize diagram structure
10. **Export**: Generate final outputs in various formats

## Installation

### Prerequisites

- Python 3.8 or higher
- pip or poetry for package management

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/diagram-agent/diagram-agent.git
cd diagram-agent

# Install dependencies
pip install -e .
```

### Development Installation

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Optional Dependencies

```bash
# Machine Learning features
pip install -e ".[ml]"

# Graph database support
pip install -e ".[graph]"

# Advanced export formats
pip install -e ".[export]"

# Monitoring and observability
pip install -e ".[monitoring]"
```

## Quick Start

### 1. Start the API Server

```bash
# Using the CLI
diagram-agent

# Or directly with uvicorn
uvicorn diagram_agent.app.main:app --host 0.0.0.0 --port 8000
```

### 2. Create a Session

```bash
curl -X POST "http://localhost:8000/api/sessions/" \
  -H "Content-Type: application/json" \
  -d '{"name": "My First Diagram", "description": "A test diagram"}'
```

### 3. Execute Workflow Steps

```bash
# Initialize session
curl -X POST "http://localhost:8000/api/steps/{session_id}/steps" \
  -H "Content-Type: application/json" \
  -d '{"step_type": "init_session", "input_data": {"timestamp": "2024-01-01T00:00:00Z"}}'

# Add more steps as needed...
```

### 4. Export Diagram

```bash
curl -X POST "http://localhost:8000/api/export/{session_id}/export" \
  -H "Content-Type: application/json" \
  -d '{"format": "mermaid", "options": {}}'
```

## Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=sqlite:///./diagram_agent.db

# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# External Services
LANGFUSE_PUBLIC_KEY=your_key_here
LANGFUSE_SECRET_KEY=your_secret_here

# GLiNER Model
GLINER_MODEL_NAME=urchade/gliner_base
```

## API Documentation

Once the server is running, visit:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## Development

### Project Structure

```
diagram-agent/
├── diagram_agent/app/          # Main application
├── api/                        # API endpoints
├── core/                       # Core services
├── graph/                      # Graph processing
├── nodes/                      # Workflow nodes
├── extract/                    # Data extraction
├── schemas/                    # Data models
├── tests/                      # Test suite
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=diagram_agent

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# Run all quality checks
pre-commit run --all-files
```

## Usage Examples

### Python API

```python
from diagram_agent.graph.build import graph_builder
from diagram_agent.graph.state import NodeType

# Create a new graph
session_id = "example_session"
graph = graph_builder.create_graph(session_id)

# Add nodes
user_node = graph_builder.add_node(session_id, NodeType.USER, {
    "name": "John Doe",
    "role": "Developer"
})

org_node = graph_builder.add_node(session_id, NodeType.CORP_CENTER, {
    "name": "Tech Corp",
    "department": "Engineering"
})

# Connect nodes
graph_builder.connect_nodes(session_id, user_node.id, org_node.id)
```

### Entity Extraction

```python
from diagram_agent.extract.candidate_extractor import candidate_extractor

data = {
    "users": [{"name": "Alice", "role": "Manager"}],
    "organizations": [{"name": "ACME Corp", "type": "Technology"}]
}

candidates = candidate_extractor.extract_candidates(data)
print(candidates)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints throughout the codebase
- Ensure all tests pass before submitting PRs

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [https://diagram-agent.readthedocs.io](https://diagram-agent.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/diagram-agent/diagram-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/diagram-agent/diagram-agent/discussions)

## Roadmap

- [ ] Advanced ML-based diagram optimization
- [ ] Real-time collaborative editing
- [ ] Plugin system for custom node types
- [ ] Integration with popular diagramming tools
- [ ] Advanced graph algorithms and analysis
- [ ] Cloud deployment templates
- [ ] Mobile-responsive web interface

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Entity extraction powered by [GLiNER](https://github.com/urchade/GLiNER)
- Graph processing with [NetworkX](https://networkx.org/)
- Monitoring with [Langfuse](https://langfuse.com/)