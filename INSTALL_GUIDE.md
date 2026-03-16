# Reference Toolkit - Installation Guide

**Platform-Specific Instructions for Windows, macOS, and Linux**

Complete guide for installing and running the Reference Toolkit on your operating system using Docker or native Python installation.

---

## 📋 Quick Reference

| Platform | Docker | Native Python | Difficulty |
|----------|--------|---------------|------------|
| **Windows** | ✅ Recommended | ✅ Supported | Docker: Easy | Native: Medium |
| **macOS** | ✅ Recommended | ✅ Supported | Docker: Easy | Native: Easy |
| **Linux** | ✅ Supported | ✅ Recommended | Docker: Easy | Native: Easy |

---

## ⚙️ Configuration

### Required: Email Address

The Reference Toolkit requires an email address for API usage. Most academic APIs (Crossref, PubMed, etc.) require this for polite usage and rate limiting.

**Methods to provide email:**

1. **CLI Argument** (Recommended for one-time use):
```bash
# Any platform
reftool search "query" --mailto your-email@example.com

# Docker
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool search "query" --mailto your-email@example.com
```

2. **Environment Variable** (Recommended for regular use):
```bash
# Linux/macOS
export REFERENCETOOLKIT_EMAIL=your-email@example.com
reftool search "query"

# Windows PowerShell
$env:REFERENCETOOLKIT_EMAIL="your-email@example.com"
reftool search "query"

# Windows Command Prompt
set REFERENCETOOLKIT_EMAIL=your-email@example.com
reftool search "query"
```

3. **Configuration File** (.env):
```bash
# Copy example file
cp .env.example .env

# Edit .env and add your email
# REFERENCETOOLKIT_EMAIL=your-email@example.com

# Load environment variables
source .env  # Linux/macOS
# Or use a tool like python-dotenv
```

### Optional Configuration

**Proxy Settings** (for institutional access):
```bash
# Environment variables
export UNPAYWALL_PROXY_URL=http://proxy.institution.edu:8080
export UNPAYWALL_PROXY_USERNAME=your-username
export UNPAYWALL_PROXY_PASSWORD=your-password
```

**Rate Limiting**:
```bash
# Adjust API call timing (default: 0.5 seconds)
export REFERENCETOOLKIT_SLEEP_TIME=1.0
```

**Timeout Settings**:
```bash
# Adjust request timeout (default: 30 seconds)
export REFERENCETOOLKIT_TIMEOUT=60
```

---

## 🪟 Windows Installation

### Method 1: Docker (Recommended)

#### Prerequisites
- Windows 10/11 Pro, Enterprise, or Education
  - Or Windows 10/11 Home with WSL 2
- Docker Desktop for Windows
- 4GB+ RAM available for Docker

#### Installation Steps

**1. Install Docker Desktop**
```powershell
# Download from: https://www.docker.com/products/docker-desktop
# Run installer with default settings
# Restart computer when prompted
```

**2. Verify Docker Installation**
```powershell
# Open PowerShell or Command Prompt
docker --version
docker-compose --version
```

**3. Pull or Build Reference Toolkit**
```powershell
# Option A: Pull from Docker Hub (when available)
docker pull tamoghna12/reference-toolkit:latest

# Option B: Build from source
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
docker build -t reference-toolkit:latest .
```

**4. Run Reference Toolkit**
```powershell
# Basic usage
docker run --rm -v ${PWD}:/data reference-toolkit:latest reftool --help

# Search for papers
docker run --rm -v ${PWD}:/data reference-toolkit:latest reftool search "CRISPR" --limit 10

# Rename PDFs
docker run --rm -v ${PWD}\pdfs:/data reference-toolkit:latest reftool rename /data
```

**5. Using Docker Compose (Easier)**
```powershell
# Navigate to project directory
cd reference-toolkit

# Start services
docker-compose up -d

# Run commands
docker-compose run run reftool search "machine learning" --limit 5

# Stop when done
docker-compose down
```

#### Windows-Specific Considerations

**Path Handling**:
```powershell
# Use forward slashes in Docker commands
docker run --rm -v C:/Users/YourName/pdfs:/data reference-toolkit:latest reftool rename /data

# Or use ${PWD} for current directory
docker run --rm -v ${PWD}:/data reference-toolkit:latest reftool search "query"
```

**PowerShell vs Command Prompt**:
```powershell
# PowerShell (recommended)
docker run --rm -v ${PWD}:/data reference-toolkit:latest reftool --help

# Command Prompt
docker run --rm -v %cd%:/data reference-toolkit:latest reftool --help
```

**Windows Defender**: Add Docker Desktop to exclusions if experiencing performance issues.

---

### Method 2: Native Python Installation

#### Prerequisites
- Windows 10/11
- Python 3.10 or later
- Administrator access (for installation)

#### Installation Steps

**1. Install Python**
```powershell
# Download from: https://www.python.org/downloads/
# Python 3.10+ recommended
# During installation:
#   ✅ Check "Add Python to PATH"
#   ✅ Check "Install for all users" (optional)

# Verify installation
python --version
pip --version
```

**2. Install Visual C++ Build Tools** (Required for some packages)
```powershell
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Install "Desktop development with C++" workload
# Or install build tools only
```

**3. Install Reference Toolkit**
```powershell
# Option A: From PyPI (when available)
pip install reference-toolkit

# Option B: From source
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
pip install -e .

# Option C: With development dependencies
pip install -e ".[dev]"
```

**4. Verify Installation**
```powershell
reftool --help
reftool search --help
reftool rename --help
```

**5. Run Reference Toolkit**
```powershell
# Search for papers
reftool search "CRISPR gene editing" --limit 10 --output results.csv

# Resolve references
reftool resolve refs.txt --output resolved.csv

# Download PDFs
reftool download resolved.csv --download-dir pdfs

# Rename PDFs
reftool rename C:\Users\YourName\Documents\pdfs --dry-run
```

#### Windows-Specific Troubleshooting

**Issue: Python not in PATH**
```powershell
# Fix: Reinstall Python with "Add to PATH" checked
# Or manually add to PATH:
# 1. Search "Environment Variables" in Windows
# 2. Edit PATH variable
# 3. Add: C:\Users\YourName\AppData\Local\Programs\Python\Python310\
# 4. Add: C:\Users\YourName\AppData\Local\Programs\Python\Python310\Scripts\
```

**Issue: Permission Denied**
```powershell
# Run PowerShell as Administrator
# Or install in user directory:
pip install --user reference-toolkit
```

**Issue: SSL Certificate Errors**
```powershell
# Disable SSL verification (not recommended for production)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org reference-toolkit
```

---

## 🍎 macOS Installation

### Method 1: Docker (Recommended)

#### Prerequisites
- macOS 11 Big Sur or later
- 4GB+ RAM available for Docker
- Apple Silicon (M1/M2) or Intel processor

#### Installation Steps

**1. Install Docker Desktop for Mac**
```bash
# Download from: https://www.docker.com/products/docker-desktop
# Choose correct chip architecture:
#   - Apple Silicon: Mac with Apple chip
#   - Intel: Mac with Intel chip

# Install and start Docker Desktop
# Accept license agreement
```

**2. Verify Docker Installation**
```bash
docker --version
docker-compose --version
```

**3. Pull or Build Reference Toolkit**
```bash
# Option A: Pull from Docker Hub (when available)
docker pull tamoghna12/reference-toolkit:latest

# Option B: Build from source
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
docker build -t reference-toolkit:latest .
```

**4. Run Reference Toolkit**
```bash
# Basic usage
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool --help

# Search for papers
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool search "CRISPR" --limit 10

# Rename PDFs in current directory
docker run --rm -v $(PWD)/pdfs:/data reference-toolkit:latest reftool rename /data

# With output directory
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool rename /data/input_pdfs --output-dir /data/output_pdfs
```

**5. Using Docker Compose**
```bash
# Navigate to project directory
cd reference-toolkit

# Start services
docker-compose up -d

# Run commands
docker-compose run run reftool search "machine learning" --limit 5

# Stop when done
docker-compose down
```

#### macOS-Specific Considerations

**Apple Silicon (M1/M2/M3)**:
```bash
# Build with platform specification
docker build --platform linux/amd64 -t reference-toolkit:latest .

# Or use native ARM64 build
docker build -t reference-toolkit:latest .
```

**File Permissions**:
```bash
# Docker runs as root by default
# Fix permission issues if needed:
docker run --rm --user $(id -u):$(id -g) -v $(PWD):/data reference-toolkit:latest reftool --help
```

---

### Method 2: Native Python Installation

#### Prerequisites
- macOS 11 Big Sur or later
- Xcode Command Line Tools
- Homebrew (recommended)

#### Installation Steps

**1. Install Homebrew** (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. Install Python 3.10+**
```bash
# Install Python via Homebrew
brew install python@3.11

# Or use pyenv for version management
brew install pyenv
pyenv install 3.11.0
pyenv global 3.11.0

# Verify installation
python3 --version
pip3 --version
```

**3. Install Reference Toolkit**
```bash
# Option A: From PyPI (when available)
pip3 install reference-toolkit

# Option B: From source
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
pip3 install -e .

# Option C: With development dependencies
pip3 install -e ".[dev]"
```

**4. Verify Installation**
```bash
reftool --help
reftool search --help
reftool rename --help
```

**5. Run Reference Toolkit**
```bash
# Search for papers
reftool search "CRISPR gene editing" --limit 10 --output results.csv

# Resolve references
reftool resolve refs.txt --output resolved.csv

# Download PDFs
reftool download resolved.csv --download-dir pdfs

# Rename PDFs
reftool rename ~/Documents/pdfs --dry-run

# Full pipeline
reftool pipeline refs.txt --download-dir ~/Documents/pdfs --bibtex
```

#### macOS-Specific Troubleshooting

**Issue: Xcode Command Line Tools Missing**
```bash
# Install command line tools
xcode-select --install

# Accept license agreement
sudo xcodebuild -license accept
```

**Issue: Python SSL Certificate Errors**
```bash
# Install Python certificates
/Applications/Python\ 3.11/Install\ Certificates.command
```

**Issue: pip Permission Denied**
```bash
# Install in user directory
pip3 install --user reference-toolkit

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install reference-toolkit
```

---

## 🐧 Linux Installation

### Method 1: Docker (Good for Consistency)

#### Prerequisites
- Ubuntu 20.04+, Debian 11+, Fedora 35+, or similar
- Docker Engine
- Docker Compose
- 4GB+ RAM available for Docker

#### Installation Steps

**1. Install Docker**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
```

**2. Install Docker Compose**
```bash
# Linux install
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

**3. Pull or Build Reference Toolkit**
```bash
# Option A: Pull from Docker Hub (when available)
docker pull tamoghna12/reference-toolkit:latest

# Option B: Build from source
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
docker build -t reference-toolkit:latest .
```

**4. Run Reference Toolkit**
```bash
# Basic usage
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool --help

# Search for papers
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool search "CRISPR" --limit 10

# Rename PDFs
docker run --rm -v $(PWD)/pdfs:/data reference-toolkit:latest reftool rename /data

# With output directory
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool rename /data/input --output-dir /data/output
```

**5. Using Docker Compose**
```bash
# Navigate to project directory
cd reference-toolkit

# Start services
docker-compose up -d

# Run commands
docker-compose run run reftool search "machine learning" --limit 5

# Stop when done
docker-compose down
```

#### Linux-Specific Considerations

**File Permissions**:
```bash
# Docker runs as root by default
# Fix permission issues:
docker run --rm --user $(id -u):$(id -g) -v $(PWD):/data reference-toolkit:latest reftool --help

# Or fix permissions after running
sudo chown -R $USER:$USER ./output
```

**SELinux** (Fedora, RHEL, CentOS):
```bash
# Add :z flag to volume mounts
docker run --rm -v $(PWD):/data:z reference-toolkit:latest reftool --help
```

---

### Method 2: Native Python Installation (Recommended for Linux)

#### Prerequisites
- Ubuntu 20.04+, Debian 11+, Fedora 35+, or similar
- Python 3.10 or later
- pip (Python package manager)
- Virtual environment (recommended)

#### Installation Steps

**Ubuntu/Debian**:
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies
sudo apt install -y build-essential python3-dev

# Verify installation
python3 --version
pip3 --version
```

**Fedora/RHEL/CentOS**:
```bash
# Install Python and development tools
sudo dnf install -y python3 python3-pip python3-devel

# Verify installation
python3 --version
pip3 --version
```

**Arch Linux**:
```bash
# Install Python
sudo pacman -S python python-pip

# Verify installation
python --version
pip --version
```

**2. Create Virtual Environment** (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

**3. Install Reference Toolkit**
```bash
# Option A: From PyPI (when available)
pip install reference-toolkit

# Option B: From source
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
pip install -e .

# Option C: With development dependencies
pip install -e ".[dev]"
```

**4. Verify Installation**
```bash
reftool --help
reftool search --help
reftool rename --help
```

**5. Run Reference Toolkit**
```bash
# Search for papers
reftool search "CRISPR gene editing" --limit 10 --output results.csv

# Resolve references
reftool resolve refs.txt --output resolved.csv

# Download PDFs
reftool download resolved.csv --download-dir pdfs

# Rename PDFs
reftool rename ~/Documents/pdfs --dry-run

# Full pipeline
reftool pipeline refs.txt --download-dir ~/Documents/pdfs --bibtex
```

**6. Deactivate Virtual Environment** (when done)
```bash
deactivate
```

#### Linux-Specific Troubleshooting

**Issue: Permission Denied when Installing**
```bash
# Use virtual environment instead of system install
python3 -m venv venv
source venv/bin/activate
pip install reference-toolkit
```

**Issue: Missing System Dependencies**
```bash
# Ubuntu/Debian
sudo apt install -y build-essential python3-dev libxml2-dev libxslt-dev

# Fedora/RHEL
sudo dnf install -y gcc python3-devel libxml2-devel libxslt-devel
```

**Issue: pip Outdated**
```bash
# Upgrade pip in virtual environment
pip install --upgrade pip
```

---

## 🐳 Docker vs Native Installation

### Docker Installation

**Pros**:
✅ Consistent environment across all platforms
✅ No Python version conflicts
✅ Isolated from system Python
✅ Easy to update and remove
✅ Includes all dependencies

**Cons**:
❌ Requires Docker installation (uses more resources)
❌ Slower execution (container overhead)
❌ File system permissions can be tricky
❌ Larger disk footprint

**Best For**:
- Users who want consistency across platforms
- CI/CD environments
- Users with Docker experience
- Avoiding Python environment conflicts

### Native Python Installation

**Pros**:
✅ Faster execution (no container overhead)
✅ Direct file system access
✅ Smaller disk footprint
✅ Can use with other Python tools
✅ Easier debugging

**Cons**:
❌ Python version management required
❌ Potential dependency conflicts
❌ Platform-specific issues
❌ System-level changes

**Best For**:
- Users comfortable with Python
- Development and debugging
- Integration with other Python tools
- Performance-critical usage

---

## 🚀 Quick Start Commands

### Docker Commands (All Platforms)

```bash
# Show help
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool --help

# Search for papers
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool search "query" --limit 10

# Resolve references
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool resolve refs.txt

# Download PDFs
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool download resolved.csv --download-dir /data/pdfs

# Rename PDFs (dry run)
docker run --rm -v $(PWD)/pdfs:/data reference-toolkit:latest reftool rename /data --dry-run

# Rename PDFs (actual)
docker run --rm -v $(PWD)/pdfs:/data reference-toolkit:latest reftool rename /data
```

### Native Python Commands (All Platforms)

```bash
# Show help
reftool --help

# Search for papers
reftool search "query" --limit 10 --output results.csv

# Resolve references
reftool resolve refs.txt --output resolved.csv

# Download PDFs
reftool download resolved.csv --download-dir pdfs/

# Rename PDFs (dry run)
reftool rename pdfs/ --dry-run

# Rename PDFs (actual)
reftool rename pdfs/
```

---

## 🔧 Troubleshooting

### Common Issues Across Platforms

**Issue: "reftool command not found"**

**Docker**:
```bash
# Use full docker run command instead
docker run --rm reference-toolkit:latest reftool --help
```

**Native**:
```bash
# Verify installation
pip show reference-toolkit

# Reinstall
pip install --force-reinstall reference-toolkit

# Check Python path
which python
which reftool
```

**Issue: "Permission Denied"**

**Docker**:
```bash
# Use user flag
docker run --rm --user $(id -u):$(id -g) -v $(PWD):/data reference-toolkit:latest reftool --help
```

**Native**:
```bash
# Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install reference-toolkit
```

**Issue: "Module Not Found"**

**Docker**:
```bash
# Rebuild image
docker build -t reference-toolkit:latest .
```

**Native**:
```bash
# Reinstall with dependencies
pip install --upgrade reference-toolkit

# Or reinstall from source
pip uninstall reference-toolkit
pip install -e .
```

---

## 📚 Additional Resources

### Documentation
- [Main README](README.md)
- [PDF Renaming Guide](docs/PDF_RENAMING_GUIDE.md)
- [Docker Usage](docs/DOCKER_USAGE.md)
- [Contributing Guide](CONTRIBUTING.md)

### Platform-Specific Help
- **Windows**: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- **macOS**: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Linux**: [Docker Engine Installation](https://docs.docker.com/engine/install/)

### Python Resources
- [Python Documentation](https://docs.python.org/3/)
- [pip Documentation](https://pip.pypa.io/)
- [Virtual Environments](https://docs.python.org/3/library/venv.html)

---

## 💡 Tips

1. **Use Docker** if you want consistency across platforms
2. **Use Native** if you want better performance and debugging
3. **Always use --dry-run first** for PDF renaming
4. **Use virtual environments** for native Python installation
5. **Check logs** for troubleshooting issues
6. **Keep Docker updated** for best performance
7. **Monitor disk space** - Docker images can be large

---

## 🆘 Getting Help

If you encounter issues:

1. **Check documentation** in docs/ directory
2. **Search existing issues** on GitHub
3. **Create new issue** with:
   - Platform (Windows/macOS/Linux)
   - Installation method (Docker/Native)
   - Error messages
   - Steps to reproduce

**GitHub**: https://github.com/Tamoghna12/reference-toolkit/issues

---

**Version**: 2.0.0
**Last Updated**: 2026-03-15
**License**: MIT
