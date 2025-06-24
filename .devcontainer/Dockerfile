# APEX Development Container
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        build-essential \
        curl \
        git \
        sudo \
        vim \
        tmux \
        htop \
        tree \
        jq \
        netcat \
        procps \
        lsof \
        strace \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and Claude Code
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @anthropic-ai/claude-code

# Install UV package manager
RUN pip install uv

# Set up workspace directory
WORKDIR /workspace

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock* ./
RUN uv sync --dev

# Install APEX in development mode
RUN uv pip install -e .

# Create APEX directories
RUN mkdir -p /workspace/.apex/{lmdb,logs,claude,config,shared/{tasks,code,issues,status}}

# Set up Git configuration for container
RUN git config --global --add safe.directory /workspace

# Create non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Set ownership of workspace
RUN chown -R $USERNAME:$USERNAME /workspace

USER $USERNAME

# Set up shell environment
RUN echo 'export PATH="/workspace/.venv/bin:$PATH"' >> ~/.bashrc \
    && echo 'alias ll="ls -la"' >> ~/.bashrc \
    && echo 'alias apex="python -m apex.cli"' >> ~/.bashrc

# Expose ports for services
EXPOSE 8000 8001 8002

CMD ["sleep", "infinity"]
