# CR-MAS — CodeReview Multi-Agent System

基于 **LangGraph + DeepSeek V4** 的多智能体代码审查系统。用 `cr commit` 替代 `git commit`，7 个 AI Agent 协作分析变更代码，输出带优先级分级的审查报告。

## 架构

```
style ──→ security ──→ performance ──→ readability ──→ extension ──→ bug ──→ chief
 flake8    bandit+V4F    radon+AST        AST+V4F           V4P          V4F     V4P+规则
```

| Agent | 职责 | 引擎 |
|-------|------|------|
| 🎨 风格警察 | PEP 8、代码格式、import 顺序 | flake8（零 Token） |
| 🛡️ 安全哨兵 | SQL 注入、硬编码密码、eval 滥用 | bandit + V4 Flash 二次确认 |
| 📊 性能顾问 | 圈复杂度、嵌套深度 | radon + AST |
| 📖 可读性顾问 | 注释率、魔法数字、变量命名、函数拆分 | AST 统计 + V4 Flash |
| 💡 扩展顾问 | 设计模式、架构优化、库建议 | V4 Pro |
| 🐛 Bug 猎人 | 运行时错误、逻辑缺陷、类型不匹配 | V4 Flash |
| 🧑‍⚖️ 主编 | 冲突检测、分类裁决（🔴🟡🔵💡） | V4 Pro + 规则引擎 |

## 快速开始

### 1. 安装

```bash
git clone https://github.com/HZYoier/cr-mas.git
cd cr-mas
pip install -e .
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

不配 API Key 也可使用静态分析层（风格、安全基础扫描、性能），LLM 增强功能会自动跳过。

### 3. 使用

```bash
# 审查并提交（有严重问题则阻止提交）
cr commit -m "fix: 修复登录模块"

# 跳过审查直接提交
cr commit -m "wip" --skip-review

# 审查有问题也允许提交
cr commit -m "hotfix" --no-fail

# 查看最近5条历史审查记录
cr history --limit 5
```

## 输出示例

```
╭────────────────────╮
│ Code Review Report │
╰────────────────────╯
                      🔴 必须修复
  位置           来源       描述
 ──────────────────────────────────────────
  config.py:5    Bug 猎人   字符串+数字导致TypeError

                      🟡 强烈建议
  位置           来源         描述
 ──────────────────────────────────────────
  test.py:3      Bug 猎人     折扣后未加税，逻辑错误
  test.py        可读性顾问   注释率仅 0%
  test.py:2      可读性顾问   建议定义常量 TAX_RATE

                      🔵 可选优化
  位置           来源         描述
 ──────────────────────────────────────────
  demo.py:4      格式问题     运算符缺少空格
  demo.py:5      未使用变量   'os' imported but unused

                      💡 扩展建议
  位置           优先级   类型       描述
 ──────────────────────────────────────────
  demo.py:22     HIGH     设计模式   建议使用策略模式
```

## 项目结构

```
cr-mas/
├── cr_mas/
│   ├── agents/          # 7 个 Agent
│   │   ├── style.py, security.py, performance.py
│   │   ├── readability.py, extension.py, bug.py, chief.py
│   ├── graph/           # LangGraph 工作流
│   │   ├── state.py, builder.py
│   ├── tools/           # 工具层
│   │   ├── git_parser.py, file_reader.py
│   ├── llm/             # LLM 客户端
│   │   ├── client.py
│   ├── memory/          # 长期记忆（SQLite）
│   │   ├── schema.sql, sqlite_store.py
│   └── main.py          # CLI 入口
│   └── config/           # 配置管理
│       ├── settings.py
├── tests/
│   ├── fixtures/         # 测试代码样本
│   └── test_*.py         # 6 个测试
├── README.md
├── .env.example
└── pyproject.toml
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 多智能体框架 | LangGraph（StateGraph + Checkpointer） |
| LLM | DeepSeek V4 Flash / V4 Pro |
| 静态分析 | flake8, bandit, radon, AST |
| CLI | Click + Rich |
| 长期记忆 | SQLite |
| 版本控制 | GitPython |

## 许可

MIT
