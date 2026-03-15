# Quick Start Reference Card

**Get up and running in 5 minutes**

---

## 🪟 Windows

### Docker (Recommended)
```powershell
# 1. Install Docker Desktop
https://www.docker.com/products/docker-desktop

# 2. Build and run
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
docker build -t reference-toolkit:latest .
docker run --rm -v ${PWD}:/data reference-toolkit:latest reftool --help

# 3. Search papers
docker run --rm -v ${PWD}:/data reference-toolkit:latest reftool search "CRISPR" --limit 10
```

### Native Python
```powershell
# 1. Install Python 3.10+
https://www.python.org/downloads/

# 2. Install toolkit
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
pip install -e .

# 3. Run
reftool search "CRISPR" --limit 10
```

---

## 🍎 macOS

### Docker (Recommended)
```bash
# 1. Install Docker Desktop
https://www.docker.com/products/docker-desktop

# 2. Build and run
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
docker build -t reference-toolkit:latest .
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool --help

# 3. Search papers
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool search "CRISPR" --limit 10
```

### Native Python
```bash
# 1. Install Homebrew and Python
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.11

# 2. Install toolkit
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
pip3 install -e .

# 3. Run
reftool search "CRISPR" --limit 10
```

---

## 🐧 Linux

### Docker
```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Build and run
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
docker build -t reference-toolkit:latest .
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool --help

# 3. Search papers
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool search "CRISPR" --limit 10
```

### Native Python (Recommended)
```bash
# 1. Install Python and pip
sudo apt install -y python3 python3-pip python3-venv  # Ubuntu/Debian
# sudo dnf install -y python3 python3-pip python3-devel  # Fedora

# 2. Create virtual environment and install
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 3. Run
reftool search "CRISPR" --limit 10
```

---

## 🎯 Common Commands

### Search Papers
```bash
# Docker
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool search "query" --limit 10

# Native
reftool search "query" --limit 10
```

### Rename PDFs
```bash
# Docker
docker run --rm -v $(PWD)/pdfs:/data reference-toolkit:latest reftool rename /data --dry-run

# Native
reftool rename pdfs/ --dry-run
```

### Full Pipeline
```bash
# Docker
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool pipeline refs.txt

# Native
reftool pipeline refs.txt
```

---

## 📋 Platform-Specific Path Examples

### Windows
```powershell
# Docker volume mounts
docker run --rm -v C:\Users\YourName\Documents:/data reference-toolkit:latest reftool rename /data

# Native paths
reftool rename C:\Users\YourName\Documents\pdfs
```

### macOS/Linux
```bash
# Docker volume mounts
docker run --rm -v ~/Documents:/data reference-toolkit:latest reftool rename /data

# Native paths
reftool rename ~/Documents/pdfs
```

---

## ⚠️ Troubleshooting Quick Fixes

### "command not found"
```bash
# Docker: Use full docker run command
# Native: Verify installation with `pip show reference-toolkit`
```

### "Permission denied"
```bash
# Docker: Add --user $(id -u):$(id -g)
# Native: Use virtual environment
```

### "Module not found"
```bash
# Docker: Rebuild image
# Native: pip install --upgrade reference-toolkit
```

---

## 📚 Need More Help?

- **Full Installation Guide**: [INSTALL_GUIDE.md](INSTALL_GUIDE.md)
- **Documentation**: [docs/](docs/)
- **Issues**: https://github.com/Tamoghna12/reference-toolkit/issues
