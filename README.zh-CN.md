# Jira Import Doctor · 实验性 Alpha

[English](README.md) | 简体中文

**原始 CSV + 一次导入日志 → 带行号和证据的诊断，区分文件问题、可能的父子级联错误，以及目标 Jira 中尚未确认的问题。**

这是一个只读诊断工具。它不会连接 Jira、上传文件、修改原始 CSV、生成修复补丁或重试导入。Python 3.10+，仅使用标准库，无需 API Key。它不是经过生产验证的导入器。

## 试用内置样例

准备好 Git 和 Python 3.10+ 后，将仓库克隆到一个新目录：

```sh
git clone https://github.com/mozzie49/jira-import-doctor.git
cd jira-import-doctor
```

在仓库根目录运行合成样例：

```sh
python3 scripts/jira_import_doctor.py --csv examples/cascade-hypothesis/input.csv --log examples/cascade-hypothesis/import.log --context examples/cascade-hypothesis/context.json --out /tmp/jira-diagnosis-demo
```

输出目录必须尚不存在。查看其中的 `report.md` 和 `report.json`。

预期结果：4 条源记录；3 条日志错误通过明确的源 ID 关联；2 个可能的父子级联问题；另一条只有 Summary 的警告保留为候选匹配。原始 CSV 的关系图没有确定缺陷。工具不会据此断言 Assignee 就是真正根因，也不会宣称现在可以安全导入。

## 加入日志前后，具体多了什么？

CSV 始终不变。下面都是**可公开展示的合成样例**，不是客户案例，也没有在 Jira 中实际执行导入。

| 可用证据 | 级联样例的结果 |
|---|---|
| [只有 CSV](examples/reports/cascade-hypothesis-before-csv-only.md) | 4 条记录；未发现确定的本地关系图缺陷；无法解释这次导入发生了什么 |
| [CSV + 日志](examples/reports/cascade-hypothesis-after-with-log.md) | 源记录 1、ID `001` 的创建失败见日志第 2 行；记录 2–3 的 Parent 错误见第 3–4 行；因此得到两个带证据的级联假设 |

**下一步：先检查记录 1 的创建失败，再考虑是否需要更改 Parent。** ID 和错误行的对应关系是观察到的证据；“祖先创建失败导致后代报错”仍然只是推测。日志第 5 行的无关警告只有 Summary，因此不认定它已经明确对应某条源记录。

[第二个加入日志后的报告](examples/reports/platform-ambiguous-after-with-log.md)展示了何时应保留判断：日志报告创建了 2 条记录，同时存在 Epic Link 警告。警告中的 Summary 只是候选匹配；CustomField 中看似 Jira Key 的值不是源记录 Key；父子关系是否最终保留仍未验证。[仅看 CSV](examples/reports/platform-ambiguous-before-csv-only.md)得不到这些信息。

重新生成这两组报告：

```sh
python3 scripts/render_demos.py --out /tmp/jira-demo-reports
```

## 三个样例

1. `examples/graph-errors`：重复 ID、缺失父记录、自引用和环。重复 Labels/Component 列与多行单元格会保留。这部分与现有 CSV 预检工具重叠
2. `examples/cascade-hypothesis`：本地关系图合法，但日志明确报告祖先创建失败和后代 Parent 错误。新增价值来自日志证据
3. `examples/platform-ambiguous`：本地关系图合法，出现旧版导入器的已知警告形态，同时日志报告记录已创建。工具保留不确定性，不擅自改写 CSV

另有一次针对 Atlassian 公开附件的实际本地检查，详见[评估记录](references/evaluation.md)。[来源](references/sources.md)和[素材说明](references/provenance.md)明确区分公开观察与合成样例。

## 本地安装 Skill

选择一个目标目录。以下结构来自对应工具的官方文档，不会安装 Claude Code 或 Codex 本身。在下载的 `jira-import-doctor` 目录中运行；目标目录必须尚不存在。

Claude Code 项目安装：

```sh
mkdir -p /path/to/project/.claude/skills
cp -R "$PWD" /path/to/project/.claude/skills/jira-import-doctor
```

Codex 项目安装：

```sh
mkdir -p /path/to/project/.agents/skills
cp -R "$PWD" /path/to/project/.agents/skills/jira-import-doctor
```

在目标项目中开启或重新启动会话。Claude Code 可用 `/jira-import-doctor`，Codex 可用 `$jira-import-doctor`，并提供实际 CSV、单次日志、导入路径和创建/更新意图。

已验证的是复制后的文件布局和 CLI 运行，**尚未实际验证宿主的自动发现与触发**。CLI 也可脱离 Agent 单独使用。

## 可复现检查

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_skill.py
python3 scripts/smoke_install.py
python3 scripts/evaluate.py
```

- `validate_skill.py`：检查必需的 frontmatter、相对资源路径，以及已审查的运行时导入白名单
- `smoke_install.py`：分别复制到两种宿主目录结构，在源代码目录外启动已安装副本；运行期间阻止 socket 和子进程操作
- `evaluate.py`：同一个确定性程序，比较不提供日志与提供日志的结果。这不是与普通 Agent 或竞争产品的效果测评

[托管 Linux CI](https://github.com/mozzie49/jira-import-doctor/actions/runs/38209314109) 已在 Python 3.10、3.12 和 3.13 上通过单元测试、安装验证、受限环境冒烟测试、日志对照和演示报告一致性检查。

这些检查不等于完整安全审计，也不证明真实 Jira 导入成功。

## 使用真实文件

遵循 [SKILL.md](SKILL.md) 和[输入约定](references/contract.md)。需要原始 CSV、一次验证/导入尝试的 UTF-8 日志，以及明确的 context JSON。不知道的信息填 `unknown`，不要猜。

更新文件可能合理地重复目标 Key，Summary 也可能留空。Parent 指向文件外的对象、缺少映射或导入路径未验证时，应保留不确定性。不要因为出现 Parent 错误就清空 Parent、编造目标 ID 或直接重试。

脚本会尽力遮盖常见凭据和邮箱，但**不保证匿名化**。报告仍可能含有 Summary、ID、Key 或未识别的敏感内容，分享前必须本地检查。Python 工具本身不联网；交给 Claude/Codex 的内容仍按所选 Agent 服务的方式处理，不能把整个工作流称为完全离线。

## Alpha 的边界与反馈

这个可复现包适合有人复核的本地试用。宿主自动发现、持续导入用户的真实试用、竞争产品实测，目前都尚未验证。一次小规模、非受控的普通 Agent 对照未显示准确性优势；初次漏识别的计数格式及后续修复已在评估记录中保留。我们不声称优于现有工具、保证兼容、达到导入就绪状态或已经成功完成真实导入。

有帮助的反馈包括：导入路径和项目类型、原本想创建还是更新、预期诊断结论，以及经过真正脱敏的最小 CSV/日志样例。不要提供凭据或私密客户文件。公开附件没有随包分发，也不假定获得了第三方再分发许可。

## 许可证

原创代码、文档和合成样例采用 [MIT 许可证](LICENSE)，署名 mozzie49。第三方 Atlassian 材料不包含在授权范围内，详见[素材说明](references/provenance.md)。
