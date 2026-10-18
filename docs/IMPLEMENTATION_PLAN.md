# 知行投资复盘工作台 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 如用户明确选择子代理执行，改用 superpowers:subagent-driven-development。

**Goal:** 交付可运行、证据可追溯、区分事前与事后信息的 Python 投资复盘 Web 应用及提交材料。

**Architecture:** FastAPI 提供同源 API 和 React 构建产物，SQLite 保存会话隔离的案例、证据、报告和清单。证据过滤和数值计算由 Python 完成，AI 仅对通过校验的证据作结构化解释。

**Tech Stack:** Python / FastAPI / Pydantic / SQLite / pytest / React / TypeScript / Vite / Docker。

**Spec:** [design-spec.md](design-spec.md)

## Global Constraints

- 所有时间以带时区 ISO 8601 存储，界面使用 Asia/Shanghai。
- 仅当 available_at 不晚于截止时点时，外部证据才可进入事前上下文。
- 未配置时提供明确标注的规则辅助复盘，不能显示为真实模型输出。
- 不自动用构造数据填补真实接口失败。
- 不得输出确定性涨跌预测、收益承诺或直接买卖建议。
- API Key 仅在服务端环境变量中读取，不返回浏览器，不写日志、提交或导出。
- 远程部署和代码仓库以实际成功结果为准；本地地址不冒充公开部署地址。

## Review Focus

1. 夏令时或无时区时间不得被当成上海本地时间静默接受：任务 1 测试。
2. 部分卖出和费用导致结果计算失真：任务 2 测试。
3. 模型输出合法 JSON 但引用了其他案例证据：任务 3 测试。
4. 浏览器刷新丢失会话或跨会话泄露案例：任务 4 集成测试。
5. 部署未配密钥导致界面误报 AI 已生成：任务 5 部署配置测试。

## 文件结构

项目源码置于 `outputs/zhixing/`，作为独立仓库根目录。

- `app/main.py`：应用工厂、路由与静态资源服务。
- `app/models.py`：交易、理由、证据和报告 schema。
- `app/storage.py`：SQLite 初始化及会话归属校验。
- `app/imports.py`：CSV 和证据导入、逐行错误与重复检查。
- `app/timeline.py`：可得时间过滤及质量问题。
- `app/calculations.py`：FIFO 已实现盈亏及不可计算原因。
- `app/reviews.py`：规则复盘、模型调用、结构及引用验证。
- `app/providers.py`：提供方状态与已验证接口适配边界。
- `app/demo.py`：明确标记的构造案例。
- `web/src/`：案例、导入、时间线、报告、清单界面。
- `tests/`：领域逻辑、API 与异常路径测试。
- `README.md`、`docs/AI_USAGE.md`、`docs/TESTING.md`：交付记录。
- `pyproject.toml`、`.env.example`、`.gitignore`、`Dockerfile`：依赖、配置与部署。

## Task 1：持久化案例和可追溯时间线

**Files:** `app/models.py`、`app/storage.py`、`app/timeline.py`、`app/main.py`、`tests/test_timeline.py`、`tests/test_api.py`。

**Interfaces:** `create_app(db_path: str) -> FastAPI`；`visible_evidence(evidence: list[Evidence], cutoff: datetime) -> list[Evidence]`。Evidence 包含 id、symbol、occurred_at、available_at、collected_at、source、raw、unit、methodology、quality；未知 available_at 为 null。

- [ ] 写失败测试：截止时点相等的证据可见；晚一秒和未知时点不可见；等价 UTC/上海时间结果相同；无时区输入拒绝；事后理由显示补录标记。
- [ ] 执行 `python -m pytest tests/test_timeline.py -q`，确认因待实现功能失败。
- [ ] 实现 schema、SQLite、会话 cookie 和案例/时间线 API；缺失采集或来源信息保留质量提示。
- [ ] 执行上述测试及 API 隔离测试，要求全部通过；创建仓库并提交该任务。

## Task 2：交易导入和可解释计算

**Files:** `app/imports.py`、`app/calculations.py`、`app/demo.py`、`app/providers.py`、`tests/test_imports.py`、`tests/test_calculations.py`。

**Interfaces:** `preview_csv(text: str) -> ImportPreview`，包含 valid_rows 和 errors；`realized_result(trades: list[Trade]) -> CalculationResult`，包含金额、币种、匹配方法和 warnings。金额内部使用 Decimal。

- [ ] 写失败测试：CSV 空文件、非法时间、负数量、重复行、超限文件；买入 100 股 × 10 元、费用 1 元，卖出 40 股 × 12 元、费用 1 元时已实现盈亏为 78.60 元；无匹配买入不生成正常盈亏。
- [ ] 执行 `python -m pytest tests/test_imports.py tests/test_calculations.py -q`，确认失败。
- [ ] 实现预览/确认导入、模板下载、证据 JSON 导入、FIFO 费用分摊、构造样例和提供方状态。真实接口只根据实际可核实文档接入；未接通显示 unavailable，不生成真实数据。
- [ ] 重跑测试全部通过；验证样例重载不重复导入；提交。

## Task 3：AI 复盘、规则降级和学习清单

**Files:** `app/reviews.py`、`app/main.py`、`tests/test_reviews.py`。

**Interfaces:** `build_review(decisions: list[Decision], evidence: list[Evidence], cutoff: datetime, mode: str) -> Review`；`validate_review(report: Review, allowed_ids: set[str]) -> None`。Report 分 facts、hypotheses、bias_signals、uncertainties、improvements，每项含 evidence_ids；保存 mode、model、cutoff 和证据快照。

- [ ] 写失败测试：无配置只能选择明确标注的规则模式；模型超时、非法 JSON、伪造/跨案例引用、无证据核心结论、含直接买卖建议时返回可识别错误；后续证据不进入模型请求。
- [ ] 执行 `python -m pytest tests/test_reviews.py -q`，确认失败。
- [ ] 实现服务端模型客户端、严格结构校验、引用约束和输出边界检查；原文视为不可信数据。规则模式只输出可核实事实和条件性线索。增加清单增改、报告 JSON/Markdown 导出，导出不包含密钥。
- [ ] 重跑测试；增加批量复盘保留决策与证据关联的测试；提交。

## Task 4：React 可操作主链路

**Files:** `web/package.json`、`web/src/App.tsx`、`web/src/api.ts`、`web/src/styles.css` 及按页面拆分的组件。

**Interfaces:** 前端仅通过同源 `/api` 读取/写入数据；cookie 保存 HttpOnly 会话。报告引用跳转到证据抽屉。导入使用 Task 2 的预览/确认接口。

- [ ] 先增加 API 集成测试：创建案例 → 导入 → 时间线筛选 → 规则复盘 → 清单 → 导出；新会话不能读取旧会话资源，同会话重建客户端可恢复数据。
- [ ] 执行 `python -m pytest tests/test_api.py -q` 并处理缺失接口。
- [ ] 实现案例导航、样例入口、CSV 预览、理由补录、时点开关、原始证据抽屉、模式选择、报告和清单；所有异步请求有加载、空态、失败提示；窄屏布局可操作。
- [ ] 执行 `npm run build` 与后端集成测试；使用可用浏览器工具检查主链路、文件导入和窄屏，修复观察到的问题；提交。

## Task 5：完整交付与真实部署验证

**Files:** `Dockerfile`、`.env.example`、`.gitignore`、`README.md`、`docs/AI_USAGE.md`、`docs/TESTING.md`、部署配置及源码压缩包。

**Interfaces:** `GET /api/health` 返回健康状态；生产通过单进程 HTTP 服务提供 API 与构建产物；数据库路径由环境变量配置；模型密钥缺失时状态明确为未配置。

- [ ] 增加配置/安全测试：未配模型健康状态不宣称模型可用；来源 HTML 不执行；大输入被拒绝；导出无环境变量和跨会话数据。
- [ ] 执行全量 pytest、前端构建和本地 HTTP 健康检查，记录实际结果。
- [ ] 编写 README 和真实 AI 使用记录，列出数据来源、已知边界、未做事项；检查仓库中没有密钥、数据库、用户上传和受限数据。
- [ ] 检查实际可用的 Python 托管及仓库发布能力；有授权则完成部署与源码推送，验证返回 URL。无可用服务则记录具体阻塞，交付可运行源码、Docker 配置与本地实测结果，不虚构 URL。
- [ ] 完成最终检查和提交，生成源码交付包；最终回复列出可验证的 URL/仓库或尚缺的部署条件。

## 自审结果

规格 1–8 均有对应任务；所有报告均依赖服务端时点筛选；提供方失败与模型失败分别显示；未连接真实服务不冒充已接入；部署和仓库发布以实际权限为条件。任务之间按模型、导入、报告、界面、交付顺序执行，避免接口并行漂移。
