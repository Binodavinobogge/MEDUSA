# 🪼 MEDUSA

### Your network, within reach.

**MEDUSA** is a lightweight desktop application for Windows that puts your PC’s network activity within easy reach.

Designed to stay conveniently on your desktop, it helps you quickly check active connections, inspect open ports, identify the processes behind them, and close a connection or terminate its process when needed.

An ocean-inspired interface, an animated jellyfish, and an interactive radar make network activity easier to explore.

> **See what’s connected. Understand what’s running. Take action.**

---

## ✨ Features

### 🔎 Explore your connections
- Monitor services such as **HTTPS, DNS, SMB, RDP, and SSH**.
- Inspect the **process, PID, local address, remote address, and connection state**.
- Browse the PC’s **TCP and UDP sockets across IPv4 and IPv6**, beyond the five monitored services.
- Filter and search the port inventory by **port, process, PID, or IP address**.

### 📡 Follow network activity
- View real-time **download and upload rates** for your PC.
- Check active TCP connections and newly observed connections on the monitored services during the last **60 seconds**.
- Explore remote endpoints through an **interactive radar**.
- Select a radar endpoint to inspect its associated connection.

### 🛑 Take action
- **Close a supported TCP IPv4 connection** without terminating the entire application.
- **Terminate a selected process**, closing its associated connections.
- Review the target in a confirmation dialog before proceeding.

### 🪼 Keep it close
- Switch to a **compact view** for quick desktop checks.
- Collapse the radar, traffic panel, and individual services.
- Keep MEDUSA **always on top** when needed.
- Enjoy smooth transitions, an animated mascot, and a teal-to-charcoal interface.
- Network collection runs separately from the interface to keep the application responsive.

---

## 💡 Built for quick checks

MEDUSA is designed to be a convenient tool you can keep at hand throughout the day.

Use it to answer everyday questions:

- **Which application is using this connection?**
- **Where is my PC connecting?**
- **Which ports are listening?**
- **How much network traffic is there right now?**
- **Can I close this connection or stop the process behind it?**

Open it, inspect the activity, and take action from the same interface.

---

## ⚙️ What to know

- Closing individual connections currently supports **TCP IPv4 on Windows** and requires administrator privileges. An application may reconnect afterward.
- Terminating a process closes the entire program and may discard unsaved work.
- The port inventory shows sockets visible to MEDUSA through the operating system. A listening port is **not necessarily reachable from the Internet**.
- Traffic rates are measured for the **whole PC**, not per connection.
- The radar is a visual arrangement of observed endpoints, **not a geographic map or an active network scan**.
- Status indicators and animations describe activity or monitoring conditions. They **do not provide security verdicts**.

---

## 🚧 Project Status

MEDUSA is actively being developed.

The goal is to build an approachable **network visibility and control tool**: useful for everyday checks, clear enough for learners, and convenient for users who want to understand what their PC is doing on the network.

It is not currently an antivirus, firewall, or intrusion detection system.

---

## 🛠️ Built With

**Python** · **PySide6** · **psutil**

---

**Observe. Understand. React.**

*Something is always moving beneath the surface.*
