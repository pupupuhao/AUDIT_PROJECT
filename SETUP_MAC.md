# Mac Studio M2 开发环境安装说明

本文适用于全新 macOS 机器，项目根目录为当前仓库。

## 1. 先安装系统基础工具

### 安装 Xcode Command Line Tools

```bash
xcode-select --install
```

### 安装 Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Apple Silicon 机器通常还需要把 Homebrew 加进 shell：

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

确认：

```bash
brew -v
```

## 2. 安装 Conda

这台机器是 M2，推荐安装 `Miniforge`，对 Apple Silicon 兼容性更稳。

```bash
brew install --cask miniforge
```

安装完成后重开终端，或者执行：

```bash
source ~/miniforge3/bin/activate
conda init zsh
```

确认：

```bash
conda --version
```

## 3. 创建项目 Python 环境

进入项目根目录后执行：

```bash
cd /Users/alpha-macstudio/Documents/工作/AUDIT_PROJECT
conda env create -f environment.yml
conda activate audit-project
```

如果后面依赖文件有变更，可以更新：

```bash
conda env update -f environment.yml --prune
```

## 4. 安装前端 Node.js 环境

这个项目有一个前端目录 `fronted/`，使用的是 Vue 3 + Vite，需要 Node.js。

推荐直接用 Homebrew 安装 LTS：

```bash
brew install node
```

确认：

```bash
node -v
npm -v
```

安装前端依赖：

```bash
cd /Users/alpha-macstudio/Documents/工作/AUDIT_PROJECT/fronted
npm install
```

## 5. 安装 PostgreSQL 和 pgvector

后端代码里使用了 PostgreSQL，并且数据库 schema 里依赖 `vector` 扩展。

```bash
brew install postgresql@16 pgvector
brew services start postgresql@16
```

进入数据库：

```bash
psql postgres
```

在 `psql` 里执行：

```sql
ALTER USER postgres WITH PASSWORD '你的密码';
CREATE DATABASE audit_project;
\c audit_project
CREATE EXTENSION IF NOT EXISTS vector;
```

退出：

```sql
\q
```

## 6. 配置后端环境变量

在 `backend/` 同级目录放一个 `.env` 文件，也就是：

`/Users/alpha-macstudio/Documents/工作/AUDIT_PROJECT/backend/.env`

示例内容：

```env
LLM_API_KEY=你的大模型接口key
EMBEDDING_PROVIDER=huggingface
EMBEDDING_API_KEY=你的向量接口key
EMBEDDING_API_URL=https://router.huggingface.co/hf-inference/models
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
EMBEDDING_DIMENSION=768

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=audit_project
POSTGRES_USER=postgres
POSTGRES_PASSWORD=你的数据库密码
```

注意：当前代码读取的是 `backend/.env`，不是仓库根目录 `.env`。

## 7. 初始化数据库表

激活 conda 环境后执行：

```bash
cd /Users/alpha-macstudio/Documents/工作/AUDIT_PROJECT/backend
python script/init_pgvector.py
```

如果需要把规则数据导入数据库，再执行：

```bash
python script/build_rules.py
```

## 8. 启动项目

### 启动后端

```bash
cd /Users/alpha-macstudio/Documents/工作/AUDIT_PROJECT/backend
conda activate audit-project
uvicorn app.main:app --reload
```

默认访问：

```text
http://127.0.0.1:8001
http://127.0.0.1:8001/docs
```

### 启动前端

```bash
cd /Users/alpha-macstudio/Documents/工作/AUDIT_PROJECT/fronted
npm run dev
```

## 9. 这个项目当前需要安装的东西

### 必装

- Xcode Command Line Tools
- Homebrew
- Miniforge（conda）
- Python 3.11 conda 环境
- Node.js / npm
- PostgreSQL 16
- pgvector

### Python 包

- fastapi
- uvicorn
- pydantic
- requests
- psycopg[binary]
- langchain-text-splitters

### 前端包

- vue
- vite
- typescript
- element-plus
- axios

## 10. 已发现的项目注意点

- 仓库里目前没有现成的 `requirements.txt` 和 `environment.yml`，本次已补齐。
- 前端目录名称是 `fronted/`，不是常见的 `frontend/`，启动命令时别写错。
- `backend/pipelines/md_processor.py` 里还写着旧 Windows 路径 `D:\\audit-project\\...`，如果你后面要单独运行这个脚本，需要改成当前 Mac 路径或改成相对路径。
