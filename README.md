# Zerotier-port-forward
The Zerotier userspace port forwarder without TUN based on ``libzt``. Most of the code are modified from Offical libzt examples. This simple script can set a server for port forwarding to Zerotier network without TUN or vice versa. It can be an easy solution when you try to connect to Zerotier in a VM or docker container but have no permission to install the TUN kernel module.
一个方便的小脚本，基于 ``libzt``，转发本地端口到 Zerotier 或转发 Zerotier 上的端口到本地实现内网穿透。这在无法使用 TUN 的环境中尤其方便，例如在虚拟机或者没有权限的 docker 容器中。
# Usage
``python3 zt.py <server|client> <storage_path> <net_id> <remote_ip> <remote_port> <local_port>``
## Forward local port 22 to ZeroTier network
``python3 zt.py server ./id 0123456789abcdef 8080 22``
## Listen ZeroTier network port 8080 to local port 1234
``python3 zt.py client ./id 0123456789abcdef 192.168.22.1 8080 1234``
