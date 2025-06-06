# Installing PlainSpeak

This guide will help you install and set up PlainSpeak on your system.

[![Documentation](https://img.shields.io/badge/docs-online-blue.svg)](https://cschanhniem.github.io/plainspeak/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

For complete and up-to-date documentation, visit [https://cschanhniem.github.io/plainspeak/](https://cschanhniem.github.io/plainspeak/)

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The simplest way to install PlainSpeak is using pip:

```bash
pip install plainspeak
```

PlainSpeak is now available on PyPI: [https://pypi.org/project/plainspeak/](https://pypi.org/project/plainspeak/)

You can also install a specific version:

```bash
pip install plainspeak==1.0.0
```

This will install PlainSpeak and all its dependencies.

### Method 2: Install from Source

If you want the latest development version or want to contribute to PlainSpeak, you can install from source:

1. Clone the repository:
   ```bash
   git clone https://github.com/cschanhniem/plainspeak.git
   cd plainspeak
   ```

2. Install using Poetry (recommended for development):
   ```bash
   # Install Poetry if you don't have it
   pip install poetry

   # Install dependencies and PlainSpeak
   poetry install  # Installs all dependencies including development dependencies

   # To run tests
   poetry run pytest
   ```

3. Alternatively, install using pip:
   ```bash
   pip install -e .  # Installs the package in development mode

   # To install test dependencies
   pip install -r tests/requirements-tests.txt  # Only needed for running tests
   ```

## Setting Up the 'pls' Command

PlainSpeak comes with a user-friendly alias called `pls` for a more conversational experience. To set it up:

1. After installing PlainSpeak, create a symbolic link to make `pls` available:
   ```bash
   # For Linux/macOS users
   mkdir -p "$HOME/bin"
   ln -s "$(which plainspeak)" "$HOME/bin/pls"
   echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc  # or ~/.zshrc for zsh users
   source ~/.bashrc  # or source ~/.zshrc

   # For Windows users (run in PowerShell as Administrator)
   New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\bin\pls.exe" -Target "$(Get-Command plainspeak).Source"
   ```

2. Verify that the `pls` command works:
   ```bash
   pls --version
   ```

The `pls` command provides the same functionality as `plainspeak` but offers a more conversational interface.

## Installing the LLM Model

PlainSpeak requires a language model to function. By default, it looks for a model in the `models/` directory.

1. Create a models directory:
   ```bash
   mkdir -p ~/.config/plainspeak/models
   ```

2. Download a compatible GGUF model (e.g., MiniCPM):
   ```bash
   # Example for MiniCPM 2B
   wget -P ~/.config/plainspeak/models https://huggingface.co/TheBloke/MiniCPM-2B-dpo-GGUF/resolve/main/minicpm-2b-dpo.Q2_K.gguf
   ```

3. Configure PlainSpeak to use the model:
   ```bash
   mkdir -p ~/.config/plainspeak
   cat > ~/.config/plainspeak/config.toml << EOF
   [llm]
   model_path = "~/.config/plainspeak/models/minicpm-2b-dpo.Q2_K.gguf"
   model_type = "llama"
   gpu_layers = 0  # Set to a higher number to use GPU acceleration
   EOF
   ```

## Platform-Specific Instructions

### macOS

1. Install Python 3.11+ using Homebrew:
   ```bash
   brew install python@3.11
   ```

2. Install PlainSpeak:
   ```bash
   pip3 install plainspeak
   ```

3. Set up the `pls` command:
   ```bash
   mkdir -p "$HOME/bin"
   ln -s "$(which plainspeak)" "$HOME/bin/pls"
   echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

### Linux (Ubuntu/Debian)

1. Install Python 3.11+ and dependencies:
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-dev python3-pip
   ```

2. Install PlainSpeak:
   ```bash
   pip3 install plainspeak
   ```

3. Set up the `pls` command:
   ```bash
   mkdir -p "$HOME/bin"
   ln -s "$(which plainspeak)" "$HOME/bin/pls"
   echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Windows

1. Install Python 3.11+ from the [official website](https://www.python.org/downloads/).

2. Install PlainSpeak:
   ```bash
   pip install plainspeak
   ```

3. Set up the `pls` command:
   ```powershell
   # Run in PowerShell as Administrator
   mkdir -p "$env:USERPROFILE\bin"
   New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\bin\pls.exe" -Target "$(Get-Command plainspeak).Source"

   # Add to PATH (one-time command)
   [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$env:USERPROFILE\bin", "User")

   # Refresh current terminal
   $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
   ```

## Verifying Installation

To verify that PlainSpeak is installed correctly:

```bash
plainspeak --version
pls --version  # Both should show the same version
```

This should display the version of PlainSpeak.

## Getting Started

To start using PlainSpeak:

```bash
# Start the interactive shell
plainspeak shell

# Or translate a single command using plainspeak
plainspeak translate "list all files in the current directory"
plainspeak "list all files in the current directory"  # Simplified syntax

# Or use the conversational pls alias
pls "list all files in the current directory"

# List available plugins
plainspeak plugins
```

## Troubleshooting

### Model Not Found

If you see an error like "Model file not found", check that:

1. The model file exists at the path specified in your `config.toml`
2. The model path in `config.toml` is correct
3. You have read permissions for the model file

### GPU Acceleration

To use GPU acceleration:

1. Install the CUDA version of `ctransformers`:
   ```bash
   pip install ctransformers[cuda]
   ```

2. Update your `config.toml` to use GPU layers:
   ```toml
   [llm]
   gpu_layers = 32  # Adjust based on your GPU memory
   ```

### Test Dependencies

If you're running tests and encounter missing dependencies:

1. If using Poetry:
   ```bash
   poetry install  # Installs all dependencies including dev dependencies
   ```

2. If using pip:
   ```bash
   pip install -r tests/requirements-tests.txt
   ```

### Other Issues

If you encounter other issues:

1. Check that all dependencies are installed
2. Ensure you're using Python 3.11 or higher
3. Check the logs in `~/.config/plainspeak/logs` (if available)
4. Report issues on the GitHub repository

## Next Steps

- Read the [`README.md`](README.md) for an overview of PlainSpeak
- Visit the [official documentation](https://cschanhniem.github.io/plainspeak/) for comprehensive guides
- Explore the [plugins directory](plainspeak/plugins) to learn about available plugins
- Try out different natural language commands in the shell
- Check out the [DataSpeak feature](https://cschanhniem.github.io/plainspeak/user/guides/dataspeak.html) (coming soon)
