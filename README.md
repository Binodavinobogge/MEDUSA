🪼 MEDUSA
Your network, within reach.
A desktop network observer for Windows.
See your connections. Understand your traffic. Take action.
🖥️ Windows · 🐍 Python · ⚙️ PySide6 · 📡 psutil
v0.4.2 · In development
</div>

🌊 What is MEDUSA?
MEDUSA puts your PC’s network activity within easy reach.
Keep it on your desktop to quickly check which applications are connected, where they are connecting, and which ports are listening. Inspect a connection, close a supported session, or terminate its process directly from the interface.
A deep teal-to-slate theme, an interactive radar, and an animated jellyfish give MEDUSA its own identity. When you only need a quick glance, turn it into a small, movable desktop widget.
A clearer view of what moves beneath your network.

✨ What you can do
	Feature	What it gives you
🔌	Service monitoring	Dedicated views for HTTPS, DNS, SMB, RDP, and SSH.
🔎	Complete socket inventory	Browse the TCP/UDP IPv4/IPv6 sockets visible to MEDUSA, beyond the five monitored services.
🧩	Process details	Identify process names, PIDs, connection states, and local/remote endpoints.
📡	Live traffic	Follow your PC’s download and upload rates.
🕒	Recent activity	See newly observed connections on the monitored services over the last 60 seconds.
🌐	Public and local IP	Check your local address and the public IP observed by an external service.
🎯	Interactive radar	Select an endpoint to inspect its associated connection.
🛑	Connection controls	Close supported connections or terminate selected processes after confirmation.
🪼	Desktop widget	Keep only active monitored services visible in a compact panel.


🔌 Monitored services
Service	Port
HTTPS	443
DNS	53
SMB	445
RDP	3389
SSH	22


Need more detail? Open Tutte le porte to explore other ports, filter by protocol or IP family, and search by process, PID, port, or address.
🪼 Small when you need it
Click Diventa widget to switch to a compact desktop panel.
- 📍 Starts at the bottom-right of the available screen area.
- 🖱️ Drag the MEDUSA header to place it wherever you prefer.
- 🟢 Shows only active monitored services, with ports and connection counts.
- ↗️ Click Apri to return to the full window.
- 📌 Use PIN in the full interface to keep MEDUSA on top.
The widget covers the five monitored services; the full socket inventory remains available in the main window. Monitoring continues while hidden radar and traffic animations are suspended.
🎯 A radar you can interact with
Click a radar point to open its connection details. Hover over the central jellyfish to see public and local IP information, or click it for quick actions:
- 📋 Copy public IP when available.
- 🔄 Refresh public IP after a network or VPN change.
- 🪼 Become a widget without returning to the sidebar.
With the radar focused, press Enter or Space to open the mascot menu. Use the left/right arrow keys to select endpoints.
The radar arranges observed endpoints visually. It is not a geographical map and does not perform active network scans.
🚀 Get started
Requirements
- Windows
- Python 3.10 or later, 64-bit
- Internet access for the initial dependency installation
Quick launch
Download and extract the project, or clone this repository. Open PowerShell in the folder containing main.py, then run:
.\AVVIA_MEDUSA.bat
You can also double-click the launcher. On first launch, it creates a local .venv and installs the dependencies. Subsequent launches reuse that environment.
<details>
<summary>🛠️ Manual installation</summary>

py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
To launch again:
.\.venv\Scripts\python.exe main.py
</details>

The interface currently uses Italian labels. Close older copies before launching an update; the sidebar and terminal identify the running version.
🛑 Connection and process controls
Close one connection
Select a supported connection and choose Chiudi connessione. Review its process and endpoints before confirming.
This currently supports established TCP IPv4 connections on Windows and requires administrator privileges. It interrupts the session without terminating the application or adding a firewall rule. The application may reconnect immediately. UDP, IPv6, and listening sockets are not supported by this action.
Stop a process
Select a row and choose Termina processo. Review the process name and PID before confirming.
On Windows, this terminates the process and closes its connections. Unsaved work may be lost. MEDUSA verifies process identity, excludes itself and PIDs 0–4, and reports permission errors. These exclusions do not cover every critical system process. Child processes are not automatically terminated, and services may restart independently.
🌐 Public IP and privacy
MEDUSA checks its public IP through ipify at startup and every 60 seconds. You can also request an update manually. Failed lookups display Non disponibile.
The provider sees the lookup request’s source IP. MEDUSA does not send it process lists, socket inventories, or connection history.
With VPN split tunneling, proxies, or application-specific routing, other applications may use a different public IP. This lookup reflects the route of MEDUSA’s request; it does not verify VPN coverage or list every public address simultaneously.
Window preferences are stored locally. Connection history is not saved as a persistent log.
📊 Reading the activity
Indicator	Meaning
🟢 Green	Active connections on the service.
🟡 Yellow	Listening sockets without active remote connections.
🔵 Muted blue	Inactive service.
🔴 Red	Monitoring error or outdated data—not a threat verdict.


Active connections counts established TCP connections across the PC. New / 60 s covers the five monitored services and initially includes connections already present at launch. These totals need not match the sum of the service rows.
Download/upload are aggregate PC interface rates, potentially including virtual interfaces—not per-process or per-connection measurements. Collection normally runs every second, so very short connections may be missed.
A listening port is not necessarily reachable from the Internet. Visibility depends on operating-system permissions; external reachability also depends on firewalls, routing, and NAT. UDP sockets may not expose a remote destination.
🛠️ Built with
Python powers the application, PySide6 provides the native interface, and psutil supplies system and network observations. Network collection runs separately from the GUI to keep the interface responsive.
<details>
<summary>🧪 Run the tests</summary>
