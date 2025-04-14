# GermanSongGenerator Crew

Welcome to the GermanSongGenerator Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```

## Docker Support

You can also run this project using Docker. The project includes a Dockerfile for containerized deployment.

### Building the Docker Image

```bash
# From the project root directory
docker build -t german-song-generator .
```

### Running with Docker

The container requires your GROQ API key to function. You can provide it as an environment variable:

```bash
docker run -e GROQ_API_KEY=your_api_key german-song-generator
```

To override the default model:
```bash
docker run -e MODEL=different_model -e GROQ_API_KEY=your_api_key german-song-generator
```

Available commands:
```bash
# Run the main application
docker run german-song-generator

# Run training
docker run german-song-generator train

# Run tests
docker run german-song-generator test
```

### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/german_song_generator/config/agents.yaml` to define your agents
- Modify `src/german_song_generator/config/tasks.yaml` to define your tasks
- Modify `src/german_song_generator/crew.py` to add your own logic, tools and specific args
- Modify `src/german_song_generator/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the german_song_generator Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The german_song_generator Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the GermanSongGenerator Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
