# 🛠️ AgenticFlow Scripts

This directory contains utility scripts for AgenticFlow development and user support.

## 📋 Available Scripts

### `test_installation.py`
**Installation verification script for users**

Comprehensive diagnostic tool that verifies AgenticFlow is properly installed and working.

#### Usage:
```bash
# Download and run directly
curl -s https://raw.githubusercontent.com/milad-o/agenticflow/main/scripts/test_installation.py | python

# Or download and run locally
wget https://raw.githubusercontent.com/milad-o/agenticflow/main/scripts/test_installation.py
python test_installation.py

# Or from cloned repository
python scripts/test_installation.py
```

#### What it tests:
- ✅ Core module imports (agenticflow, config, agent, tools)
- ✅ Memory system imports  
- ✅ Orchestration and workflow imports
- ✅ Optional components (vectorstores, embeddings, MCP)
- ✅ Basic agent creation and configuration
- ✅ Provides troubleshooting guidance for failures

#### Output example:
```
🚀 AgenticFlow Installation Test
============================================================
🎉 SUCCESS: AgenticFlow is properly installed!
✅ All core components are working
📚 Check out USAGE.md or examples/ to get started
```

---

## 🔧 For Developers

To add new utility scripts:

1. **Create the script** in this directory
2. **Make it executable**: `chmod +x script_name.py`
3. **Add shebang**: `#!/usr/bin/env python3`
4. **Update this README** with usage instructions
5. **Test the script** with different installation scenarios

## 📚 Related Documentation

- [Installation Guide](../USAGE.md#installation)
- [Development Setup](../README.md#development-installation)
- [Troubleshooting](../README.md#troubleshooting)