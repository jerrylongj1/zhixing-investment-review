# 知行 · 投资决策复盘与学习

一个真正运行在 Python 后端上的投资复盘工作台。把交易、当时理由、行情和事件放回时间线；区分事前证据与事后信息，将学习沉淀为下一次决策清单。

> **当前边界**：内置的是构造案例，不是真实行情。运行时 AI 和扶摇接口需要自行配置服务端密钥；未配置时可以使用明确标注的规则辅助模式，不能称为大模型生成。iFinD 尚未接入。

## 快速启动

需要 Python 3.11+、Node.js 22+ 和 pnpm 11.25.0。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
cd web
corepack enable
corepack prepare pnpm@11.25.0 --activate
pnpm install --frozen-lockfile
pnpm build
cd ..
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

访问 http://127.0.0.1:8000 。API 文档位于 `/docs`，健康检查位于 `/api/health`。前端开发可在另一个终端运行 `cd web && pnpm dev`，Vite 将 `/api` 代理到 8000 端口；需要通过该代理访问，保持同源。

也可按本次验证版本安装：`pip install -r requirements.lock.txt`。这份文件包含测试依赖；生产基础依赖在 `pyproject.toml` 中。

## 体验路径

1. 点击“体验完整样例”。样例证券 `DEMO.A`、交易、经营简报与价格均为构造数据。
2. 观察默认截止 `2024-03-04 10:15` 时点。首笔交易当日收盘、稍后公告和事后补录理由不会显示为当时已知。
3. 切换“查看后续”，检查后续信息和未知时点标记；点击任何证据查看原始字段、来源、发生/可得/采集时间、单位与口径。
4. 选择交易，生成规则复盘；若服务端已配置模型，可主动选择 AI 模式。报告保留引用和证据快照。
5. 从改进结论加入学习清单，编辑、勾选并导出。创建下一个案例时会显示同会话以往清单，作为决策前上下文。
6. 使用 `examples/trades.csv` 验证 CSV 预览/确认导入，使用 `examples/evidence.json` 验证外部证据导入。

单笔决策的证据白名单以该笔成交时点与观察截止时点的较早者过滤。成组复盘保留 `knowledge_by_decision`，禁止较晚决策的信息被引用到较早决策。报告可以包含晚于某笔决策的已实现结果计算，但计算单独标注为结果，且**不传给模型作为事前上下文**。

## 环境变量

`.env.example` 仅是示例；应用不会自动读取 `.env`。请由运行环境注入，或在 shell 中 `export` 所需变量。

| 变量 | 默认值 / 用途 |
|---|---|
| `DATABASE_PATH` | `data/zhixing.db`，SQLite 路径 |
| `PUBLIC_ORIGIN` | 可选；TLS 反向代理下配置公开 HTTPS 来源，例如 `https://example.com`，保留同源写入检查 |
| `RENDER_EXTERNAL_URL` | Render 自动提供的公网来源；未显式设置 PUBLIC_ORIGIN 时用于同源校验 |
| `COOKIE_SECURE` | `0`；HTTPS 生产设为 `1` |
| `PORT` | Docker 启动端口，默认 `8000`；本地 uvicorn 可用 `--port` |
| `AI_API_KEY` | 可选；只在服务端使用 |
| `AI_MODEL` | 可选；与密钥同时配置，模型需支持严格 JSON Schema |
| `AI_BASE_URL` | `https://api.openai.com/v1`；可指定支持相同结构化输出协议的 HTTPS 服务 |
| `FUYAO_API_KEY` | 可选；扶摇历史日线的 `X-api-key` |

AI 模式会将经过时点过滤的所选证据发送到配置的模型服务。请仅在具有数据使用和发送权限时启用；公开演示不配置模型和金融数据密钥。

## 数据与时点规则

- 真实数据优先适配 [扶摇文档](https://fuyao.aicubes.cn/docs/api-reference/prices/)，鉴权见 [快速开始](https://fuyao.aicubes.cn/docs/quickstart/)。使用文档明确的 `/api/a-share/prices/historical`、`interval=1d`、`adjust=none`；不猜测端点。首版 UI 每次最多 366 天。
- 扶摇历史字段 `date_ms` 是行情日期，`data.timestamp` 是序列就绪时间，**都不证明某根历史 K 线的首次公开时间**。因此适配器保留原字段和 request_id，`available_at=null`、`quality=missing`，可以展开审查，不进入事前结论。未经授权未调用真实接口；测试使用构造响应验证适配。
- [iFinD MCP](https://mcp.51ifind.com/) 当前没有已授权可调用工具，未实现连接。可导入合法获得并注明来源的证据。
- 用户导入的来源、首次可得时间是用户声明，未经过独立认证。`collected_at` 不会替代 `available_at`。无时区日期拒绝；界面统一上海时间。
- 事后补写理由由服务器记录实际时间，不因用户填写历史日期而变成同期证据。样例中的同期记录同样只是构造情节。
- 缺失、冲突、过期、失败的证据均标记异常并排除出正常事实输入。调用失败会保存案例内最近调用状态，不回填样例行情。
- FIFO 用 Decimal 计算，按股数分摊买入费用，卖出费用全额计入；不合并币种/标的。缺少匹配买入则不可计算。所有费用/税费须显式录入；不计算未实现盈亏、企业行动和基准超额收益。

## AI 的角色与验证

开发过程由 Codex 辅助完成架构、实现、测试、界面与审查。产品运行时的 AI 只负责条件性解释、行为线索和过程改进；事实条目由代码从交易和理由记录确定性生成。规则模式没有模型调用。

AI 请求使用严格 JSON Schema；服务端再次校验结构、证据 ID、决策 ID 和逐笔时点白名单，保存证据快照及 SHA256。响应超时、拒绝、截断、无效 JSON、无效引用或命中不允许建议的输出会失败，**不静默降级为正常报告**。用户可主动改用规则模式。

规则校验与提示约束不能证明模型语义正确，也不能穷尽所有变体的金融建议；AI 解释始终标为待人工核验，不能用于自动交易或投资决策。完整实测与修正见 [AI 使用与验证记录](docs/AI_USAGE.md)。

## 测试

```bash
pytest -q
cd web && pnpm build
```

测试覆盖主链路、持久化/会话隔离、时点边界、CSV 失败、费用及部分成交、模型超时/坏响应/伪造引用、数据提供方失败、敏感配置边界。实际验证结果和未覆盖项见 [测试说明](docs/TESTING.md)。

## Docker 与部署

```bash
docker build -t zhixing .
docker run --rm -p 8000:8000 -v zhixing-data:/data \
  -e COOKIE_SECURE=0 zhixing
```

Dockerfile 分阶段构建前端，Python 以非 root 用户运行。将镜像发布到支持 Docker 的平台，挂载可写持久磁盘 `/data`，配置 `DATABASE_PATH=/data/zhixing.db`、HTTPS 下的 `COOKIE_SECURE=1`，健康检查 `/api/health`。平台反向代理应正确传递 Host 和协议；仅信任平台明确的代理地址，不要无条件信任公网转发头。

当前环境无 Docker 引擎，Dockerfile 未实测构建。临时公网隧道若建立成功，仅在本机服务和隧道进程存活时有效，不能当作长期托管。实际 URL 与发布状态见 [交付状态](docs/DELIVERY.md)。

## 隐私、边界与未做事项

- 这是演示级原型：通过随机 HttpOnly Cookie 隔离浏览器会话，数据库持久化。没有正式登录、账户恢复、细粒度授权、配额、审计和备份。清除 Cookie 会失去原会话访问权；请提前导出。
- 公开演示仅输入构造或匿名数据。SQLite 不加密；真实持仓建议本地运行。模型模式的内容安全规则是启发式约束，不能作为合规认证。
- 代码不含密钥、数据库、用户上传和受限金融数据。构造示例可分发，真实接口返回的数据权限由提供方与用户约定。
- 外部证据不自动追踪修订版本，未支持证券拆并、分红复权成本、多空杠杆、多市场税制、订单撮合和券商连接。
- 无确定性涨跌预测、收益承诺或直接买卖建议；复盘中的假设不构成事实归因证明。
- 真实模型端到端调用、真实金融接口、持久远程托管及 GitHub 推送均需要相应服务授权；未验证部分如实记录，不冒充完成。

## 源码结构

`app/` 领域模型/API/数据适配/复盘；`web/` React 工作台；`tests/` 自动化测试；`examples/` 构造导入文件；`docs/` 设计、执行、验证和交付记录。源代码为独立 Git 仓库，另提供可离线还原历史的 Git bundle。

## 公开只读源码快照（可选）

演示部署可显式设置 `PUBLIC_SOURCE_PATH` 为**已经审查、无密钥和用户数据的 bare Git 快照**，先对快照运行 `git update-server-info`，再启动应用。`/source.git` 支持只读 HTTP 克隆，路由仅允许 HEAD、info/refs 和 Git 对象文件，拒绝 config、hooks 等路径。不设置该变量时源码路由返回 404。不要指向含隐私提交历史的仓库；本项目演示快照仅包含本次构造应用源码。

下载交付 ZIP 若包含 `web/dist`，则可跳过 Node 构建步骤，直接安装 Python 依赖并启动。

GitHub 仓库： https://github.com/jerrylongj1/zhixing-investment-review （私有）。CI 配置作为 `docs/ci-example.yml` 示例保存，尚未启用 GitHub Actions。云端仓库使用经过检查的初始源码快照；完整开发提交历史保留在离线 Git bundle 中。
