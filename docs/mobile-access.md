# 手机端访问 AgentDeck

AgentDeck 不需要单独开发手机 App，手机浏览器直接打开 Web Dashboard 即可。

## 推荐方式：Tailscale

在以下设备安装并登录同一个 Tailscale 账号：

- 运行 AgentDeck Hub + Web 的电脑
- 手机

然后在电脑上启动 AgentDeck，并让 Web 监听所有网卡：

```powershell
.\.venv\Scripts\python.exe .\scripts\agentdeck.py local --demo --web-host 0.0.0.0
```

查看电脑的 Tailscale IP：

```powershell
tailscale ip -4
```

假设输出：

```text
100.x.y.z
```

手机浏览器打开：

```text
http://100.x.y.z:5173
```

Dashboard token：

```text
dev-dashboard-token
```

## 同一 Wi-Fi 方式

如果 Android 手机上无法安装或使用 Tailscale，优先用这个方式。不需要手机安装任何 App。

如果手机和电脑在同一个 Wi-Fi，先在电脑上查看局域网 IP：

```powershell
ipconfig
```

找到 IPv4 地址，例如：

```text
192.168.1.23
```

启动 AgentDeck：

```powershell
.\agentdeck-mobile-lan.bat
```

手机浏览器打开：

```text
http://192.168.1.23:5173
```

如果页面能打开但数据加载失败，通常是电脑防火墙拦了 `8000` 端口。需要允许 Python / uvicorn 在专用网络中通信，或者临时放行本机的 `8000` 和 `5173` 端口。

## 不在同一 Wi-Fi 的情况

如果手机和电脑不在同一个网络，又不能用 Tailscale，可以考虑：

- ZeroTier：和 Tailscale 类似，也是在设备之间建立虚拟局域网。
- 自建 WireGuard：更稳定可控，但配置成本更高。
- Cloudflare Tunnel + Access：适合临时公网访问，但必须加访问控制，不要裸露 Dashboard。

个人使用优先级建议：

```text
同一 Wi-Fi > ZeroTier > 自建 WireGuard > Cloudflare Tunnel + Access
```

## 手机上能做什么

- 查看节点状态
- 查看 Codex session
- 读取最近终端输出
- 给某个 tmux pane 发送 prompt
- 查看 changed files 和 git diff
- 查看操作审计日志

## 注意事项

- 电脑上的 AgentDeck 启动窗口要保持打开。
- 不要把 `5173` 或 `8000` 直接暴露到公网。
- 推荐用 Tailscale，而不是公网端口转发。
- 如果手机打不开页面，优先检查 Windows 防火墙，以及手机和电脑是否在同一个 Tailscale 网络或同一个 Wi-Fi。
