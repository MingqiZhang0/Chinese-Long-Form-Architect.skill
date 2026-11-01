# Narrative Workbench technical spike

隔离的 C# 14 / net10.0 / Avalonia 12.1.3 桌面与 Python 3.14.2 只读服务。The original detailed technical-spike report remains in the private development archive; generated reports are not included in this public source snapshot.这里不是完整 Workbench，也不是可通用打开旧项目的 importer。

## Windows reproduction

从仓库根目录运行，依赖安装与构建需要网络：

```powershell
./experiments/workbench-spike/setup.ps1
./experiments/workbench-spike/run-tests.ps1
dotnet run --project experiments/workbench-spike/desktop/Workbench.App --no-restore -- --root $PWD
./experiments/workbench-spike/package.ps1
```

SDK 由 desktop/global.json 固定为 10.0.400。开发依赖默认在 OS temp/NarrativeWorkbenchSpike/environment，NuGet 在同级 nuget，不放入 Skill 源树。也可显式传 `-Python` 或 `--python`。锁文件同时记录 win-x64 打包依赖；当前 Spike runtime 显式固定 10.0.11，原设计期望 10.0.12 的差异见报告。

生成百万汉字、10k synthetic issues 的临时项目：

```powershell
python -B experiments/workbench-spike/fixture.py "$env:TEMP/narrative-large" --large
dotnet run --project experiments/workbench-spike/desktop/Workbench.App --no-restore -- --root $PWD --project "$env:TEMP/narrative-large"
```

应用默认打开仓库 tiny fixture。外部编辑演示请先复制到临时目录，并传 `--project`：删除 `proof` block 的完整 marker 和段落，等待 S2。没有自动改写、保存正文或重新判断小说的按钮。`Restart / reconnect` 重建服务、session 和 lease。

包默认生成在 OS temp/NarrativeWorkbenchSpike/package；其中 `launch.ps1` 使用 bundle 内的 .NET runtime 和冻结 Python 服务。`package-manifest.json` 保存实际文件 hashes。clean VM 尚未验证，不能把 PATH 隔离 smoke 当成 clean-machine certification。

## Layers and contracts

- `desktop/Workbench.Protocol`: 从唯一共享 schema 生成 DTO、nominal IDs，边界校验和 Unicode scalar→UTF-16 映射。
- `desktop/Workbench.Infrastructure`: framed stdio、bounded pending requests、ProcessSupervisor、IWorkbenchClient 实现与 PresentationModel。
- `desktop/Workbench.App`: 可 resize 的原生只读窗口；20 blocks/page，虚拟化 issues；Developer metadata。
- `service`: 原生 watchdog hints、debounce、稳定采集、validated immutable snapshots、leases、read-only dispatch。
- `fixtures/tiny`: canonical state、events/graph/claims、evidence、analysis 分开；没有 LLM。
- `tests`: 临时副本上的故障注入、真实 owner、真实 C#/Python wire、真实 Avalonia smoke；生成的短期 artifacts 不进入发布源包。

沿用正式 `state.query`、`trace.query`、`source.resolve`，对应用户需求中的 knowledge / why / evidence 操作，没有平行 aliases。`snapshot.compare` 的范围只有已登记 state、source digest、evidence health/freshness；不判定正文新意义。

`extend_contract.py` 是一次性、幂等的 profile 升级工具。普通构建只运行 `generate_contract.py --check`。`tests/capture_goldens.py` 显式更新真实 Python sender vectors；不在普通测试里重写 oracle。生成器/边界 validator 只覆盖当前 schema 的受限子集，不是生产通用 codegen 工具。

## Deliberate limits

支持显式 block markers 与 numeric story_valid/day；presentation 查询拒绝，章号不会自动变成故事时间。没有记录的知识返回 UNKNOWN + PARTIAL + NO_RECORDED_STATE，时间未知不默认已知。trace 缺 terminal 或登记对象时返回 TRACE_GAP；没有 fuzzy / AI reattachment。

正文通过分页 windowing，选择/复制局限当前页，未完成整书跨页选择。watch 合批后完整重建小 profile，不是生产增量索引。snapshots 仅内存保存；保留当前、前版和有 lease 的版本，最多 16 pinned generations / 128 leases / 300s TTL。崩溃后重新 baseline，未归档旧正文不可恢复。

只读 allowlist、Python audit write/network guards 与零调用断言已测试；hello 如实返回 `readonly_enforcement=UNVERIFIED`，没有声称 OS 强沙箱。GUI/打包只在 Windows 验证；headless 三平台 CI workflow 尚未运行。
