# Repos Management Tool

A Python-based utility for managing and synchronizing Odoo addons from multiple GitHub repositories. This tool automates cloning repositories with sparse checkout and generates Odoo installation commands for updated modules.

## Features

- 🚀 **Auto-clone multiple repositories** with sparse checkout (download only specific modules)
- 📦 **Track changed modules** automatically
- 🔄 **Pull updates** from existing repositories
- 💡 **Generate Odoo commands** for module installation/updates
- ✨ **Supports shallow cloning** for faster downloads
- 🐳 **Compatible with Docker & Native setups**

---

## Installation

### Prerequisites

- Python 3.7+
- PyYAML library
- Git installed and configured
- Bash/Zsh shell

### Step 1: Install Dependencies

```bash
pip install pyyaml
```

Or if you prefer using a requirements file:

```bash
pip install -r requirements.txt
```

### Step 2: Download the Script

Clone or download this repository to your desired location:

```bash
git clone <repository-url> /path/to/repos_management
cd /path/to/repos_management
```

### Step 3: Verify Installation

Check that both files exist in your directory:

```bash
ls -la
```

You should see:

- `sync_repo.py` (the main script)
- `repos.yaml` (configuration file)
- `README.md` (this file)

---

## Configuration: repos.yaml

The `repos.yaml` file defines all repositories to manage and which modules to include from each.

### File Structure

```yaml
./repository-name:
  remotes:
    origin: https://github.com/user/repository.git
  merges:
    - origin branch-name
  includes:
    - module_name_1
    - module_name_2
  depth: 1
```

### Configuration Fields

| Field | Required | Description |
| --- | --- | --- |
| `remotes.origin` | Yes | Git repository URL |
| `merges` | Yes | List with format `origin branch-name` (e.g., `origin 18.0`) |
| `includes` | No | List of specific module/addon names to clone. If omitted, all modules are cloned |
| `depth` | No | Git clone depth (1 = shallow clone, faster) |

### Example Configuration

```yaml
./CybroAddons:
  remotes:
    origin: https://github.com/CybroOdoo/CybroAddons.git
  merges:
    - origin 18.0
  includes:
    - rest_api_odoo
  depth: 1

./knowledge:
  remotes:
    origin: https://github.com/OCA/knowledge.git
  merges:
    - origin 18.0
  includes:
    - document_knowledge
    - document_page
    - document_page_reference
  depth: 1

./base_addons:
  remotes:
    origin: https://github.com/bhurivaj/base_addons.git
  merges:
    - origin master
  depth: 1
```

### Adding a New Repository

1. Open `repos.yaml` in your text editor
2. Add a new entry following the structure above
3. Save the file
4. Run the sync script

```bash
python sync_repo.py
```

---

## How to Run the Script

### Basic Usage

Run the script to clone all repositories defined in `repos.yaml`:

```bash
python sync_repo.py
```

**What it does:**

- Clones new repositories from `repos.yaml`
- For existing repositories, shows "⏭️ ข้าม" (skipped) message
- Generates Odoo installation commands for changed modules

### Pull/Update Existing Repositories

Update all existing repositories to the latest code:

```bash
python sync_repo.py -p
```

Or with long flag:

```bash
python sync_repo.py --pull
```

**What it does:**

- Runs `git pull` on all existing repositories
- Detects which modules were updated
- Generates Odoo commands for updated modules

### Clone/Update Specific Repositories

Clone or update only certain repositories by name:

```bash
python sync_repo.py -g CybroAddons knowledge
```

Or:

```bash
python sync_repo.py --git CybroAddons knowledge
```

**What it does:**

- Processes only the specified repositories
- Works with or without `-p` flag

### Combining Flags

Pull updates for specific repositories:

```bash
python sync_repo.py -p -g CybroAddons server-backend
```

---

## Running the Generated Odoo Commands

After the script finishes, it generates installation/update commands. Choose based on your setup:

### For Native/Virtual Environment Setup

```bash
python odoo-bin -c odoo.conf -d <YOUR_DB_NAME> -u module_name_1,module_name_2
```

**Example:**

```bash
python odoo-bin -c odoo.conf -d production_db -u rest_api_odoo,document_knowledge,account_billing
```

### For Docker Compose Setup (Odoo 18)

```bash
docker compose exec web odoo -c /etc/odoo/odoo.conf -d <YOUR_DB_NAME> -u module_name_1,module_name_2
```

**Example:**

```bash
docker compose exec web odoo -c /etc/odoo/odoo.conf -d production_db -u rest_api_odoo,document_knowledge,account_billing
```

---

## Output Messages

The script provides helpful feedback:

| Icon | Message | Meaning |
| --- | --- | --- |
| 🚀 | "เริ่มตรวจสอบ..." | Starting to process repositories |
| 📦 | "โคลนใหม่..." | Creating new clone of repository |
| ✅ | "โคลนสำเร็จ" | Repository cloned successfully |
| 🔄 | "ตรวจสอบอัปเดต..." | Checking for updates |
| ✨ | "มีโค้ดใหม่เข้ามา!" | Updates found and applied |
| ➖ | "ไม่มีอัปเดตใหม่" | Repository is up to date |
| ⏭️ | "ข้าม..." | Skipped (exists, use -p to update) |
| ❌ | "ล้มเหลว" | Operation failed |
| 🎉 | "สรุป:" | Summary of changed modules |

---

## Changelog

### Version 1.0.0 (Current)

**Features:**

- ✅ Clone repositories with sparse checkout support
- ✅ Pull updates from existing repositories
- ✅ Auto-detect Odoo modules using `__manifest__.py`
- ✅ Track changed modules across operations
- ✅ Generate native and Docker Compose Odoo commands
- ✅ Support for shallow cloning (depth parameter)
- ✅ Selective repository processing with `-g` flag
- ✅ Git commit hash tracking for change detection

**Improvements:**

- Shallow cloning (depth=1) for faster downloads
- Sparse checkout to reduce disk usage
- Automatic module detection when `includes` is not specified
- Support for multiple remotes (though only `origin` is used)

---

## Troubleshooting

### Error: "❌ Error: ไม่พบไฟล์ repos.yaml"

**Solution:** Make sure `repos.yaml` exists in the same directory as the script.

```bash
ls -la repos.yaml
```

### Error: "git clone" fails

**Possible causes:**

- Invalid repository URL in `repos.yaml`
- Network connectivity issues
- Authentication required (for private repositories)

**Solution:** Verify the URL and ensure you can access it:

```bash
git clone https://github.com/OCA/knowledge.git
```

### Modules not detected

**Cause:** The repository may not have `__manifest__.py` files in module directories, or `includes` is not specified.

**Solution:** Specify module names explicitly in the `includes` field in `repos.yaml`.

### Docker command fails

**Cause:** Docker container name or service name may be different.

**Solution:** Check your `docker-compose.yml`:

```bash
docker compose exec <service-name> odoo -c <config-path> -d <db-name> -u module_name
```

---

## Example Workflow

### 1. Setup Initial Configuration

```bash
# Edit repos.yaml with your repositories
nano repos.yaml
```

### 2. Initial Clone

```bash
# Clone all repositories
python sync_repo.py
```

### 3. Upgrade Odoo Modules (Native)

```bash
# Get the generated module list and run
python odoo-bin -c odoo.conf -d mydb -u module1,module2
```

### 4. Regular Updates

```bash
# Pull latest changes
python sync_repo.py -p

# Then upgrade in Odoo
docker compose exec web odoo -c /etc/odoo/odoo.conf -d mydb -u module1,module2
```

---

## License

This tool is provided as-is for managing Odoo addons and repositories.

## Support

For issues or questions, check the script output messages or verify your `repos.yaml` configuration.
