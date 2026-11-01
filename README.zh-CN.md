<div align="center">

# Chinese Long-Form Architect

**中文长篇架构师：面向严肃中文长篇创作的持久化世界 Agent Skill。**

*故事之外，世界仍在继续。*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.13+](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)](#环境要求)
[![Release status: Public preview](https://img.shields.io/badge/Status-Public%20Preview-orange.svg)](PUBLIC_RELEASE_NOTES.md)

[English](README.md) · **简体中文**

[项目动机](#为什么需要它) · [快速开始](#快速开始) · [工作原理](#工作原理) · [系统架构](#系统架构) · [开发与测试](#开发与测试)

</div>

---

Chinese Long-Form Architect 是一套用于**构思、续写、诊断和修订中文长篇小说**的 Agent Skill 与确定性工具。它不把每一章当作彼此孤立的提示词任务，而是持续维护故事事实、人物认知、因果关系与修订影响，同时将作品的文学选择权保留给作者。

本项目**不是独立大语言模型、在线小说写作服务，也不是已经完成的桌面软件**。当前公开版本是 *Public Preview（公开预览版）*；尚不能宣称已经通过完整的长期文学质量验证。

## 为什么需要它

AI 可以在一次生成中写出流畅的场景，却仍可能在后续章节中修改既定事实，让人物突然知道不该知道的信息，遗忘重大事件造成的长期影响，或者通过临时添加设定来解释先前的谜题。

| 长篇创作的典型问题 | 本项目提供的机制 |
| --- | --- |
| 前后章节的既定事实矛盾 | **Canon 与 Story State**：记录重要事实，检查已登记的约束 |
| 人物突然掌握未获得的信息 | **Knowledge Topology（知识拓扑）**：区分世界真相、人物认知、证据来源及信息披露 |
| 悬疑谜底缺乏先前因果依据 | **Hidden Causal Networks（隐藏因果网络）**：记录关键机制、前提和有界因果主张 |
| 配角离开主角视线后停止活动 | **Living World（生活中的世界）**：维护有必要的幕后活动和持续状态 |
| 修改前文后，后续章节悄然失效 | **修订影响分析**：追踪依赖与失效范围 |
| 写作上下文泄露秘密或丢失关键事实 | **按角色限定的上下文编译**：向写作环节提供相应的信息 |
| 所有小说被强行套入固定套路 | **Project Poetics（作品文学原则）**：由作者决定本作品需要何种文学表达 |

这些是辅助创作的机制与工作流程，**并非自动保证**。机器校验只对正确记录并提交的事实与约束有效。

## 快速开始

### 1. 安装 Skill

使用支持文件夹式 Agent Skills 的宿主环境。在项目的 [Releases](https://github.com/MingqiZhang0/Chinese-Long-Form-Architect.skill/releases) 页面发布安装包后，下载独立的 **`skill.zip`** 并解压到宿主的 Skills 目录中。

安装完成后，应当有如下入口：

```text
<你的 Agent Skills 目录>/
└── literary-webnovel-architect/
    ├── SKILL.md
    ├── agents/
    ├── references/
    ├── scripts/
    └── assets/
```

宿主的实际 Skills 路径以其官方说明为准。技术标识符 `literary-webnovel-architect` 仍用于兼容现有配置，不应擅自重命名。**安装包不等同于整个开发仓库**：测试、实验性 Workbench 等开发资源不会全部包含在运行包中。

### 2. 从小说构想开始

在已加载 Skill 的 Agent 对话中，可以直接说：

> 我准备写一部长篇中文悬疑小说。先不要写第一章，请帮助我建立最小必要的项目状态，区分已经发生的事实、每个人物知道什么，以及读者见过哪些信息。不要擅自决定不可逆的核心剧情，请先告诉我哪些问题必须由作者确定。

Skill 会根据项目状态和任务风险选择合适的工作流程。**新建长篇、章节续写、局部文字润色和因果修订不应该执行完全相同的程序**。

### 3. 使用确定性工具（可选）

如果需要命令行项目管理，可以克隆**源码仓库**，在仓库根目录执行：

```bash
git clone https://github.com/MingqiZhang0/Chinese-Long-Form-Architect.skill.git
cd Chinese-Long-Form-Architect.skill
python -m pip install -r requirements.txt

# 查看全部命令及新项目的推荐流程。
python -B scripts/storyctl.py catalog
python -B scripts/storyctl.py route new-project

# 初始化一个最小项目，再验证项目清单。
python -B scripts/storyctl.py project init ./example-novel --project-id example-novel
python -B scripts/storyctl.py project verify ./example-novel/project-manifest.json --root ./example-novel
```

最后一条命令预期输出：

```text
OK: project manifest and canonical pointers are consistent
```

初始化命令创建的是**项目元数据，而不是已经写好的小说**。对于现有项目，可使用 `route resume-project`、`route continue-chapter` 和 `route diagnose-project` 查询推荐操作流程。

## 工作原理

一部长篇小说不只是一个文本文件。Skill 刻意区分普通聊天记录容易混淆的五类信息：

- **世界事实**：在小说世界里实际发生过什么。
- **人物知识和信念**：某个人在某个时刻可能知道什么、相信什么，以及知识依据。
- **叙事可见性**：某种视角、叙述者或写作环节可以披露什么。
- **作者授权**：哪些设定已经确定，哪些只是暂定，哪些保持开放。
- **历史后果**：修改先前决定或事件后，哪些后续内容需要复查。

一个典型的章节流程如下：

```text
作者意图 + Project Poetics
            |
            v
    既定事实 / 状态 / 证据
            |
            v
      规划与准备状态验证
            |
            v
       按职责编译上下文
            |
            v
         正文写作 / 修订
            |
            v
          审查与状态同步
            |
            v
        下一章的最新状态
```

**例子：** 某人在第三章仅仅听说一条传闻，从未亲眼目睹相关事件；但第八章的正文却让他以亲历者身份描述事件。如果相应的知识获得过程和陈述依据已经被记录，系统就能提示依据不匹配。它**不会仅凭阅读未经结构化登记的全文就自动发现所有此类错误**。

项目坚持**选择性形式化**：重要因果与连续性应记录，普通氛围描写和修辞选择则不必全部变成数据库字段。详细规则见 [Skill 主规范](SKILL.md)、[Project Poetics](references/project-poetics.md) 与 [Knowledge Topology](references/knowledge-topology.md)。

## 系统架构

| 层次 | 职责 | 主要目录 |
| --- | --- | --- |
| **Agent Skill** | 选择流程、维护作者控制权、筛选上下文并引导写作与审查 | [`SKILL.md`](SKILL.md)、[`references/`](references/) |
| **确定性工具** | 检验已登记的状态、来源、时间与知识关系、事件、准备状态和修订影响 | [`scripts/`](scripts/)、[`assets/`](assets/) |
| **实验性 Workbench** | 探索只读的项目状态与证据可视化 | [`experiments/workbench-spike/`](experiments/workbench-spike/) |

Workbench 目前只是**技术验证原型，不是正式桌面产品**；Skill 不依赖 Workbench 才能运行。它需要的合成协议文件位于 [`docs/workbench/contracts/`](docs/workbench/contracts/)。

## 支持范围与限制

| 方面 | 当前状态 |
| --- | --- |
| 正文语言 | 以**中文**为目标；当前正文评测证据主要集中在简体中文（`zh-CN`） |
| 任务范围 | 新项目、续写、重大修订、一致性诊断，以及按需使用的局部／探索模式 |
| 文学风格 | 由各项目的 **Project Poetics** 决定，而非固定情节模板 |
| 工具可靠性 | 校验**已登记**的约束；不能保证全部叙事错误自动被发现 |
| 长期文学质量 | 不能承诺连续 50、100 或 300 章的高质量输出 |
| 用户界面 | Skill 与 CLI；Workbench 仍处于实验阶段 |
| 安全边界 | 本地文件及脚本不构成抵御恶意 Agent 或不可信插件的强沙箱 |

公开源码有意排除了私人小说测试素材、原始模型交互记录和内部实验日志。因此历史 **Core / Full / Soak** 回归测试无法从公开仓库完整复现。详细限制请见 [公开发布说明](PUBLIC_RELEASE_NOTES.md) 与 [公开数据政策](PUBLIC_DATA_POLICY.md)。

## 环境要求

- 支持文件式 Agent Skills，并能提供所需模型能力及工具权限的宿主环境。
- 确定性脚本使用 **Python 3.13+**。
- 文档化工具校验所需的 `jsonschema>=4.18,<5`（见 `requirements.txt`）。
- 只有研究实验性 Workbench 时才需要额外的 Python / .NET 依赖，详情见其 [README](experiments/workbench-spike/README.md)。

仅阅读 Skill 指令不需要运行 Python；项目验证、事务处理、上下文编译和正式准备状态门禁等功能则需要相应工具及项目证据。

## 开发与测试

本仓库是经过隐私筛选的**公开源码**；可安装的 `skill.zip` 只保留生产 Skill 所需的内容，不包含全部开发测试与 Workbench。两者有意不是逐文件相同的包。

在源码仓库根目录执行：

```bash
python -B scripts/audit_skill_structure.py .
python -B scripts/test_public_release.py
python -B scripts/test_public_fast.py

# 可选：检查 Workbench 协议代码生成文件是否同步。
python -B experiments/workbench-spike/generate_contract.py --check
```

发布审查时，经过筛选的公开版 Fast 测试曾取得 **12/12** 通过，但这**不能代表**被保留在私人归档中的历史 Core / Full / Soak 测试全部通过。仓库公开后应以 [GitHub Actions](https://github.com/MingqiZhang0/Chinese-Long-Form-Architect.skill/actions) 的实际运行状态为准。

**代码与文档导航：** [`SKILL.md`](SKILL.md) · [`references/`](references/) · [`scripts/`](scripts/) · [`assets/`](assets/) · [`PUBLIC_RELEASE_NOTES.md`](PUBLIC_RELEASE_NOTES.md) · [`SECURITY.md`](SECURITY.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md)

## 贡献与安全

欢迎提交 Issue 和 Pull Request。涉及作者授权、人物知识、证据来源或修订规则的修改，请附上能够复现的**合成测试**。参与方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

请勿将真实小说原稿、隐藏剧情规划、模型交互记录、访问密钥或本机日志提交到公开仓库。Git 历史不是存储私人创作项目的合适位置。安全问题按照 [SECURITY.md](SECURITY.md) 处理。

## 许可证

此公开发行包中的原创代码与文档以 [MIT License](LICENSE) 授权。第三方组件与参考素材（如适用）仍遵守各自条款，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
