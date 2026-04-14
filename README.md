# Windows 安装与运行说明

本文面向 Windows 10 / 11 用户，帮助你在本地安装并运行这个项目。

项目结构：

- `backend/`：FastAPI + Tortoise ORM 后端
- `frontend/`：Vue 3 + Vite 前端
- `environment.yml`：Conda 环境定义
- `.env.example`：环境变量示例

## 1. 安装基础软件

建议先安装下面这些工具：

- Git
- Miniconda 或 Anaconda
- Node.js 18 或 20 LTS
- PostgreSQL 16
- pgvector

推荐下载地址：

- Git: https://git-scm.com/download/win
- Miniconda: https://docs.conda.io/en/latest/miniconda.html
- Node.js: https://nodejs.org/
- PostgreSQL: https://www.postgresql.org/download/windows/
- pgvector: https://github.com/pgvector/pgvector

## 2. 克隆项目

打开 `PowerShell` 或 `Git Bash`：

```powershell
git clone <你的仓库地址>
cd AUDIT_PROJECT_test
```

如果你是直接拿到压缩包，也可以直接解压后进入项目目录。

## 3. 创建 Python 环境

在项目根目录执行：

```powershell
conda env create -f environment.yml
conda activate audit-project
```

如果环境已经存在，后续可以更新：

```powershell
conda env update -f environment.yml --prune
```

确认 Python 可用：

```powershell
python --version
```

建议版本为 `Python 3.11`。

## 4. 安装前端依赖

进入前端目录：

```powershell
cd frontend
npm install
cd ..
```

确认 Node 和 npm：

```powershell
node -v
npm -v
```

## 5. 配置 PostgreSQL 和 pgvector

### 5.1 创建数据库

安装 PostgreSQL 后，打开 `SQL Shell (psql)` 或你常用的数据库客户端，执行：

```sql
CREATE DATABASE audit_project;
```

### 5.2 启用 pgvector

连接到 `audit_project` 数据库后执行：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

如果提示没有 `vector` 扩展，说明 `pgvector` 还没有正确安装。

## 6. 配置环境变量

这个项目读取的是仓库根目录下的 `.env` 文件。你可以直接复制 `.env.example`：

```powershell
copy .env.example .env
```

然后按你的本机配置修改 `.env`。

一个可参考的示例：

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

说明：

- `.env` 放在项目根目录，不是 `backend/.env`
- 如果不配置大模型和向量接口，部分规则增强或检索能力可能不可用

## 7. 初始化数据库

激活 Conda 环境后，在项目根目录执行：

```powershell
cd backend
python script/init_pgvector.py
cd ..
```

如果你还需要把规则构建并写入 pgvector，可以继续执行：

```powershell
cd backend
python script/build_rules.py
cd ..
```

## 8. 启动后端

在项目根目录打开终端：

```powershell
conda activate audit-project
cd backend
uvicorn app.main:app --reload --port 8001
```

启动后可访问：

- `http://127.0.0.1:8001`
- `http://127.0.0.1:8001/docs`

## 9. 启动前端

另开一个终端窗口：

```powershell
conda activate audit-project
cd frontend
npm run dev
```

前端启动后一般会显示类似地址：

- `http://127.0.0.1:5173`

## 10. 初始化法律数据

如果你需要把现有 Markdown 法规内容导入数据库，可以执行：

```powershell
cd backend
python script/import_law_policy.py
cd ..
```

这个脚本会读取：

- `backend/data/raw/law_policy.md`

并把解析后的条款写入数据库 `law_clauses` 表。

## 11. 常用开发命令

### 后端依赖重装

```powershell
conda activate audit-project
pip install -r backend/requirements.txt
```

### 前端重新安装依赖

```powershell
cd frontend
rmdir /s /q node_modules
del package-lock.json
npm install
```

### 构建前端

```powershell
cd frontend
npm run build
```

## 12. 系统用户与权限数据说明

这个项目除了业务数据外，还有一套系统管理数据，用来支持：

- 登录
- 用户管理
- 角色管理
- 菜单权限控制

相关数据表包括：

- `sys_user`
- `sys_role`
- `sys_user_role`
- `sys_menu`
- `sys_role_menu`

需要注意：

- 当前项目代码里没有单独提供“自动初始化默认管理员、默认角色、默认菜单”的脚本
- `backend/script/init_pgvector.py` 只负责初始化 pgvector 相关表，不负责系统用户数据
- 如果你使用的是全新的空数据库，仅启动后端并不能自动生成可登录的系统管理员

这意味着首次部署时，你通常需要先准备一套系统管理基础数据，至少包括：

- 1 个管理员用户
- 1 个管理员角色
- 用户和角色的关联关系
- 菜单和角色权限关系

推荐方式：

1. 直接导入一份已经可用的数据库初始化数据
2. 或者在已有管理员账号基础上，通过前端“系统管理”页面继续维护用户、角色和菜单

### 使用 SQL 脚本初始化系统用户

如果你已经有一份系统初始化 SQL 脚本，可以直接在 PostgreSQL 中执行。

你当前已有一份脚本用于初始化：

- 角色
- 用户
- 用户角色关系
- 菜单
- 角色菜单关系

执行方式示例：

```powershell
psql -U postgres -d audit_project -f init_user_role_database.sql
```

如果你是在数据库客户端中执行，也可以直接打开脚本后运行。

建议把脚本放到项目内固定位置，例如：

- `backend/script/init_user_role_database.sql`

这样后续 README、部署文档和新环境初始化都会更统一。

脚本应至少覆盖这些系统表：

- `sys_role`
- `sys_user`
- `sys_user_role`
- `sys_menu`
- `sys_role_menu`

注意：

- 这类脚本通常会先清空旧的系统权限数据，再重新插入
- 执行前请确认目标数据库环境，避免覆盖线上数据
- 如果脚本里写死了 `id`，要确保和当前数据库中的主键策略不冲突

补充说明：

- 用户密码在数据库中不是明文保存，而是哈希后的值
- 因此如果你打算手工插入管理员用户，不能直接把明文密码写进 `sys_user.password`
- 更稳妥的做法是使用项目已有数据库、已有管理员账号，或后续补一份专门的初始化脚本

如果后续要把项目交给别人部署，建议再补一个“系统初始化脚本”，自动创建：

- 默认管理员用户
- 默认角色
- 默认菜单
- 默认角色菜单关系

这样新环境会更容易启动。

## 13. Windows 环境注意事项

### 1. 端口问题

项目里常用：

- 后端：`8001`
- 前端：`5173`
- 另一个本地系统可能是：`3000`

如果端口被占用，需要先释放端口或改启动参数。

### 2. 路径分隔符问题

Windows 使用 `\`，但 Python 里大多数相对路径写法没问题。  
如果你手动改脚本路径，尽量优先使用 `Path(...)` 这种写法，不要写死绝对路径。

### 3. PostgreSQL 权限问题

如果连接数据库失败，请优先检查：

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

### 4. 防火墙或代理

如果模型接口或 embedding 接口调用失败，先检查：

- 公司网络限制
- 系统代理
- 防火墙
- API Key 是否正确

## 14. 首次启动检查清单

第一次启动建议按这个顺序检查：

1. `conda activate audit-project`
2. `python --version`
3. `node -v`
4. PostgreSQL 是否已启动
5. `audit_project` 数据库是否存在
6. `vector` 扩展是否已启用
7. `.env` 是否已配置
8. 后端 `http://127.0.0.1:8001/docs` 是否能打开
9. 前端页面是否能打开
10. `sys_user / sys_role / sys_menu` 等系统表是否已有基础数据

## 15. 常见问题

### Q1: `ModuleNotFoundError`

先确认已经激活 Conda 环境：

```powershell
conda activate audit-project
```

然后重新安装依赖：

```powershell
pip install -r backend/requirements.txt
```

### Q2: `psycopg` 或 PostgreSQL 连接失败

请确认：

- PostgreSQL 服务已启动
- `.env` 中用户名密码正确
- 数据库 `audit_project` 已创建

### Q3: 前端启动后接口 401 / 404

请确认：

- 后端是否运行在 `8001`
- 前端请求地址是否正确
- 是否已经登录

### Q4: `vector` 扩展报错

这通常表示 pgvector 未安装成功，或者安装后没有在目标数据库里执行：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Q5: 后端能启动，但前端登录后没有菜单或无法正常使用

请优先检查系统管理相关表是否已有初始化数据：

- `sys_user`
- `sys_role`
- `sys_user_role`
- `sys_menu`
- `sys_role_menu`

如果这些表是空的，系统管理功能将无法正常工作。

## 16. 建议

如果你是第一次在 Windows 上配置这个项目，建议顺序是：

1. 先跑通后端
2. 再跑通前端
3. 再初始化法律数据
4. 最后再跑规则构建和 pgvector 写入

这样排错会简单很多。
