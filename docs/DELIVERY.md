# 交付状态

日期：2026-10-18（上海时间）。

- Web 临时演示： https://f6fb1b666f9839.lhr.life
- 本地运行： http://127.0.0.1:8000
- 只读 Git 源码快照： https://f6fb1b666f9839.lhr.life/source.git
- 本项目也是本地独立 Git 仓库，另随交付提供源码 ZIP 与 Git bundle。

公网地址由 localhost.run SSH 隧道转发到实际 FastAPI 服务，并非静态截图或只有前端的模拟站点。域名和可访问性依赖当前隧道、本机服务与网络，不提供长期在线保证。只读源码仓库通过 Git dumb HTTP 提供克隆，仅导出 Git 对象白名单，不开放数据库、Cookie、配置、工作区文件或写入。

```bash
git clone https://f6fb1b666f9839.lhr.life/source.git zhixing
# 临时链接失效后，可从离线 bundle 恢复完整提交历史：
git clone zhixing.bundle zhixing
```

长期部署配置已准备为 Dockerfile，尚未获得长期托管授权。已发现 Render 有可用连接能力，但尚未确认安装/连接。没有创建 GitHub 仓库或向用户未知仓库推送；如需 GitHub，可将该本地仓库或 bundle 推送至用户提供的目标。

应用当前默认无真实模型/数据密钥：完整交互主链路使用标记明确的规则模式与构造样例。真实模型与金融数据不冒充已联调。真实持仓不要提交至公开演示。

最终验收包含自动化测试、前端构建、真实 HTTP 与浏览器操作，详见 TESTING.md；部署验证结果以会话末尾实际检查为准。

## 最终公网实测

公网 HTTPS 请求已实际完成：health=ok、主 HTML 返回、未来信息隐藏、逐笔证据白名单、规则模式报告、清单状态更新、JSON 导出、Secure 会话 Cookie，以及跨会话读取返回 404。只读源仓库 HEAD 返回 200，config 返回 404。原始检查结果保存在 PUBLIC_SMOKE.json，不包含用户数据或会话令牌。

localhost.run 在本次运行中自动轮换过域名，因此旧域名失效；以上链接已更新为最后验证时的地址。内置浏览器对公网导航返回 ERR_BLOCKED_BY_CLIENT，未绕过客户端限制；本地真实浏览器操作已验收，公网交互由 HTTPS 集成检查验证。
