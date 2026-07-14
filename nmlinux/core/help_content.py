from __future__ import annotations
from nmlinux.core.settings import get as _get_settings


_CONTENT: dict[str, dict[str, dict]] = {
    "Dashboard": {
        "fr": {
            "desc": "Vue d'ensemble réseau de la machine locale : nom d'hôte, IPv4/IPv6, passerelle, serveurs DNS actifs, adresse IP publique et géolocalisation approximative via ip-api.com.",
            "examples": [
                "Vérifier l'IP locale et la passerelle avant de diagnostiquer un problème de connectivité.",
                "Confirmer que les bons serveurs DNS sont utilisés après un changement de configuration.",
                "Connaître son IP publique sans ouvrir un navigateur.",
                "Vérifier sa localisation apparente (utile avec un VPN actif).",
            ],
            "cli": [
                "ip route",
                "ip addr show",
                "curl -s ifconfig.me",
                "resolvectl status | grep 'DNS Servers'",
            ],
        },
        "en": {
            "desc": "Network overview of the local machine: hostname, IPv4/IPv6, gateway, active DNS servers, public IP and approximate geolocation via ip-api.com.",
            "examples": [
                "Check local IP and gateway before diagnosing a connectivity issue.",
                "Confirm the correct DNS servers are in use after a config change.",
                "Know your public IP without opening a browser.",
                "Verify your apparent location (useful with an active VPN).",
            ],
            "cli": [
                "ip route",
                "ip addr show",
                "curl -s ifconfig.me",
                "resolvectl status | grep 'DNS Servers'",
            ],
        },
        "es": {
            "desc": "Vista general de red de la máquina local: nombre de host, IPv4/IPv6, puerta de enlace, servidores DNS activos, IP pública y geolocalización aproximada via ip-api.com.",
            "examples": [
                "Verificar la IP local y la puerta de enlace antes de diagnosticar un problema de conectividad.",
                "Confirmar que se usan los servidores DNS correctos tras un cambio de configuración.",
                "Conocer la IP pública sin abrir un navegador.",
                "Verificar la ubicación aparente (útil con una VPN activa).",
            ],
            "cli": [
                "ip route",
                "ip addr show",
                "curl -s ifconfig.me",
                "resolvectl status | grep 'DNS Servers'",
            ],
        },
        "de": {
            "desc": "Netzwerkübersicht der lokalen Maschine: Hostname, IPv4/IPv6, Gateway, aktive DNS-Server, öffentliche IP und ungefähre Geolokalisierung über ip-api.com.",
            "examples": [
                "Lokale IP und Gateway prüfen, bevor ein Verbindungsproblem diagnostiziert wird.",
                "Nach einer Konfigurationsänderung bestätigen, dass die richtigen DNS-Server verwendet werden.",
                "Öffentliche IP kennen, ohne einen Browser zu öffnen.",
                "Scheinbaren Standort prüfen (nützlich mit aktivem VPN).",
            ],
            "cli": [
                "ip route",
                "ip addr show",
                "curl -s ifconfig.me",
                "resolvectl status | grep 'DNS Servers'",
            ],
        },
        "it": {
            "desc": "Panoramica di rete della macchina locale: hostname, IPv4/IPv6, gateway, server DNS attivi, IP pubblico e geolocalizzazione approssimativa tramite ip-api.com.",
            "examples": [
                "Verificare IP locale e gateway prima di diagnosticare un problema di connettività.",
                "Confermare che i server DNS corretti vengono utilizzati dopo una modifica della configurazione.",
                "Conoscere il proprio IP pubblico senza aprire un browser.",
                "Verificare la posizione apparente (utile con una VPN attiva).",
            ],
            "cli": [
                "ip route",
                "ip addr show",
                "curl -s ifconfig.me",
                "resolvectl status | grep 'DNS Servers'",
            ],
        },
        "pt": {
            "desc": "Visão geral da rede da máquina local: hostname, IPv4/IPv6, gateway, servidores DNS ativos, IP público e geolocalização aproximada via ip-api.com.",
            "examples": [
                "Verificar o IP local e o gateway antes de diagnosticar um problema de conectividade.",
                "Confirmar que os servidores DNS corretos estão a ser utilizados após uma alteração de configuração.",
                "Conhecer o IP público sem abrir um browser.",
                "Verificar a localização aparente (útil com uma VPN ativa).",
            ],
            "cli": [
                "ip route",
                "ip addr show",
                "curl -s ifconfig.me",
                "resolvectl status | grep 'DNS Servers'",
            ],
        },

        "ja": {
            "desc": "ローカルマシンのネットワーク概要：ホスト名、IPv4/IPv6、ゲートウェイ、有効なDNSサーバー、パブリックIPおよびip-api.com経由のおおよその位置情報。",
            "examples": [
                "接続の問題を診断する前にローカルIPとゲートウェイを確認する。",
                "設定変更後に正しいDNSサーバーが使用されていることを確認する。",
                "ブラウザを開かずにパブリックIPを確認する。",
                "見かけの位置を確認する（VPN使用時に便利）。",
            ],
            "cli": [
                "ip route",
                "ip addr show",
                "curl -s ifconfig.me",
                "resolvectl status | grep 'DNS Servers'",
            ],
        },
        "zh": {
            "desc": "本地机器的网络概览：主机名、IPv4/IPv6、网关、活动DNS服务器、公网IP及通过ip-api.com获取的大致地理位置。",
            "examples": [
                "诊断连接问题前检查本地IP和网关。",
                "配置更改后确认使用了正确的DNS服务器。",
                "无需打开浏览器即可查看公网IP。",
                "验证显示的位置（使用VPN时很有用）。",
            ],
            "cli": [
                "ip route",
                "ip addr show",
                "curl -s ifconfig.me",
                "resolvectl status | grep 'DNS Servers'",
            ],
        },
    },
    "Connections": {
        "fr": {
            "desc": "Gère toutes les connexions réseau NetworkManager (Ethernet, Wi-Fi, VPN, WireGuard). Connecter, déconnecter, éditer ou supprimer une connexion, avec filtre par type et barre CLI pédagogique.",
            "examples": [
                "Activer ou désactiver rapidement une connexion VPN.",
                "Voir les détails IP/DNS/SSID d'une connexion Wi-Fi active.",
                "Supprimer un ancien profil Wi-Fi inutile.",
            ],
            "cli": [
                "nmcli connection show",
                "nmcli connection up 'MonWifi'",
                "nmcli connection down 'MonVPN'",
                "nmcli connection delete 'AncienProfil'",
            ],
        },
        "en": {
            "desc": "Manages all NetworkManager connections (Ethernet, Wi-Fi, VPN, WireGuard). Connect, disconnect, edit or delete connections with type filtering and a pedagogic CLI bar.",
            "examples": [
                "Quickly activate or deactivate a VPN connection.",
                "See IP/DNS/SSID details of an active Wi-Fi connection.",
                "Delete an old unused Wi-Fi profile.",
            ],
            "cli": [
                "nmcli connection show",
                "nmcli connection up 'MyWifi'",
                "nmcli connection down 'MyVPN'",
                "nmcli connection delete 'OldProfile'",
            ],
        },
        "es": {
            "desc": "Gestiona todas las conexiones de red NetworkManager (Ethernet, Wi-Fi, VPN, WireGuard). Conectar, desconectar, editar o eliminar conexiones con filtro por tipo y barra CLI pedagógica.",
            "examples": [
                "Activar o desactivar rápidamente una conexión VPN.",
                "Ver los detalles IP/DNS/SSID de una conexión Wi-Fi activa.",
                "Eliminar un perfil Wi-Fi antiguo que ya no se usa.",
            ],
            "cli": [
                "nmcli connection show",
                "nmcli connection up 'MiWifi'",
                "nmcli connection down 'MiVPN'",
                "nmcli connection delete 'PerfilAntiguo'",
            ],
        },
        "de": {
            "desc": "Verwaltet alle NetworkManager-Verbindungen (Ethernet, Wi-Fi, VPN, WireGuard). Verbindungen herstellen, trennen, bearbeiten oder löschen mit Typfilter und pädagogischer CLI-Leiste.",
            "examples": [
                "Eine VPN-Verbindung schnell aktivieren oder deaktivieren.",
                "IP/DNS/SSID-Details einer aktiven Wi-Fi-Verbindung anzeigen.",
                "Ein altes ungenutztes Wi-Fi-Profil löschen.",
            ],
            "cli": [
                "nmcli connection show",
                "nmcli connection up 'MeinWifi'",
                "nmcli connection down 'MeinVPN'",
                "nmcli connection delete 'AlteresProfil'",
            ],
        },
        "it": {
            "desc": "Gestisce tutte le connessioni di rete NetworkManager (Ethernet, Wi-Fi, VPN, WireGuard). Connettere, disconnettere, modificare o eliminare connessioni con filtro per tipo e barra CLI didattica.",
            "examples": [
                "Attivare o disattivare rapidamente una connessione VPN.",
                "Vedere i dettagli IP/DNS/SSID di una connessione Wi-Fi attiva.",
                "Eliminare un vecchio profilo Wi-Fi non utilizzato.",
            ],
            "cli": [
                "nmcli connection show",
                "nmcli connection up 'MyWifi'",
                "nmcli connection down 'MyVPN'",
                "nmcli connection delete 'OldProfile'",
            ],
        },
        "pt": {
            "desc": "Gere todas as ligações de rede NetworkManager (Ethernet, Wi-Fi, VPN, WireGuard). Ligar, desligar, editar ou eliminar ligações com filtro por tipo e barra CLI pedagógica.",
            "examples": [
                "Ativar ou desativar rapidamente uma ligação VPN.",
                "Ver os detalhes IP/DNS/SSID de uma ligação Wi-Fi ativa.",
                "Eliminar um perfil Wi-Fi antigo que já não é utilizado.",
            ],
            "cli": [
                "nmcli connection show",
                "nmcli connection up 'MyWifi'",
                "nmcli connection down 'MyVPN'",
                "nmcli connection delete 'OldProfile'",
            ],
        },

        "ja": {
            "desc": "すべてのNetworkManager接続（Ethernet、Wi-Fi、VPN、WireGuard）を管理。タイプフィルターと教育的CLIバーで接続・切断・編集・削除が可能。",
            "examples": [
                "VPN接続を素早く有効化または無効化する。",
                "アクティブなWi-Fi接続のIP/DNS/SSID詳細を確認する。",
                "使用していない古いWi-Fiプロファイルを削除する。",
            ],
            "cli": [
                "nmcli connection show",
                "nmcli connection up 'MyWifi'",
                "nmcli connection down 'MyVPN'",
                "nmcli connection delete 'OldProfile'",
            ],
        },
        "zh": {
            "desc": "管理所有NetworkManager连接（Ethernet、Wi-Fi、VPN、WireGuard）。支持按类型筛选和教学式CLI栏，可连接、断开、编辑或删除连接。",
            "examples": [
                "快速启用或禁用VPN连接。",
                "查看活动Wi-Fi连接的IP/DNS/SSID详情。",
                "删除不再使用的旧Wi-Fi配置文件。",
            ],
            "cli": [
                "nmcli connection show",
                "nmcli connection up 'MyWifi'",
                "nmcli connection down 'MyVPN'",
                "nmcli connection delete 'OldProfile'",
            ],
        },
    },
    "Interfaces": {
        "fr": {
            "desc": "Liste toutes les interfaces réseau actives (Ethernet, Wi-Fi, loopback, bridges…) avec état, adresse MAC, IPv4 et IPv6. Clic sur une interface → détail complet.",
            "examples": [
                "Vérifier quelle interface est active et son état up/down.",
                "Retrouver l'adresse MAC pour configurer un DHCP statique.",
                "Identifier les interfaces virtuelles créées par Docker ou WireGuard.",
            ],
            "cli": [
                "ip addr show",
                "ip link show",
                "ip -j addr | python3 -m json.tool",
                "nmcli device status",
            ],
        },
        "en": {
            "desc": "Lists all active network interfaces (Ethernet, Wi-Fi, loopback, bridges…) with state, MAC address, IPv4 and IPv6. Click an interface for full details.",
            "examples": [
                "Check which interface is active and its up/down state.",
                "Find the MAC address to configure a static DHCP lease.",
                "Identify virtual interfaces created by Docker or WireGuard.",
            ],
            "cli": [
                "ip addr show",
                "ip link show",
                "ip -j addr | python3 -m json.tool",
                "nmcli device status",
            ],
        },
        "es": {
            "desc": "Lista todas las interfaces de red activas (Ethernet, Wi-Fi, loopback, bridges…) con estado, dirección MAC, IPv4 e IPv6. Clic en una interfaz → detalles completos.",
            "examples": [
                "Verificar qué interfaz está activa y su estado up/down.",
                "Encontrar la dirección MAC para configurar un DHCP estático.",
                "Identificar interfaces virtuales creadas por Docker o WireGuard.",
            ],
            "cli": [
                "ip addr show",
                "ip link show",
                "ip -j addr | python3 -m json.tool",
                "nmcli device status",
            ],
        },
        "de": {
            "desc": "Listet alle aktiven Netzwerkschnittstellen (Ethernet, Wi-Fi, Loopback, Bridges…) mit Status, MAC-Adresse, IPv4 und IPv6. Klick auf eine Schnittstelle → vollständige Details.",
            "examples": [
                "Prüfen, welche Schnittstelle aktiv ist und ihren Up/Down-Status.",
                "MAC-Adresse für eine statische DHCP-Reservierung finden.",
                "Von Docker oder WireGuard erstellte virtuelle Schnittstellen identifizieren.",
            ],
            "cli": [
                "ip addr show",
                "ip link show",
                "ip -j addr | python3 -m json.tool",
                "nmcli device status",
            ],
        },
        "it": {
            "desc": "Elenca tutte le interfacce di rete attive (Ethernet, Wi-Fi, loopback, bridge…) con stato, indirizzo MAC, IPv4 e IPv6. Clic su un'interfaccia → dettagli completi.",
            "examples": [
                "Verificare quale interfaccia è attiva e il suo stato up/down.",
                "Trovare l'indirizzo MAC per configurare una prenotazione DHCP statica.",
                "Identificare le interfacce virtuali create da Docker o WireGuard.",
            ],
            "cli": [
                "ip addr show",
                "ip link show",
                "ip -j addr | python3 -m json.tool",
                "nmcli device status",
            ],
        },
        "pt": {
            "desc": "Lista todas as interfaces de rede ativas (Ethernet, Wi-Fi, loopback, bridges…) com estado, endereço MAC, IPv4 e IPv6. Clique numa interface → detalhes completos.",
            "examples": [
                "Verificar qual interface está ativa e o seu estado up/down.",
                "Encontrar o endereço MAC para configurar uma reserva DHCP estática.",
                "Identificar interfaces virtuais criadas pelo Docker ou WireGuard.",
            ],
            "cli": [
                "ip addr show",
                "ip link show",
                "ip -j addr | python3 -m json.tool",
                "nmcli device status",
            ],
        },

        "ja": {
            "desc": "すべてのアクティブなネットワークインターフェース（Ethernet、Wi-Fi、ループバック、ブリッジ…）を状態・MACアドレス・IPv4・IPv6と共に一覧表示。インターフェースをクリックすると詳細表示。",
            "examples": [
                "どのインターフェースがアクティブでその状態（up/down）を確認する。",
                "静的DHCPリースを設定するためにMACアドレスを調べる。",
                "DockerまたはWireGuardで作成された仮想インターフェースを特定する。",
            ],
            "cli": [
                "ip addr show",
                "ip link show",
                "ip -j addr | python3 -m json.tool",
                "nmcli device status",
            ],
        },
        "zh": {
            "desc": "列出所有活动网络接口（Ethernet、Wi-Fi、环回、桥接…），显示状态、MAC地址、IPv4和IPv6。点击接口可查看完整详情。",
            "examples": [
                "检查哪个接口处于活动状态及其up/down状态。",
                "查找MAC地址以配置静态DHCP租约。",
                "识别Docker或WireGuard创建的虚拟接口。",
            ],
            "cli": [
                "ip addr show",
                "ip link show",
                "ip -j addr | python3 -m json.tool",
                "nmcli device status",
            ],
        },
    },
    "Wi-Fi": {
        "fr": {
            "desc": "Scanne les réseaux Wi-Fi disponibles et affiche SSID, BSSID, canal, fréquence, signal (barres ▂▄▆█) et sécurité. Le réseau connecté apparaît en premier.",
            "examples": [
                "Détecter les réseaux voisins et comparer les niveaux de signal.",
                "Vérifier si un réseau est en 2,4 GHz ou 5 GHz.",
                "Identifier les réseaux non sécurisés (Open) à proximité.",
            ],
            "cli": [
                "nmcli dev wifi list",
                "nmcli dev wifi connect 'MonSSID' password 'monmotdepasse'",
                "iwlist wlan0 scan | grep -E 'SSID|Signal'",
            ],
        },
        "en": {
            "desc": "Scans available Wi-Fi networks and shows SSID, BSSID, channel, frequency, signal (bars ▂▄▆█) and security type. The connected network appears first.",
            "examples": [
                "Detect nearby networks and compare signal levels.",
                "Check if a network is on 2.4 GHz or 5 GHz.",
                "Identify unsecured (Open) networks nearby.",
            ],
            "cli": [
                "nmcli dev wifi list",
                "nmcli dev wifi connect 'MySSID' password 'mypassword'",
                "iwlist wlan0 scan | grep -E 'SSID|Signal'",
            ],
        },
        "es": {
            "desc": "Escanea las redes Wi-Fi disponibles y muestra SSID, BSSID, canal, frecuencia, señal (barras ▂▄▆█) y seguridad. La red conectada aparece primero.",
            "examples": [
                "Detectar redes cercanas y comparar los niveles de señal.",
                "Verificar si una red está en 2,4 GHz o 5 GHz.",
                "Identificar redes no seguras (Open) en las proximidades.",
            ],
            "cli": [
                "nmcli dev wifi list",
                "nmcli dev wifi connect 'MiSSID' password 'micontraseña'",
                "iwlist wlan0 scan | grep -E 'SSID|Signal'",
            ],
        },
        "de": {
            "desc": "Scannt verfügbare Wi-Fi-Netzwerke und zeigt SSID, BSSID, Kanal, Frequenz, Signal (Balken ▂▄▆█) und Sicherheitstyp an. Das verbundene Netzwerk erscheint zuerst.",
            "examples": [
                "Nahegelegene Netzwerke erkennen und Signalstärken vergleichen.",
                "Prüfen, ob ein Netzwerk auf 2,4 GHz oder 5 GHz betrieben wird.",
                "Ungesicherte (offene) Netzwerke in der Nähe identifizieren.",
            ],
            "cli": [
                "nmcli dev wifi list",
                "nmcli dev wifi connect 'MeinSSID' password 'meinpasswort'",
                "iwlist wlan0 scan | grep -E 'SSID|Signal'",
            ],
        },
        "it": {
            "desc": "Scansiona le reti Wi-Fi disponibili e mostra SSID, BSSID, canale, frequenza, segnale (barre ▂▄▆█) e tipo di sicurezza. La rete connessa appare per prima.",
            "examples": [
                "Rilevare le reti vicine e confrontare i livelli di segnale.",
                "Verificare se una rete è a 2,4 GHz o 5 GHz.",
                "Identificare le reti non protette (Open) nelle vicinanze.",
            ],
            "cli": [
                "nmcli dev wifi list",
                "nmcli dev wifi connect 'MySSID' password 'mypassword'",
                "iwlist wlan0 scan | grep -E 'SSID|Signal'",
            ],
        },
        "pt": {
            "desc": "Analisa as redes Wi-Fi disponíveis e mostra SSID, BSSID, canal, frequência, sinal (barras ▂▄▆█) e tipo de segurança. A rede ligada aparece primeiro.",
            "examples": [
                "Detetar redes próximas e comparar os níveis de sinal.",
                "Verificar se uma rede está em 2,4 GHz ou 5 GHz.",
                "Identificar redes não seguras (Open) nas proximidades.",
            ],
            "cli": [
                "nmcli dev wifi list",
                "nmcli dev wifi connect 'MySSID' password 'mypassword'",
                "iwlist wlan0 scan | grep -E 'SSID|Signal'",
            ],
        },

        "ja": {
            "desc": "利用可能なWi-Fiネットワークをスキャンし、SSID、BSSID、チャンネル、周波数、信号強度（▂▄▆█）およびセキュリティタイプを表示。接続中のネットワークが先頭に表示される。",
            "examples": [
                "近隣のネットワークを検出し、信号強度を比較する。",
                "ネットワークが2.4 GHzか5 GHzかを確認する。",
                "近くのオープン（非暗号化）ネットワークを特定する。",
            ],
            "cli": [
                "nmcli dev wifi list",
                "nmcli dev wifi connect 'MySSID' password 'mypassword'",
                "iwlist wlan0 scan | grep -E 'SSID|Signal'",
            ],
        },
        "zh": {
            "desc": "扫描可用Wi-Fi网络，显示SSID、BSSID、信道、频率、信号强度（▂▄▆█）和安全类型。已连接的网络显示在首位。",
            "examples": [
                "检测附近的网络并比较信号强度。",
                "检查网络是否工作在2.4 GHz或5 GHz。",
                "识别附近的开放（不安全）网络。",
            ],
            "cli": [
                "nmcli dev wifi list",
                "nmcli dev wifi connect 'MySSID' password 'mypassword'",
                "iwlist wlan0 scan | grep -E 'SSID|Signal'",
            ],
        },
    },
    "Subnet": {
        "fr": {
            "desc": "Calculateur CIDR : à partir d'une IP et d'un masque (ex. 192.168.1.0/24), calcule réseau, masque, wildcard, broadcast, plage d'hôtes et nombre total d'hôtes. IPv4 et IPv6.",
            "examples": [
                "Calculer la plage d'adresses avant d'attribuer des IPs fixes.",
                "Vérifier si deux adresses IP appartiennent au même sous-réseau.",
                "Planifier le découpage d'un réseau (subnetting).",
            ],
            "cli": [
                "ipcalc 192.168.1.0/24",
                "python3 -c \"import ipaddress; n=ipaddress.IPv4Network('192.168.1.0/24'); print(n.network_address, n.broadcast_address, n.num_addresses)\"",
                "ip route show | grep 192.168.1",
            ],
        },
        "en": {
            "desc": "CIDR calculator: from an IP and mask (e.g. 192.168.1.0/24), computes network, mask, wildcard, broadcast, host range and total count. IPv4 and IPv6.",
            "examples": [
                "Calculate the address range before assigning static IPs.",
                "Check if two IP addresses are on the same subnet.",
                "Plan subnetting for a network.",
            ],
            "cli": [
                "ipcalc 192.168.1.0/24",
                "python3 -c \"import ipaddress; n=ipaddress.IPv4Network('192.168.1.0/24'); print(n.network_address, n.broadcast_address, n.num_addresses)\"",
                "ip route show | grep 192.168.1",
            ],
        },
        "es": {
            "desc": "Calculadora CIDR: a partir de una IP y máscara (ej. 192.168.1.0/24), calcula red, máscara, wildcard, broadcast, rango de hosts y total. IPv4 e IPv6.",
            "examples": [
                "Calcular el rango de direcciones antes de asignar IPs estáticas.",
                "Verificar si dos direcciones IP pertenecen a la misma subred.",
                "Planificar el fraccionamiento de una red (subnetting).",
            ],
            "cli": [
                "ipcalc 192.168.1.0/24",
                "python3 -c \"import ipaddress; n=ipaddress.IPv4Network('192.168.1.0/24'); print(n.network_address, n.broadcast_address, n.num_addresses)\"",
                "ip route show | grep 192.168.1",
            ],
        },
        "de": {
            "desc": "CIDR-Rechner: aus einer IP und Maske (z.B. 192.168.1.0/24) werden Netzwerk, Maske, Wildcard, Broadcast, Hostbereich und Gesamtzahl berechnet. IPv4 und IPv6.",
            "examples": [
                "Adressbereich berechnen, bevor statische IPs vergeben werden.",
                "Prüfen, ob zwei IP-Adressen im gleichen Subnetz liegen.",
                "Subnetting für ein Netzwerk planen.",
            ],
            "cli": [
                "ipcalc 192.168.1.0/24",
                "python3 -c \"import ipaddress; n=ipaddress.IPv4Network('192.168.1.0/24'); print(n.network_address, n.broadcast_address, n.num_addresses)\"",
                "ip route show | grep 192.168.1",
            ],
        },
        "it": {
            "desc": "Calcolatore CIDR: da un IP e una maschera (es. 192.168.1.0/24) calcola rete, maschera, wildcard, broadcast, intervallo di host e totale. IPv4 e IPv6.",
            "examples": [
                "Calcolare l'intervallo di indirizzi prima di assegnare IP statici.",
                "Verificare se due indirizzi IP si trovano nella stessa subnet.",
                "Pianificare il subnetting per una rete.",
            ],
            "cli": [
                "ipcalc 192.168.1.0/24",
                "python3 -c \\\"import ipaddress; n=ipaddress.IPv4Network('192.168.1.0/24'); print(n.network_address, n.broadcast_address, n.num_addresses)\\\"",
                "ip route show | grep 192.168.1",
            ],
        },
        "pt": {
            "desc": "Calculadora CIDR: a partir de um IP e máscara (ex. 192.168.1.0/24) calcula rede, máscara, wildcard, broadcast, intervalo de hosts e total. IPv4 e IPv6.",
            "examples": [
                "Calcular o intervalo de endereços antes de atribuir IPs estáticos.",
                "Verificar se dois endereços IP estão na mesma sub-rede.",
                "Planear o subnetting de uma rede.",
            ],
            "cli": [
                "ipcalc 192.168.1.0/24",
                "python3 -c \\\"import ipaddress; n=ipaddress.IPv4Network('192.168.1.0/24'); print(n.network_address, n.broadcast_address, n.num_addresses)\\\"",
                "ip route show | grep 192.168.1",
            ],
        },

        "ja": {
            "desc": "CIDRカリキュレーター：IPとマスク（例：192.168.1.0/24）からネットワーク、マスク、ワイルドカード、ブロードキャスト、ホスト範囲と合計数を計算。IPv4とIPv6に対応。",
            "examples": [
                "静的IPを割り当てる前にアドレス範囲を計算する。",
                "2つのIPアドレスが同じサブネットにあるか確認する。",
                "ネットワークのサブネット分割を計画する。",
            ],
            "cli": [
                "ipcalc 192.168.1.0/24",
                "python3 -c \"import ipaddress; n=ipaddress.IPv4Network('192.168.1.0/24'); print(n.network_address, n.broadcast_address, n.num_addresses)\"",
                "ip route show | grep 192.168.1",
            ],
        },
        "zh": {
            "desc": "CIDR计算器：根据IP和掩码（如192.168.1.0/24），计算网络地址、子网掩码、反掩码、广播地址、主机范围和总数。支持IPv4和IPv6。",
            "examples": [
                "分配静态IP前计算地址范围。",
                "检查两个IP地址是否在同一子网中。",
                "规划网络的子网划分方案。",
            ],
            "cli": [
                "ipcalc 192.168.1.0/24",
                "python3 -c \"import ipaddress; n=ipaddress.IPv4Network('192.168.1.0/24'); print(n.network_address, n.broadcast_address, n.num_addresses)\"",
                "ip route show | grep 192.168.1",
            ],
        },
    },
    "DNS": {
        "fr": {
            "desc": "Interroge n'importe quel serveur DNS via dig. Supporte A, AAAA, MX, TXT, NS, CNAME, PTR, SOA, ANY. Serveur DNS alternatif configurable, reverse lookup automatique depuis une IP.",
            "examples": [
                "Vérifier qu'un enregistrement A pointe vers la bonne IP.",
                "Tester la propagation DNS d'un domaine nouvellement configuré.",
                "Chercher les enregistrements MX pour diagnostiquer des problèmes email.",
                "Reverse lookup d'une IP pour identifier un serveur.",
            ],
            "cli": [
                "dig A example.com @8.8.8.8",
                "dig MX example.com",
                "dig -x 8.8.8.8",
                "dig TXT example.com +short",
            ],
        },
        "en": {
            "desc": "Queries any DNS server using dig. Supports A, AAAA, MX, TXT, NS, CNAME, PTR, SOA, ANY. Configurable alternative DNS server, automatic reverse lookup from an IP.",
            "examples": [
                "Verify an A record points to the correct IP.",
                "Test DNS propagation for a newly configured domain.",
                "Look up MX records to diagnose email issues.",
                "Reverse lookup an IP to identify a server.",
            ],
            "cli": [
                "dig A example.com @8.8.8.8",
                "dig MX example.com",
                "dig -x 8.8.8.8",
                "dig TXT example.com +short",
            ],
        },
        "es": {
            "desc": "Consulta cualquier servidor DNS mediante dig. Soporta A, AAAA, MX, TXT, NS, CNAME, PTR, SOA, ANY. Servidor DNS alternativo configurable, reverse lookup automático desde una IP.",
            "examples": [
                "Verificar que un registro A apunta a la IP correcta.",
                "Probar la propagación DNS de un dominio recién configurado.",
                "Buscar registros MX para diagnosticar problemas de correo.",
                "Reverse lookup de una IP para identificar un servidor.",
            ],
            "cli": [
                "dig A example.com @8.8.8.8",
                "dig MX example.com",
                "dig -x 8.8.8.8",
                "dig TXT example.com +short",
            ],
        },
        "de": {
            "desc": "Fragt beliebige DNS-Server über dig ab. Unterstützt A, AAAA, MX, TXT, NS, CNAME, PTR, SOA, ANY. Konfigurierbarer alternativer DNS-Server, automatisches Reverse-Lookup von einer IP.",
            "examples": [
                "Prüfen, ob ein A-Record auf die richtige IP zeigt.",
                "DNS-Propagation einer neu konfigurierten Domain testen.",
                "MX-Einträge nachschlagen, um E-Mail-Probleme zu diagnostizieren.",
                "Reverse-Lookup einer IP zur Server-Identifikation.",
            ],
            "cli": [
                "dig A example.com @8.8.8.8",
                "dig MX example.com",
                "dig -x 8.8.8.8",
                "dig TXT example.com +short",
            ],
        },
        "it": {
            "desc": "Interroga qualsiasi server DNS tramite dig. Supporta A, AAAA, MX, TXT, NS, CNAME, PTR, SOA, ANY. Server DNS alternativo configurabile, reverse lookup automatico da un IP.",
            "examples": [
                "Verificare che un record A punti all'IP corretto.",
                "Testare la propagazione DNS di un dominio appena configurato.",
                "Cercare i record MX per diagnosticare problemi email.",
                "Reverse lookup di un IP per identificare un server.",
            ],
            "cli": [
                "dig A example.com @8.8.8.8",
                "dig MX example.com",
                "dig -x 8.8.8.8",
                "dig TXT example.com +short",
            ],
        },
        "pt": {
            "desc": "Consulta qualquer servidor DNS através do dig. Suporta A, AAAA, MX, TXT, NS, CNAME, PTR, SOA, ANY. Servidor DNS alternativo configurável, reverse lookup automático a partir de um IP.",
            "examples": [
                "Verificar se um registo A aponta para o IP correto.",
                "Testar a propagação DNS de um domínio recentemente configurado.",
                "Procurar registos MX para diagnosticar problemas de email.",
                "Reverse lookup de um IP para identificar um servidor.",
            ],
            "cli": [
                "dig A example.com @8.8.8.8",
                "dig MX example.com",
                "dig -x 8.8.8.8",
                "dig TXT example.com +short",
            ],
        },

        "ja": {
            "desc": "digを使用して任意のDNSサーバーをクエリ。A、AAAA、MX、TXT、NS、CNAME、PTR、SOA、ANYをサポート。代替DNSサーバーの設定可能、IPからの自動リバースルックアップ。",
            "examples": [
                "AレコードがIPを正しく指していることを確認する。",
                "新たに設定したドメインのDNS伝播をテストする。",
                "メール問題を診断するためにMXレコードを調べる。",
                "IPのリバースルックアップでサーバーを特定する。",
            ],
            "cli": [
                "dig A example.com @8.8.8.8",
                "dig MX example.com",
                "dig -x 8.8.8.8",
                "dig TXT example.com +short",
            ],
        },
        "zh": {
            "desc": "使用dig查询任意DNS服务器。支持A、AAAA、MX、TXT、NS、CNAME、PTR、SOA、ANY类型。可配置备用DNS服务器，支持从IP自动反向查找。",
            "examples": [
                "验证A记录是否指向正确的IP。",
                "测试新配置域名的DNS传播情况。",
                "查找MX记录以诊断邮件问题。",
                "对IP进行反向查找以识别服务器。",
            ],
            "cli": [
                "dig A example.com @8.8.8.8",
                "dig MX example.com",
                "dig -x 8.8.8.8",
                "dig TXT example.com +short",
            ],
        },
    },
    "Ping": {
        "fr": {
            "desc": "Moniteur de ping multi-hôtes en continu : paquets ICMP à intervalles configurables (1-30s) vers plusieurs destinations simultanées. Statistiques RTT min/moy/max et taux de perte en temps réel.",
            "examples": [
                "Surveiller simultanément la passerelle, 8.8.8.8 et un serveur distant.",
                "Mesurer la stabilité d'une connexion internet sur une longue durée.",
                "Vérifier qu'un équipement répond après un redémarrage.",
                "Comparer la latence vers plusieurs serveurs.",
            ],
            "cli": [
                "ping -c 4 -i 1 8.8.8.8",
                "ping -c 100 -i 0.2 192.168.1.1",
                "ping -s 1400 -c 10 192.168.1.1",
                "ping6 ::1",
            ],
        },
        "en": {
            "desc": "Continuous multi-host ping monitor: ICMP packets at configurable intervals (1-30s) to multiple simultaneous destinations. RTT min/avg/max and packet loss stats in real time.",
            "examples": [
                "Monitor gateway, 8.8.8.8 and a remote server simultaneously.",
                "Measure internet connection stability over a long period.",
                "Verify that a device responds after a reboot.",
                "Compare latency to multiple servers.",
            ],
            "cli": [
                "ping -c 4 -i 1 8.8.8.8",
                "ping -c 100 -i 0.2 192.168.1.1",
                "ping -s 1400 -c 10 192.168.1.1",
                "ping6 ::1",
            ],
        },
        "es": {
            "desc": "Monitor de ping multi-host continuo: paquetes ICMP a intervalos configurables (1-30s) hacia múltiples destinos simultáneos. Estadísticas RTT mín/med/máx y tasa de pérdida en tiempo real.",
            "examples": [
                "Monitorear simultáneamente la puerta de enlace, 8.8.8.8 y un servidor remoto.",
                "Medir la estabilidad de la conexión a internet durante un período largo.",
                "Verificar que un equipo responde tras un reinicio.",
                "Comparar la latencia hacia varios servidores.",
            ],
            "cli": [
                "ping -c 4 -i 1 8.8.8.8",
                "ping -c 100 -i 0.2 192.168.1.1",
                "ping -s 1400 -c 10 192.168.1.1",
                "ping6 ::1",
            ],
        },
        "de": {
            "desc": "Kontinuierlicher Multi-Host-Ping-Monitor: ICMP-Pakete in konfigurierbaren Intervallen (1-30s) zu mehreren gleichzeitigen Zielen. RTT min/avg/max und Paketverluststatistiken in Echtzeit.",
            "examples": [
                "Gateway, 8.8.8.8 und einen entfernten Server gleichzeitig überwachen.",
                "Stabilität der Internetverbindung über einen langen Zeitraum messen.",
                "Prüfen, ob ein Gerät nach einem Neustart antwortet.",
                "Latenz zu mehreren Servern vergleichen.",
            ],
            "cli": [
                "ping -c 4 -i 1 8.8.8.8",
                "ping -c 100 -i 0.2 192.168.1.1",
                "ping -s 1400 -c 10 192.168.1.1",
                "ping6 ::1",
            ],
        },
        "it": {
            "desc": "Monitor ping multi-host continuo: pacchetti ICMP a intervalli configurabili (1-30s) verso più destinazioni simultanee. Statistiche RTT min/avg/max e perdita pacchetti in tempo reale.",
            "examples": [
                "Monitorare contemporaneamente gateway, 8.8.8.8 e un server remoto.",
                "Misurare la stabilità della connessione internet su un lungo periodo.",
                "Verificare che un dispositivo risponda dopo un riavvio.",
                "Confrontare la latenza verso più server.",
            ],
            "cli": [
                "ping -c 4 -i 1 8.8.8.8",
                "ping -c 100 -i 0.2 192.168.1.1",
                "ping -s 1400 -c 10 192.168.1.1",
                "ping6 ::1",
            ],
        },
        "pt": {
            "desc": "Monitor de ping multi-host contínuo: pacotes ICMP a intervalos configuráveis (1-30s) para múltiplos destinos simultâneos. Estatísticas RTT mín/méd/máx e taxa de perda em tempo real.",
            "examples": [
                "Monitorizar simultaneamente o gateway, 8.8.8.8 e um servidor remoto.",
                "Medir a estabilidade da ligação à internet durante um longo período.",
                "Verificar se um dispositivo responde após um reinício.",
                "Comparar a latência para vários servidores.",
            ],
            "cli": [
                "ping -c 4 -i 1 8.8.8.8",
                "ping -c 100 -i 0.2 192.168.1.1",
                "ping -s 1400 -c 10 192.168.1.1",
                "ping6 ::1",
            ],
        },

        "ja": {
            "desc": "継続的なマルチホストpingモニター：設定可能な間隔（1〜30秒）で複数の宛先へ同時にICMPパケットを送信。RTT最小/平均/最大とパケットロス統計をリアルタイム表示。",
            "examples": [
                "ゲートウェイ、8.8.8.8、リモートサーバーを同時に監視する。",
                "長期間にわたってインターネット接続の安定性を測定する。",
                "再起動後にデバイスが応答することを確認する。",
                "複数のサーバーへのレイテンシーを比較する。",
            ],
            "cli": [
                "ping -c 4 -i 1 8.8.8.8",
                "ping -c 100 -i 0.2 192.168.1.1",
                "ping -s 1400 -c 10 192.168.1.1",
                "ping6 ::1",
            ],
        },
        "zh": {
            "desc": "持续多主机ping监控：以可配置间隔（1-30秒）同时向多个目标发送ICMP数据包。实时显示RTT最小/平均/最大值和丢包统计。",
            "examples": [
                "同时监控网关、8.8.8.8和远程服务器。",
                "长期测量互联网连接的稳定性。",
                "验证设备重启后是否响应。",
                "比较到多个服务器的延迟。",
            ],
            "cli": [
                "ping -c 4 -i 1 8.8.8.8",
                "ping -c 100 -i 0.2 192.168.1.1",
                "ping -s 1400 -c 10 192.168.1.1",
                "ping6 ::1",
            ],
        },
    },
    "IP Scanner": {
        "fr": {
            "desc": "Découvre les équipements actifs sur un réseau local par scan ARP/ping sur une plage CIDR. Affiche IP, hostname (DNS/mDNS/NetBIOS), adresse MAC et fabricant (base OUI 39 000 entrées). Export CSV/TXT.",
            "examples": [
                "Inventorier tous les équipements sur 192.168.1.0/24.",
                "Retrouver l'IP d'un équipement par son nom ou son fabricant.",
                "Détecter un équipement inconnu via l'OUI.",
                "Exporter la liste pour un audit d'inventaire réseau.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn 192.168.1.0/24 -oG - | grep 'Up'",
                "arp-scan --localnet",
                "ip neigh show",
            ],
        },
        "en": {
            "desc": "Discovers active devices on a local network by ARP/ping scanning a CIDR range. Shows IP, hostname (DNS/mDNS/NetBIOS), MAC and manufacturer (39,000-entry OUI database). CSV/TXT export.",
            "examples": [
                "Inventory all devices on 192.168.1.0/24.",
                "Find a device's IP by its name or manufacturer.",
                "Detect an unknown device via OUI lookup.",
                "Export the list for a network inventory audit.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn 192.168.1.0/24 -oG - | grep 'Up'",
                "arp-scan --localnet",
                "ip neigh show",
            ],
        },
        "es": {
            "desc": "Descubre los dispositivos activos en una red local mediante escaneo ARP/ping sobre un rango CIDR. Muestra IP, hostname (DNS/mDNS/NetBIOS), MAC y fabricante (base OUI 39.000 entradas). Exportación CSV/TXT.",
            "examples": [
                "Inventariar todos los dispositivos en 192.168.1.0/24.",
                "Encontrar la IP de un dispositivo por su nombre o fabricante.",
                "Detectar un dispositivo desconocido mediante OUI.",
                "Exportar la lista para una auditoría de inventario de red.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn 192.168.1.0/24 -oG - | grep 'Up'",
                "arp-scan --localnet",
                "ip neigh show",
            ],
        },
        "de": {
            "desc": "Entdeckt aktive Geräte in einem lokalen Netzwerk durch ARP/Ping-Scan eines CIDR-Bereichs. Zeigt IP, Hostname (DNS/mDNS/NetBIOS), MAC und Hersteller (39.000-Einträge OUI-Datenbank). CSV/TXT-Export.",
            "examples": [
                "Alle Geräte in 192.168.1.0/24 inventarisieren.",
                "IP eines Geräts über seinen Namen oder Hersteller finden.",
                "Unbekanntes Gerät über OUI-Nachschlagen erkennen.",
                "Liste für ein Netzwerkinventar-Audit exportieren.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn 192.168.1.0/24 -oG - | grep 'Up'",
                "arp-scan --localnet",
                "ip neigh show",
            ],
        },
        "it": {
            "desc": "Scopre i dispositivi attivi su una rete locale tramite scansione ARP/ping su un intervallo CIDR. Mostra IP, hostname (DNS/mDNS/NetBIOS), MAC e produttore (database OUI 39.000 voci). Export CSV/TXT.",
            "examples": [
                "Inventariare tutti i dispositivi su 192.168.1.0/24.",
                "Trovare l'IP di un dispositivo tramite nome o produttore.",
                "Rilevare un dispositivo sconosciuto tramite OUI.",
                "Esportare la lista per un audit di inventario di rete.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn 192.168.1.0/24 -oG - | grep 'Up'",
                "arp-scan --localnet",
                "ip neigh show",
            ],
        },
        "pt": {
            "desc": "Descobre dispositivos ativos numa rede local por varrimento ARP/ping num intervalo CIDR. Mostra IP, hostname (DNS/mDNS/NetBIOS), MAC e fabricante (base OUI 39.000 entradas). Exportação CSV/TXT.",
            "examples": [
                "Inventariar todos os dispositivos em 192.168.1.0/24.",
                "Encontrar o IP de um dispositivo pelo nome ou fabricante.",
                "Detetar um dispositivo desconhecido via OUI.",
                "Exportar a lista para uma auditoria de inventário de rede.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn 192.168.1.0/24 -oG - | grep 'Up'",
                "arp-scan --localnet",
                "ip neigh show",
            ],
        },

        "ja": {
            "desc": "ARP/pingスキャンによりCIDR範囲内のアクティブなデバイスを検出。IP、ホスト名（DNS/mDNS/NetBIOS）、MACアドレス、メーカー（39,000件OUIデータベース）を表示。CSV/TXTエクスポート。",
            "examples": [
                "192.168.1.0/24上のすべてのデバイスをインベントリする。",
                "名前またはメーカーでデバイスのIPを検索する。",
                "OUI検索で未知のデバイスを検出する。",
                "ネットワークインベントリ監査用にリストをエクスポートする。",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn 192.168.1.0/24 -oG - | grep 'Up'",
                "arp-scan --localnet",
                "ip neigh show",
            ],
        },
        "zh": {
            "desc": "通过ARP/ping扫描CIDR范围内的活动设备。显示IP、主机名（DNS/mDNS/NetBIOS）、MAC地址和厂商（39,000条OUI数据库）。支持CSV/TXT导出。",
            "examples": [
                "清点192.168.1.0/24上的所有设备。",
                "通过名称或厂商查找设备IP。",
                "通过OUI查找检测未知设备。",
                "导出列表用于网络资产审计。",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn 192.168.1.0/24 -oG - | grep 'Up'",
                "arp-scan --localnet",
                "ip neigh show",
            ],
        },
    },
    "Port Scanner": {
        "fr": {
            "desc": "Scanne les ports TCP d'un hôte par connexion directe (sans root). Plages de ports, presets courants (Web, Mail, SSH…), service identifié pour chaque port ouvert. Jusqu'à 200 threads.",
            "examples": [
                "Vérifier que les ports 80 et 443 sont ouverts sur un serveur web.",
                "Détecter les services actifs sur un serveur avant d'y accéder.",
                "Confirmer que le port SSH (22) est fermé sur une machine exposée.",
                "Chercher des ports inhabituels sur un équipement suspect.",
            ],
            "cli": [
                "nmap -sT -p 80,443,22 192.168.1.10",
                "nmap -sT -p 1-1024 192.168.1.10",
                "nc -zv 192.168.1.10 22",
                "ss -tlnp",
            ],
        },
        "en": {
            "desc": "Scans TCP ports on a host via direct connect (no root). Port ranges, common presets (Web, Mail, SSH…), identified service per open port. Up to 200 threads.",
            "examples": [
                "Verify ports 80 and 443 are open on a web server.",
                "Detect active services on a server before accessing it.",
                "Confirm SSH port (22) is closed on an internet-facing machine.",
                "Look for unusual ports on a suspicious device.",
            ],
            "cli": [
                "nmap -sT -p 80,443,22 192.168.1.10",
                "nmap -sT -p 1-1024 192.168.1.10",
                "nc -zv 192.168.1.10 22",
                "ss -tlnp",
            ],
        },
        "es": {
            "desc": "Escanea puertos TCP de un host mediante conexión directa (sin root). Rangos de puertos, presets comunes (Web, Mail, SSH…), servicio identificado por puerto abierto. Hasta 200 hilos.",
            "examples": [
                "Verificar que los puertos 80 y 443 están abiertos en un servidor web.",
                "Detectar los servicios activos en un servidor antes de acceder.",
                "Confirmar que el puerto SSH (22) está cerrado en una máquina expuesta.",
                "Buscar puertos inusuales en un dispositivo sospechoso.",
            ],
            "cli": [
                "nmap -sT -p 80,443,22 192.168.1.10",
                "nmap -sT -p 1-1024 192.168.1.10",
                "nc -zv 192.168.1.10 22",
                "ss -tlnp",
            ],
        },
        "de": {
            "desc": "Scannt TCP-Ports eines Hosts per Direktverbindung (kein Root). Port-Bereiche, gängige Presets (Web, Mail, SSH…), erkannter Dienst pro offenem Port. Bis zu 200 Threads.",
            "examples": [
                "Prüfen, ob Ports 80 und 443 auf einem Webserver offen sind.",
                "Aktive Dienste auf einem Server erkennen, bevor darauf zugegriffen wird.",
                "Sicherstellen, dass SSH-Port (22) auf einer exponierten Maschine geschlossen ist.",
                "Auf ungewöhnliche Ports auf einem verdächtigen Gerät suchen.",
            ],
            "cli": [
                "nmap -sT -p 80,443,22 192.168.1.10",
                "nmap -sT -p 1-1024 192.168.1.10",
                "nc -zv 192.168.1.10 22",
                "ss -tlnp",
            ],
        },
        "it": {
            "desc": "Scansiona le porte TCP di un host tramite connessione diretta (senza root). Intervalli di porte, preset comuni (Web, Mail, SSH…), servizio identificato per ogni porta aperta. Fino a 200 thread.",
            "examples": [
                "Verificare che le porte 80 e 443 siano aperte su un server web.",
                "Rilevare i servizi attivi su un server prima di accedervi.",
                "Confermare che la porta SSH (22) sia chiusa su una macchina esposta.",
                "Cercare porte insolite su un dispositivo sospetto.",
            ],
            "cli": [
                "nmap -sT -p 80,443,22 192.168.1.10",
                "nmap -sT -p 1-1024 192.168.1.10",
                "nc -zv 192.168.1.10 22",
                "ss -tlnp",
            ],
        },
        "pt": {
            "desc": "Analisa portas TCP de um host por ligação direta (sem root). Intervalos de portas, presets comuns (Web, Mail, SSH…), serviço identificado por porta aberta. Até 200 threads.",
            "examples": [
                "Verificar se as portas 80 e 443 estão abertas num servidor web.",
                "Detetar os serviços ativos num servidor antes de aceder.",
                "Confirmar que a porta SSH (22) está fechada numa máquina exposta.",
                "Procurar portas incomuns num dispositivo suspeito.",
            ],
            "cli": [
                "nmap -sT -p 80,443,22 192.168.1.10",
                "nmap -sT -p 1-1024 192.168.1.10",
                "nc -zv 192.168.1.10 22",
                "ss -tlnp",
            ],
        },

        "ja": {
            "desc": "ルート不要の直接接続でホストのTCPポートをスキャン。ポート範囲、一般的なプリセット（Web、Mail、SSH…）、開いているポートのサービスを識別。最大200スレッド。",
            "examples": [
                "Webサーバーのポート80と443が開いていることを確認する。",
                "アクセス前にサーバーのアクティブなサービスを検出する。",
                "インターネット側のマシンでSSHポート（22）が閉じていることを確認する。",
                "不審なデバイスで異常なポートを探す。",
            ],
            "cli": [
                "nmap -sT -p 80,443,22 192.168.1.10",
                "nmap -sT -p 1-1024 192.168.1.10",
                "nc -zv 192.168.1.10 22",
                "ss -tlnp",
            ],
        },
        "zh": {
            "desc": "通过直接连接（无需root）扫描主机的TCP端口。支持端口范围、常用预设（Web、Mail、SSH…），识别每个开放端口的服务。最多200个线程。",
            "examples": [
                "验证Web服务器的80和443端口是否开放。",
                "访问前检测服务器上的活动服务。",
                "确认面向互联网的机器上SSH端口（22）已关闭。",
                "在可疑设备上查找异常端口。",
            ],
            "cli": [
                "nmap -sT -p 80,443,22 192.168.1.10",
                "nmap -sT -p 1-1024 192.168.1.10",
                "nc -zv 192.168.1.10 22",
                "ss -tlnp",
            ],
        },
    },
    "Nmap": {
        "fr": {
            "desc": "Scan réseau avancé via nmap : 7 modes (découverte, TCP, SYN, services/versions, OS, complet, NSE). Résultats XML parsés dans un tableau structuré. Export CSV/TXT.",
            "examples": [
                "Identifier l'OS d'un équipement inconnu (mode OS detection).",
                "Découvrir les versions exactes des services pour évaluer les vulnérabilités.",
                "Effectuer un scan SYN furtif (nécessite root).",
                "Lancer des scripts NSE pour détecter des vulnérabilités connues.",
            ],
            "cli": [
                "nmap -sV -p 1-1024 192.168.1.10",
                "nmap -O 192.168.1.10",
                "sudo nmap -sS 192.168.1.0/24",
                "nmap --script ssl-cert 192.168.1.10",
            ],
        },
        "en": {
            "desc": "Advanced network scanning via nmap: 7 modes (discovery, TCP, SYN, service/version, OS, full, NSE scripts). XML results parsed into a structured table. CSV/TXT export.",
            "examples": [
                "Identify the OS of an unknown device (OS detection mode).",
                "Discover exact service versions to assess vulnerabilities.",
                "Run a stealthy SYN scan (requires root).",
                "Launch NSE scripts to detect known vulnerabilities.",
            ],
            "cli": [
                "nmap -sV -p 1-1024 192.168.1.10",
                "nmap -O 192.168.1.10",
                "sudo nmap -sS 192.168.1.0/24",
                "nmap --script ssl-cert 192.168.1.10",
            ],
        },
        "es": {
            "desc": "Escaneo de red avanzado mediante nmap: 7 modos (descubrimiento, TCP, SYN, servicios/versión, OS, completo, NSE). Resultados XML analizados en una tabla estructurada. Exportación CSV/TXT.",
            "examples": [
                "Identificar el OS de un dispositivo desconocido (modo detección OS).",
                "Descubrir las versiones exactas de servicios para evaluar vulnerabilidades.",
                "Realizar un escaneo SYN silencioso (requiere root).",
                "Lanzar scripts NSE para detectar vulnerabilidades conocidas.",
            ],
            "cli": [
                "nmap -sV -p 1-1024 192.168.1.10",
                "nmap -O 192.168.1.10",
                "sudo nmap -sS 192.168.1.0/24",
                "nmap --script ssl-cert 192.168.1.10",
            ],
        },
        "de": {
            "desc": "Erweiterter Netzwerkscan über nmap: 7 Modi (Entdeckung, TCP, SYN, Dienst/Version, OS, vollständig, NSE-Skripte). XML-Ergebnisse in strukturierter Tabelle geparst. CSV/TXT-Export.",
            "examples": [
                "OS eines unbekannten Geräts identifizieren (OS-Erkennungsmodus).",
                "Exakte Dienstversionen zur Schwachstellenbewertung entdecken.",
                "Unauffälligen SYN-Scan durchführen (Root erforderlich).",
                "NSE-Skripte zur Erkennung bekannter Schwachstellen starten.",
            ],
            "cli": [
                "nmap -sV -p 1-1024 192.168.1.10",
                "nmap -O 192.168.1.10",
                "sudo nmap -sS 192.168.1.0/24",
                "nmap --script ssl-cert 192.168.1.10",
            ],
        },
        "it": {
            "desc": "Scansione di rete avanzata tramite nmap: 7 modalità (scoperta, TCP, SYN, servizi/versione, OS, completo, NSE). Risultati XML analizzati in tabella strutturata. Export CSV/TXT.",
            "examples": [
                "Identificare l'OS di un dispositivo sconosciuto (modalità OS detection).",
                "Scoprire le versioni esatte dei servizi per valutare le vulnerabilità.",
                "Eseguire una scansione SYN furtiva (richiede root).",
                "Lanciare script NSE per rilevare vulnerabilità note.",
            ],
            "cli": [
                "nmap -sV -p 1-1024 192.168.1.10",
                "nmap -O 192.168.1.10",
                "sudo nmap -sS 192.168.1.0/24",
                "nmap --script ssl-cert 192.168.1.10",
            ],
        },
        "pt": {
            "desc": "Análise avançada de rede via nmap: 7 modos (descoberta, TCP, SYN, serviços/versão, OS, completo, NSE). Resultados XML analisados em tabela estruturada. Exportação CSV/TXT.",
            "examples": [
                "Identificar o OS de um dispositivo desconhecido (modo deteção OS).",
                "Descobrir as versões exatas dos serviços para avaliar vulnerabilidades.",
                "Executar uma análise SYN furtiva (requer root).",
                "Lançar scripts NSE para detetar vulnerabilidades conhecidas.",
            ],
            "cli": [
                "nmap -sV -p 1-1024 192.168.1.10",
                "nmap -O 192.168.1.10",
                "sudo nmap -sS 192.168.1.0/24",
                "nmap --script ssl-cert 192.168.1.10",
            ],
        },

        "ja": {
            "desc": "nmapによる高度なネットワークスキャン：7つのモード（検出、TCP、SYN、サービス/バージョン、OS、フル、NSEスクリプト）。XML結果を構造化テーブルに解析。CSV/TXTエクスポート。",
            "examples": [
                "未知のデバイスのOSを特定する（OS検出モード）。",
                "脆弱性を評価するためにサービスの正確なバージョンを検出する。",
                "ステルスSYNスキャンを実行する（rootが必要）。",
                "NSEスクリプトを使って既知の脆弱性を検出する。",
            ],
            "cli": [
                "nmap -sV -p 1-1024 192.168.1.10",
                "nmap -O 192.168.1.10",
                "sudo nmap -sS 192.168.1.0/24",
                "nmap --script ssl-cert 192.168.1.10",
            ],
        },
        "zh": {
            "desc": "通过nmap进行高级网络扫描：7种模式（发现、TCP、SYN、服务/版本、OS、完整、NSE脚本）。XML结果解析为结构化表格。支持CSV/TXT导出。",
            "examples": [
                "识别未知设备的操作系统（OS检测模式）。",
                "发现确切的服务版本以评估漏洞。",
                "执行隐蔽的SYN扫描（需要root）。",
                "运行NSE脚本检测已知漏洞。",
            ],
            "cli": [
                "nmap -sV -p 1-1024 192.168.1.10",
                "nmap -O 192.168.1.10",
                "sudo nmap -sS 192.168.1.0/24",
                "nmap --script ssl-cert 192.168.1.10",
            ],
        },
    },
    "Whois": {
        "fr": {
            "desc": "Requête WHOIS sur un nom de domaine ou une adresse IP. Affiche les informations d'enregistrement, contacts administratifs et plages IP d'opérateur en format monospace brut.",
            "examples": [
                "Vérifier la date d'expiration d'un nom de domaine.",
                "Identifier le registrar et le propriétaire d'un domaine suspect.",
                "Retrouver l'opérateur réseau (AS) derrière une IP.",
                "Obtenir les contacts abus pour signaler un comportement malveillant.",
            ],
            "cli": [
                "whois example.com",
                "whois 8.8.8.8",
                "whois -h whois.iana.org example.com",
            ],
        },
        "en": {
            "desc": "WHOIS query on a domain name or IP address. Shows registration info, admin contacts and operator IP ranges in raw monospace format.",
            "examples": [
                "Check the expiry date of a domain name.",
                "Identify the registrar and owner of a suspicious domain.",
                "Find the network operator (AS) behind an IP.",
                "Get abuse contacts to report malicious behavior.",
            ],
            "cli": [
                "whois example.com",
                "whois 8.8.8.8",
                "whois -h whois.iana.org example.com",
            ],
        },
        "es": {
            "desc": "Consulta WHOIS sobre un nombre de dominio o dirección IP. Muestra información de registro, contactos administrativos y rangos IP del operador en formato monoespaciado sin procesar.",
            "examples": [
                "Verificar la fecha de expiración de un dominio.",
                "Identificar el registrar y propietario de un dominio sospechoso.",
                "Encontrar el operador de red (AS) detrás de una IP.",
                "Obtener contactos de abuso para reportar comportamiento malicioso.",
            ],
            "cli": [
                "whois example.com",
                "whois 8.8.8.8",
                "whois -h whois.iana.org example.com",
            ],
        },
        "de": {
            "desc": "WHOIS-Abfrage für einen Domainnamen oder eine IP-Adresse. Zeigt Registrierungsdaten, Admin-Kontakte und Operator-IP-Bereiche im rohen Monospace-Format.",
            "examples": [
                "Ablaufdatum eines Domainnamens prüfen.",
                "Registrar und Inhaber einer verdächtigen Domain identifizieren.",
                "Netzwerkbetreiber (AS) hinter einer IP ermitteln.",
                "Missbrauchs-Kontakte für Meldungen schädlichen Verhaltens erhalten.",
            ],
            "cli": [
                "whois example.com",
                "whois 8.8.8.8",
                "whois -h whois.iana.org example.com",
            ],
        },
        "it": {
            "desc": "Query WHOIS su un nome di dominio o indirizzo IP. Mostra informazioni di registrazione, contatti amministrativi e intervalli IP dell'operatore in formato monospace grezzo.",
            "examples": [
                "Verificare la data di scadenza di un nome di dominio.",
                "Identificare il registrar e il proprietario di un dominio sospetto.",
                "Trovare l'operatore di rete (AS) dietro un IP.",
                "Ottenere i contatti per abusi per segnalare comportamenti dannosi.",
            ],
            "cli": [
                "whois example.com",
                "whois 8.8.8.8",
                "whois -h whois.iana.org example.com",
            ],
        },
        "pt": {
            "desc": "Consulta WHOIS sobre um nome de domínio ou endereço IP. Mostra informações de registo, contactos administrativos e intervalos IP do operador em formato monospace sem formatação.",
            "examples": [
                "Verificar a data de expiração de um nome de domínio.",
                "Identificar o registrar e proprietário de um domínio suspeito.",
                "Encontrar o operador de rede (AS) por trás de um IP.",
                "Obter contactos de abuso para reportar comportamento malicioso.",
            ],
            "cli": [
                "whois example.com",
                "whois 8.8.8.8",
                "whois -h whois.iana.org example.com",
            ],
        },

        "ja": {
            "desc": "ドメイン名またはIPアドレスへのWHOISクエリ。登録情報、管理者連絡先、オペレーターのIP範囲を生のモノスペースフォーマットで表示。",
            "examples": [
                "ドメイン名の有効期限を確認する。",
                "不審なドメインのレジストラと所有者を特定する。",
                "IPの背後にあるネットワーク事業者（AS）を調べる。",
                "悪意のある行為を報告するための不正連絡先を取得する。",
            ],
            "cli": [
                "whois example.com",
                "whois 8.8.8.8",
                "whois -h whois.iana.org example.com",
            ],
        },
        "zh": {
            "desc": "对域名或IP地址进行WHOIS查询。以原始等宽格式显示注册信息、管理联系人和运营商IP范围。",
            "examples": [
                "检查域名的到期日期。",
                "识别可疑域名的注册商和所有者。",
                "查找IP背后的网络运营商（AS）。",
                "获取滥用联系方式以举报恶意行为。",
            ],
            "cli": [
                "whois example.com",
                "whois 8.8.8.8",
                "whois -h whois.iana.org example.com",
            ],
        },
    },
    "TLS Inspector": {
        "fr": {
            "desc": "Inspecte le certificat TLS/SSL d'un serveur : CN, SANs, émetteur, validité (vert/orange/rouge), numéro de série, protocole, cipher et chaîne complète via openssl. Fonctionne sur certificats valides, expirés et auto-signés.",
            "examples": [
                "Vérifier l'expiration d'un certificat avant interruption de service.",
                "Contrôler les SANs d'un certificat multi-domaine.",
                "Diagnostiquer des erreurs TLS via le protocole et le cipher.",
                "Inspecter la chaîne de certification d'un CA privé interne.",
            ],
            "cli": [
                "openssl s_client -connect example.com:443 </dev/null 2>/dev/null | openssl x509 -noout -dates -subject",
                "openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null",
                "curl -vI https://example.com 2>&1 | grep -E 'expire|issuer|subject'",
            ],
        },
        "en": {
            "desc": "Inspects a server's TLS/SSL certificate: CN, SANs, issuer, validity (green/orange/red), serial, protocol, cipher and full chain via openssl. Works on valid, expired and self-signed certificates.",
            "examples": [
                "Check certificate expiry before it causes a service outage.",
                "Verify the SANs on a multi-domain certificate.",
                "Diagnose TLS errors by inspecting protocol and cipher.",
                "Inspect the certificate chain of an internal private CA.",
            ],
            "cli": [
                "openssl s_client -connect example.com:443 </dev/null 2>/dev/null | openssl x509 -noout -dates -subject",
                "openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null",
                "curl -vI https://example.com 2>&1 | grep -E 'expire|issuer|subject'",
            ],
        },
        "es": {
            "desc": "Inspecciona el certificado TLS/SSL de un servidor: CN, SANs, emisor, validez (verde/naranja/rojo), serie, protocolo, cipher y cadena completa via openssl. Funciona con certificados válidos, expirados y autofirmados.",
            "examples": [
                "Verificar la expiración de un certificado antes de que cause una interrupción.",
                "Controlar los SANs de un certificado multi-dominio.",
                "Diagnosticar errores TLS inspeccionando el protocolo y el cipher.",
                "Inspeccionar la cadena de certificación de una CA privada interna.",
            ],
            "cli": [
                "openssl s_client -connect example.com:443 </dev/null 2>/dev/null | openssl x509 -noout -dates -subject",
                "openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null",
                "curl -vI https://example.com 2>&1 | grep -E 'expire|issuer|subject'",
            ],
        },
        "de": {
            "desc": "Prüft das TLS/SSL-Zertifikat eines Servers: CN, SANs, Aussteller, Gültigkeit (grün/orange/rot), Seriennummer, Protokoll, Cipher und vollständige Kette über openssl. Funktioniert mit gültigen, abgelaufenen und selbstsignierten Zertifikaten.",
            "examples": [
                "Zertifikatsablauf prüfen, bevor es zu einem Dienstausfall kommt.",
                "SANs eines Multi-Domain-Zertifikats überprüfen.",
                "TLS-Fehler durch Protokoll- und Cipher-Inspektion diagnostizieren.",
                "Zertifikatskette einer internen privaten CA prüfen.",
            ],
            "cli": [
                "openssl s_client -connect example.com:443 </dev/null 2>/dev/null | openssl x509 -noout -dates -subject",
                "openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null",
                "curl -vI https://example.com 2>&1 | grep -E 'expire|issuer|subject'",
            ],
        },
        "it": {
            "desc": "Ispeziona il certificato TLS/SSL di un server: CN, SAN, emittente, validità (verde/arancione/rosso), seriale, protocollo, cipher e catena completa via openssl. Funziona su certificati validi, scaduti e autofirmati.",
            "examples": [
                "Verificare la scadenza di un certificato prima che causi un'interruzione del servizio.",
                "Controllare i SAN di un certificato multi-dominio.",
                "Diagnosticare errori TLS ispezionando protocollo e cipher.",
                "Ispezionare la catena di certificazione di una CA privata interna.",
            ],
            "cli": [
                "openssl s_client -connect example.com:443 </dev/null 2>/dev/null | openssl x509 -noout -dates -subject",
                "openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null",
                "curl -vI https://example.com 2>&1 | grep -E 'expire|issuer|subject'",
            ],
        },
        "pt": {
            "desc": "Inspeciona o certificado TLS/SSL de um servidor: CN, SAN, emissor, validade (verde/laranja/vermelho), série, protocolo, cipher e cadeia completa via openssl. Funciona com certificados válidos, expirados e autoassinados.",
            "examples": [
                "Verificar a expiração de um certificado antes de causar uma interrupção.",
                "Controlar os SAN de um certificado multi-domínio.",
                "Diagnosticar erros TLS inspecionando protocolo e cipher.",
                "Inspecionar a cadeia de certificação de uma CA privada interna.",
            ],
            "cli": [
                "openssl s_client -connect example.com:443 </dev/null 2>/dev/null | openssl x509 -noout -dates -subject",
                "openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null",
                "curl -vI https://example.com 2>&1 | grep -E 'expire|issuer|subject'",
            ],
        },

        "ja": {
            "desc": "サーバーのTLS/SSL証明書を検査：CN、SAN、発行者、有効性（緑/橙/赤）、シリアル番号、プロトコル、暗号スイート、openssl経由の完全なチェーン。有効・期限切れ・自己署名証明書に対応。",
            "examples": [
                "サービス停止前に証明書の有効期限を確認する。",
                "マルチドメイン証明書のSANを確認する。",
                "プロトコルと暗号スイートを調査してTLSエラーを診断する。",
                "内部プライベートCAの証明書チェーンを検査する。",
            ],
            "cli": [
                "openssl s_client -connect example.com:443 </dev/null 2>/dev/null | openssl x509 -noout -dates -subject",
                "openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null",
                "curl -vI https://example.com 2>&1 | grep -E 'expire|issuer|subject'",
            ],
        },
        "zh": {
            "desc": "检查服务器的TLS/SSL证书：CN、SAN、颁发者、有效性（绿/橙/红）、序列号、协议、加密套件及通过openssl获取的完整链。支持有效、过期和自签名证书。",
            "examples": [
                "在证书导致服务中断前检查其到期时间。",
                "验证多域名证书的SAN。",
                "通过检查协议和加密套件诊断TLS错误。",
                "检查内部私有CA的证书链。",
            ],
            "cli": [
                "openssl s_client -connect example.com:443 </dev/null 2>/dev/null | openssl x509 -noout -dates -subject",
                "openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null",
                "curl -vI https://example.com 2>&1 | grep -E 'expire|issuer|subject'",
            ],
        },
    },
    "SMB / NFS": {
        "fr": {
            "desc": "Liste les partages SMB/Samba et les exports NFS d'un serveur ou NAS. SMB via smbclient -L (identifiants optionnels), NFS via showmount -e.",
            "examples": [
                "Voir tous les partages disponibles sur un NAS.",
                "Vérifier quels répertoires sont exportés en NFS.",
                "Accéder à un partage Samba avec des identifiants de domaine.",
                "Diagnostiquer pourquoi un partage réseau n'est pas accessible.",
            ],
            "cli": [
                "smbclient -L //192.168.1.100 -N",
                "smbclient -L //192.168.1.100 -U user%password",
                "showmount -e 192.168.1.100",
                "mount -t nfs 192.168.1.100:/export /mnt/nfs",
            ],
        },
        "en": {
            "desc": "Lists SMB/Samba shares and NFS exports from a server or NAS. SMB via smbclient -L (optional credentials), NFS via showmount -e.",
            "examples": [
                "See all available shares on a NAS.",
                "Check which directories are exported via NFS.",
                "Access a Samba share with domain credentials.",
                "Diagnose why a network share is not accessible.",
            ],
            "cli": [
                "smbclient -L //192.168.1.100 -N",
                "smbclient -L //192.168.1.100 -U user%password",
                "showmount -e 192.168.1.100",
                "mount -t nfs 192.168.1.100:/export /mnt/nfs",
            ],
        },
        "es": {
            "desc": "Lista los recursos compartidos SMB/Samba y las exportaciones NFS de un servidor o NAS. SMB via smbclient -L (credenciales opcionales), NFS via showmount -e.",
            "examples": [
                "Ver todos los recursos disponibles en un NAS.",
                "Verificar qué directorios se exportan por NFS.",
                "Acceder a un recurso Samba con credenciales de dominio.",
                "Diagnosticar por qué un recurso de red no es accesible.",
            ],
            "cli": [
                "smbclient -L //192.168.1.100 -N",
                "smbclient -L //192.168.1.100 -U user%password",
                "showmount -e 192.168.1.100",
                "mount -t nfs 192.168.1.100:/export /mnt/nfs",
            ],
        },
        "de": {
            "desc": "Listet SMB/Samba-Freigaben und NFS-Exporte eines Servers oder NAS. SMB über smbclient -L (optionale Zugangsdaten), NFS über showmount -e.",
            "examples": [
                "Alle verfügbaren Freigaben auf einem NAS anzeigen.",
                "Prüfen, welche Verzeichnisse über NFS exportiert werden.",
                "Auf eine Samba-Freigabe mit Domain-Anmeldedaten zugreifen.",
                "Diagnostizieren, warum eine Netzwerkfreigabe nicht erreichbar ist.",
            ],
            "cli": [
                "smbclient -L //192.168.1.100 -N",
                "smbclient -L //192.168.1.100 -U user%password",
                "showmount -e 192.168.1.100",
                "mount -t nfs 192.168.1.100:/export /mnt/nfs",
            ],
        },
        "it": {
            "desc": "Elenca le condivisioni SMB/Samba e le esportazioni NFS di un server o NAS. SMB via smbclient -L (credenziali opzionali), NFS via showmount -e.",
            "examples": [
                "Vedere tutte le condivisioni disponibili su un NAS.",
                "Verificare quali directory vengono esportate via NFS.",
                "Accedere a una condivisione Samba con credenziali di dominio.",
                "Diagnosticare perché una condivisione di rete non è accessibile.",
            ],
            "cli": [
                "smbclient -L //192.168.1.100 -N",
                "smbclient -L //192.168.1.100 -U user%password",
                "showmount -e 192.168.1.100",
                "mount -t nfs 192.168.1.100:/export /mnt/nfs",
            ],
        },
        "pt": {
            "desc": "Lista as partilhas SMB/Samba e as exportações NFS de um servidor ou NAS. SMB via smbclient -L (credenciais opcionais), NFS via showmount -e.",
            "examples": [
                "Ver todas as partilhas disponíveis num NAS.",
                "Verificar quais diretórios são exportados via NFS.",
                "Aceder a uma partilha Samba com credenciais de domínio.",
                "Diagnosticar por que uma partilha de rede não está acessível.",
            ],
            "cli": [
                "smbclient -L //192.168.1.100 -N",
                "smbclient -L //192.168.1.100 -U user%password",
                "showmount -e 192.168.1.100",
                "mount -t nfs 192.168.1.100:/export /mnt/nfs",
            ],
        },

        "ja": {
            "desc": "サーバーまたはNASのSMB/Samba共有とNFSエクスポートを一覧表示。SMBはsmbclient -L（オプションの認証情報）、NFSはshowmount -e経由。",
            "examples": [
                "NASで利用可能なすべての共有を確認する。",
                "NFS経由でエクスポートされているディレクトリを確認する。",
                "ドメイン認証情報でSamba共有にアクセスする。",
                "ネットワーク共有にアクセスできない原因を診断する。",
            ],
            "cli": [
                "smbclient -L //192.168.1.100 -N",
                "smbclient -L //192.168.1.100 -U user%password",
                "showmount -e 192.168.1.100",
                "mount -t nfs 192.168.1.100:/export /mnt/nfs",
            ],
        },
        "zh": {
            "desc": "列出服务器或NAS上的SMB/Samba共享和NFS导出。SMB通过smbclient -L（可选凭据），NFS通过showmount -e。",
            "examples": [
                "查看NAS上所有可用的共享。",
                "检查哪些目录通过NFS导出。",
                "使用域凭据访问Samba共享。",
                "诊断网络共享无法访问的原因。",
            ],
            "cli": [
                "smbclient -L //192.168.1.100 -N",
                "smbclient -L //192.168.1.100 -U user%password",
                "showmount -e 192.168.1.100",
                "mount -t nfs 192.168.1.100:/export /mnt/nfs",
            ],
        },
    },
    "Hosts File": {
        "fr": {
            "desc": "Affiche et édite /etc/hosts dans une interface tabulaire. Ajouter, modifier, supprimer ou activer/désactiver des entrées. Sauvegarde via pkexec (authentification polkit).",
            "examples": [
                "Ajouter un alias local : monserveur.local → 192.168.1.10.",
                "Bloquer un domaine en le redirigeant vers 0.0.0.0.",
                "Désactiver temporairement une entrée sans la supprimer.",
                "Forcer une IP localement avant la propagation DNS.",
            ],
            "cli": [
                "cat /etc/hosts",
                "sudo bash -c 'echo \"192.168.1.10 monserveur.local\" >> /etc/hosts'",
                "getent hosts monserveur.local",
            ],
        },
        "en": {
            "desc": "Displays and edits /etc/hosts in a table UI. Add, edit, delete or enable/disable entries. Saves via pkexec (polkit authentication).",
            "examples": [
                "Add a local alias: myserver.local → 192.168.1.10.",
                "Block a domain by redirecting it to 0.0.0.0.",
                "Temporarily disable an entry without deleting it.",
                "Force a local IP before DNS propagation.",
            ],
            "cli": [
                "cat /etc/hosts",
                "sudo bash -c 'echo \"192.168.1.10 myserver.local\" >> /etc/hosts'",
                "getent hosts myserver.local",
            ],
        },
        "es": {
            "desc": "Muestra y edita /etc/hosts en una interfaz tabular. Agregar, modificar, eliminar o activar/desactivar entradas. Guarda via pkexec (autenticación polkit).",
            "examples": [
                "Agregar un alias local: miservidor.local → 192.168.1.10.",
                "Bloquear un dominio redirigiéndolo a 0.0.0.0.",
                "Desactivar temporalmente una entrada sin eliminarla.",
                "Forzar una IP localmente antes de la propagación DNS.",
            ],
            "cli": [
                "cat /etc/hosts",
                "sudo bash -c 'echo \"192.168.1.10 miservidor.local\" >> /etc/hosts'",
                "getent hosts miservidor.local",
            ],
        },
        "de": {
            "desc": "Zeigt /etc/hosts in einer Tabellenoberfläche an und bearbeitet es. Einträge hinzufügen, bearbeiten, löschen oder aktivieren/deaktivieren. Speichert über pkexec (polkit-Authentifizierung).",
            "examples": [
                "Lokalen Alias hinzufügen: meinserver.local → 192.168.1.10.",
                "Eine Domain durch Umleitung auf 0.0.0.0 blockieren.",
                "Einen Eintrag vorübergehend deaktivieren, ohne ihn zu löschen.",
                "Eine lokale IP vor der DNS-Propagation erzwingen.",
            ],
            "cli": [
                "cat /etc/hosts",
                "sudo bash -c 'echo \"192.168.1.10 meinserver.local\" >> /etc/hosts'",
                "getent hosts meinserver.local",
            ],
        },
        "it": {
            "desc": "Visualizza e modifica /etc/hosts in un'interfaccia tabellare. Aggiungere, modificare, eliminare o attivare/disattivare voci. Salvataggio via pkexec (autenticazione polkit).",
            "examples": [
                "Aggiungere un alias locale: mioserver.local → 192.168.1.10.",
                "Bloccare un dominio reindirizzandolo a 0.0.0.0.",
                "Disabilitare temporaneamente una voce senza eliminarla.",
                "Forzare un IP locale prima della propagazione DNS.",
            ],
            "cli": [
                "cat /etc/hosts",
                "sudo bash -c 'echo \\\"192.168.1.10 myserver.local\\\" >> /etc/hosts'",
                "getent hosts myserver.local",
            ],
        },
        "pt": {
            "desc": "Apresenta e edita /etc/hosts numa interface tabular. Adicionar, editar, eliminar ou ativar/desativar entradas. Guarda via pkexec (autenticação polkit).",
            "examples": [
                "Adicionar um alias local: meuservidor.local → 192.168.1.10.",
                "Bloquear um domínio redirecionando-o para 0.0.0.0.",
                "Desativar temporariamente uma entrada sem a eliminar.",
                "Forçar um IP local antes da propagação DNS.",
            ],
            "cli": [
                "cat /etc/hosts",
                "sudo bash -c 'echo \\\"192.168.1.10 myserver.local\\\" >> /etc/hosts'",
                "getent hosts myserver.local",
            ],
        },

        "ja": {
            "desc": "/etc/hostsをテーブルUIで表示・編集。エントリの追加・編集・削除・有効化/無効化。pkexec（polkit認証）経由で保存。",
            "examples": [
                "ローカルエイリアスを追加：myserver.local → 192.168.1.10。",
                "ドメインを0.0.0.0にリダイレクトしてブロックする。",
                "エントリを削除せずに一時的に無効化する。",
                "DNS伝播前にローカルIPを強制する。",
            ],
            "cli": [
                "cat /etc/hosts",
                "sudo bash -c 'echo \"192.168.1.10 myserver.local\" >> /etc/hosts'",
                "getent hosts myserver.local",
            ],
        },
        "zh": {
            "desc": "在表格界面中显示和编辑/etc/hosts。添加、编辑、删除或启用/禁用条目。通过pkexec（polkit认证）保存。",
            "examples": [
                "添加本地别名：myserver.local → 192.168.1.10。",
                "通过重定向到0.0.0.0来屏蔽域名。",
                "临时禁用条目而不删除它。",
                "在DNS传播前强制使用本地IP。",
            ],
            "cli": [
                "cat /etc/hosts",
                "sudo bash -c 'echo \"192.168.1.10 myserver.local\" >> /etc/hosts'",
                "getent hosts myserver.local",
            ],
        },
    },
    "SNMP": {
        "fr": {
            "desc": "Interroge des équipements réseau SNMP (routeurs, switches, NAS…) via snmpwalk/snmpget. Supporte v1/v2c avec 10 presets d'OID courants (nom système, uptime, interfaces, CPU, mémoire…).",
            "examples": [
                "Lire l'uptime d'un switch ou d'un routeur.",
                "Récupérer la liste des interfaces d'un équipement.",
                "Interroger la charge CPU d'un serveur compatible SNMP.",
                "Tester la communauté SNMP avant intégration dans un outil de supervision.",
            ],
            "cli": [
                "snmpwalk -v2c -c public 192.168.1.1 system",
                "snmpget -v2c -c public 192.168.1.1 sysDescr.0",
                "snmpwalk -v2c -c public 192.168.1.1 ifTable",
                "snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.2.1.25.3.3.1.2",
            ],
        },
        "en": {
            "desc": "Queries SNMP-compatible network devices (routers, switches, NAS…) via snmpwalk/snmpget. Supports v1/v2c with 10 common OID presets (system name, uptime, interfaces, CPU, memory…).",
            "examples": [
                "Read the uptime of a switch or router.",
                "Retrieve the interface list of a device.",
                "Query CPU load on an SNMP-compatible server.",
                "Test the SNMP community before integrating into a monitoring tool.",
            ],
            "cli": [
                "snmpwalk -v2c -c public 192.168.1.1 system",
                "snmpget -v2c -c public 192.168.1.1 sysDescr.0",
                "snmpwalk -v2c -c public 192.168.1.1 ifTable",
                "snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.2.1.25.3.3.1.2",
            ],
        },
        "es": {
            "desc": "Consulta dispositivos de red compatibles con SNMP (routers, switches, NAS…) via snmpwalk/snmpget. Soporta v1/v2c con 10 presets de OID comunes (nombre sistema, uptime, interfaces, CPU, memoria…).",
            "examples": [
                "Leer el uptime de un switch o router.",
                "Recuperar la lista de interfaces de un dispositivo.",
                "Consultar la carga de CPU de un servidor compatible con SNMP.",
                "Probar la comunidad SNMP antes de integrarla en una herramienta de monitoreo.",
            ],
            "cli": [
                "snmpwalk -v2c -c public 192.168.1.1 system",
                "snmpget -v2c -c public 192.168.1.1 sysDescr.0",
                "snmpwalk -v2c -c public 192.168.1.1 ifTable",
                "snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.2.1.25.3.3.1.2",
            ],
        },
        "de": {
            "desc": "Fragt SNMP-kompatible Netzwerkgeräte (Router, Switches, NAS…) über snmpwalk/snmpget ab. Unterstützt v1/v2c mit 10 gängigen OID-Presets (Systemname, Uptime, Interfaces, CPU, Speicher…).",
            "examples": [
                "Uptime eines Switches oder Routers auslesen.",
                "Schnittstellenliste eines Geräts abrufen.",
                "CPU-Last eines SNMP-kompatiblen Servers abfragen.",
                "SNMP-Community testen, bevor sie in ein Monitoring-Tool integriert wird.",
            ],
            "cli": [
                "snmpwalk -v2c -c public 192.168.1.1 system",
                "snmpget -v2c -c public 192.168.1.1 sysDescr.0",
                "snmpwalk -v2c -c public 192.168.1.1 ifTable",
                "snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.2.1.25.3.3.1.2",
            ],
        },
        "it": {
            "desc": "Interroga dispositivi di rete compatibili SNMP (router, switch, NAS…) via snmpwalk/snmpget. Supporta v1/v2c con 10 preset OID comuni (nome sistema, uptime, interfacce, CPU, memoria…).",
            "examples": [
                "Leggere l'uptime di uno switch o router.",
                "Recuperare la lista delle interfacce di un dispositivo.",
                "Interrogare il carico CPU di un server compatibile SNMP.",
                "Testare la community SNMP prima di integrarla in uno strumento di monitoraggio.",
            ],
            "cli": [
                "snmpwalk -v2c -c public 192.168.1.1 system",
                "snmpget -v2c -c public 192.168.1.1 sysDescr.0",
                "snmpwalk -v2c -c public 192.168.1.1 ifTable",
                "snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.2.1.25.3.3.1.2",
            ],
        },
        "pt": {
            "desc": "Consulta dispositivos de rede compatíveis SNMP (routers, switches, NAS…) via snmpwalk/snmpget. Suporta v1/v2c com 10 presets OID comuns (nome sistema, uptime, interfaces, CPU, memória…).",
            "examples": [
                "Ler o uptime de um switch ou router.",
                "Recuperar a lista de interfaces de um dispositivo.",
                "Consultar a carga de CPU de um servidor compatível SNMP.",
                "Testar a community SNMP antes de integrar numa ferramenta de monitorização.",
            ],
            "cli": [
                "snmpwalk -v2c -c public 192.168.1.1 system",
                "snmpget -v2c -c public 192.168.1.1 sysDescr.0",
                "snmpwalk -v2c -c public 192.168.1.1 ifTable",
                "snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.2.1.25.3.3.1.2",
            ],
        },
        "ja": {
            "desc": "SNMPに対応したネットワーク機器（ルーター、スイッチ、NAS…）をsnmpwalk/snmpget経由でクエリ。v1/v2cをサポートし、10個の一般的なOIDプリセット（システム名、アップタイム、インターフェース、CPU、メモリ…）を装備。",
            "examples": [
                "スイッチまたはルーターのアップタイムを読み取る。",
                "デバイスのインターフェース一覧を取得する。",
                "SNMP対応サーバーのCPU負荷をクエリする。",
                "監視ツールに統合する前にSNMPコミュニティをテストする。",
            ],
            "cli": [
                "snmpwalk -v2c -c public 192.168.1.1 system",
                "snmpget -v2c -c public 192.168.1.1 sysDescr.0",
                "snmpwalk -v2c -c public 192.168.1.1 ifTable",
                "snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.2.1.25.3.3.1.2",
            ],
        },
        "zh": {
            "desc": "通过snmpwalk/snmpget查询支持SNMP的网络设备（路由器、交换机、NAS…）。支持v1/v2c，内置10个常用OID预设（系统名称、运行时间、接口、CPU、内存…）。",
            "examples": [
                "读取交换机或路由器的运行时间。",
                "获取设备的接口列表。",
                "查询支持SNMP的服务器的CPU负载。",
                "在集成到监控工具前测试SNMP社区字符串。",
            ],
            "cli": [
                "snmpwalk -v2c -c public 192.168.1.1 system",
                "snmpget -v2c -c public 192.168.1.1 sysDescr.0",
                "snmpwalk -v2c -c public 192.168.1.1 ifTable",
                "snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.2.1.25.3.3.1.2",
            ],
        },
    },
    "SNTP / NTP": {
        "fr": {
            "desc": "Teste la synchronisation NTP via un client UDP pur Python (RFC 4330). Affiche offset, délai roundtrip, stratum et source de référence. Jusqu'à 5 requêtes moyennées.",
            "examples": [
                "Vérifier que le serveur NTP local est accessible et répond correctement.",
                "Mesurer la dérive d'horloge d'un serveur.",
                "Tester plusieurs serveurs du pool ntp.org.",
                "Diagnostiquer des erreurs TLS liées à une horloge incorrecte.",
            ],
            "cli": [
                "ntpdate -q pool.ntp.org",
                "chronyc tracking",
                "timedatectl status",
                "sntp -q pool.ntp.org",
            ],
        },
        "en": {
            "desc": "Tests NTP synchronization via a pure Python UDP client (RFC 4330). Shows offset, roundtrip delay, stratum and reference source. Up to 5 averaged requests.",
            "examples": [
                "Verify the local NTP server is reachable and responding.",
                "Measure a server's clock drift.",
                "Test multiple ntp.org pool servers.",
                "Diagnose TLS errors caused by an incorrect system clock.",
            ],
            "cli": [
                "ntpdate -q pool.ntp.org",
                "chronyc tracking",
                "timedatectl status",
                "sntp -q pool.ntp.org",
            ],
        },
        "es": {
            "desc": "Prueba la sincronización NTP mediante un cliente UDP Python puro (RFC 4330). Muestra offset, retardo roundtrip, stratum y fuente de referencia. Hasta 5 consultas promediadas.",
            "examples": [
                "Verificar que el servidor NTP local es accesible y responde correctamente.",
                "Medir la deriva del reloj de un servidor.",
                "Probar varios servidores del pool ntp.org.",
                "Diagnosticar errores TLS causados por un reloj del sistema incorrecto.",
            ],
            "cli": [
                "ntpdate -q pool.ntp.org",
                "chronyc tracking",
                "timedatectl status",
                "sntp -q pool.ntp.org",
            ],
        },
        "de": {
            "desc": "Testet NTP-Synchronisation über einen reinen Python-UDP-Client (RFC 4330). Zeigt Offset, Roundtrip-Verzögerung, Stratum und Referenzquelle. Bis zu 5 gemittelte Anfragen.",
            "examples": [
                "Prüfen, ob der lokale NTP-Server erreichbar ist und antwortet.",
                "Uhrenabweichung eines Servers messen.",
                "Mehrere ntp.org-Pool-Server testen.",
                "TLS-Fehler durch eine falsche Systemuhr diagnostizieren.",
            ],
            "cli": [
                "ntpdate -q pool.ntp.org",
                "chronyc tracking",
                "timedatectl status",
                "sntp -q pool.ntp.org",
            ],
        },
        "it": {
            "desc": "Testa la sincronizzazione NTP tramite un client UDP Python puro (RFC 4330). Mostra offset, ritardo roundtrip, stratum e sorgente di riferimento. Fino a 5 richieste mediate.",
            "examples": [
                "Verificare che il server NTP locale sia raggiungibile e risponda.",
                "Misurare la deriva dell'orologio di un server.",
                "Testare più server del pool ntp.org.",
                "Diagnosticare errori TLS causati da un orologio di sistema errato.",
            ],
            "cli": [
                "ntpdate -q pool.ntp.org",
                "chronyc tracking",
                "timedatectl status",
                "sntp -q pool.ntp.org",
            ],
        },
        "pt": {
            "desc": "Testa a sincronização NTP através de um cliente UDP Python puro (RFC 4330). Mostra offset, atraso roundtrip, stratum e fonte de referência. Até 5 pedidos mediados.",
            "examples": [
                "Verificar se o servidor NTP local está acessível e a responder.",
                "Medir o desvio de relógio de um servidor.",
                "Testar múltiplos servidores do pool ntp.org.",
                "Diagnosticar erros TLS causados por um relógio de sistema incorreto.",
            ],
            "cli": [
                "ntpdate -q pool.ntp.org",
                "chronyc tracking",
                "timedatectl status",
                "sntp -q pool.ntp.org",
            ],
        },
        "ja": {
            "desc": "純粋なPython UDPクライアント（RFC 4330）でNTP同期をテスト。オフセット、ラウンドトリップ遅延、ストラタム、参照ソースを表示。最大5回の平均リクエスト。",
            "examples": [
                "ローカルNTPサーバーが到達可能で応答していることを確認する。",
                "サーバーのクロックドリフトを測定する。",
                "ntp.orgプールの複数のサーバーをテストする。",
                "不正なシステムクロックが原因のTLSエラーを診断する。",
            ],
            "cli": [
                "ntpdate -q pool.ntp.org",
                "chronyc tracking",
                "timedatectl status",
                "sntp -q pool.ntp.org",
            ],
        },
        "zh": {
            "desc": "通过纯Python UDP客户端（RFC 4330）测试NTP同步。显示偏移量、往返延迟、层级和参考源。最多对5次请求取平均值。",
            "examples": [
                "验证本地NTP服务器是否可达并正常响应。",
                "测量服务器的时钟漂移。",
                "测试ntp.org池中的多个服务器。",
                "诊断由系统时钟不正确引起的TLS错误。",
            ],
            "cli": [
                "ntpdate -q pool.ntp.org",
                "chronyc tracking",
                "timedatectl status",
                "sntp -q pool.ntp.org",
            ],
        },
    },
    "SSH": {
        "fr": {
            "desc": "Terminal SSH embarqué avec carnet d'adresses hiérarchique (groupes/sous-groupes). Authentification par clé et mot de passe, agent forwarding (-A), scrollback 2000 lignes, PTY dynamique, toutes séquences VT100/xterm.",
            "examples": [
                "Se connecter à un serveur et exécuter des commandes interactivement.",
                "Gérer plusieurs serveurs organisés par groupes (Production, Dev…).",
                "Utiliser Vim, htop ou tout outil TUI dans le terminal embarqué.",
                "Activer l'agent forwarding pour rebondir vers d'autres serveurs sans copier la clé privée (PC → A → B).",
            ],
            "cli": [
                "ssh user@192.168.1.10",
                "ssh -p 2222 user@192.168.1.10",
                "ssh -i ~/.ssh/id_ed25519 user@server.example.com",
                "ssh -A user@serveur-A  # agent forwarding : rebond vers serveur-B possible depuis A",
            ],
        },
        "en": {
            "desc": "Embedded SSH terminal with hierarchical address book (groups/subgroups). Key and password auth, agent forwarding (-A), 2000-line scrollback, dynamic PTY, all VT100/xterm sequences.",
            "examples": [
                "Connect to a server and run commands interactively.",
                "Manage multiple servers organized in groups (Production, Dev…).",
                "Use Vim, htop or any TUI tool in the embedded terminal.",
                "Enable agent forwarding to hop between servers without copying your private key (PC → A → B).",
            ],
            "cli": [
                "ssh user@192.168.1.10",
                "ssh -p 2222 user@192.168.1.10",
                "ssh -i ~/.ssh/id_ed25519 user@server.example.com",
                "ssh -A user@server-A  # agent forwarding: can then SSH to server-B from A",
            ],
        },
        "es": {
            "desc": "Terminal SSH integrado con libreta de direcciones jerárquica (grupos/subgrupos). Autenticación por clave y contraseña, reenvío de agente (-A), scrollback de 2000 líneas, PTY dinámico, todas las secuencias VT100/xterm.",
            "examples": [
                "Conectarse a un servidor y ejecutar comandos de forma interactiva.",
                "Gestionar múltiples servidores organizados por grupos (Producción, Dev…).",
                "Usar Vim, htop o cualquier herramienta TUI en el terminal integrado.",
                "Activar el reenvío de agente para saltar entre servidores sin copiar la clave privada (PC → A → B).",
            ],
            "cli": [
                "ssh user@192.168.1.10",
                "ssh -p 2222 user@192.168.1.10",
                "ssh -i ~/.ssh/id_ed25519 user@server.example.com",
                "ssh -A user@servidor-A  # reenvío de agente: salto a servidor-B posible desde A",
            ],
        },
        "de": {
            "desc": "Eingebettetes SSH-Terminal mit hierarchischem Adressbuch (Gruppen/Untergruppen). Schlüssel- und Passwortauthentifizierung, Agent-Forwarding (-A), 2000-Zeilen-Scrollback, dynamisches PTY, alle VT100/xterm-Sequenzen.",
            "examples": [
                "Mit einem Server verbinden und Befehle interaktiv ausführen.",
                "Mehrere Server in Gruppen verwalten (Produktion, Dev…).",
                "Vim, htop oder beliebige TUI-Tools im eingebetteten Terminal verwenden.",
                "Agent-Forwarding aktivieren, um zwischen Servern zu springen ohne den privaten Schlüssel zu kopieren (PC → A → B).",
            ],
            "cli": [
                "ssh user@192.168.1.10",
                "ssh -p 2222 user@192.168.1.10",
                "ssh -i ~/.ssh/id_ed25519 user@server.example.com",
                "ssh -A user@server-A  # Agent-Forwarding: Sprung zu Server-B von A aus möglich",
            ],
        },
        "it": {
            "desc": "Terminale SSH integrato con rubrica gerarchica (gruppi/sottogruppi). Autenticazione a chiave e password, agent forwarding (-A), scrollback 2000 righe, PTY dinamico, tutte le sequenze VT100/xterm.",
            "examples": [
                "Connettersi a un server ed eseguire comandi in modo interattivo.",
                "Gestire più server organizzati in gruppi (Produzione, Dev…).",
                "Usare Vim, htop o qualsiasi strumento TUI nel terminale integrato.",
                "Attivare l'agent forwarding per saltare tra server senza copiare la chiave privata (PC → A → B).",
            ],
            "cli": [
                "ssh user@192.168.1.10",
                "ssh -p 2222 user@192.168.1.10",
                "ssh -i ~/.ssh/id_ed25519 user@server.example.com",
                "ssh -A user@server-A  # agent forwarding: salto a server-B possibile da A",
            ],
        },
        "pt": {
            "desc": "Terminal SSH integrado com livro de endereços hierárquico (grupos/subgrupos). Autenticação por chave e palavra-passe, reencaminhamento de agente (-A), scrollback de 2000 linhas, PTY dinâmico, todas as sequências VT100/xterm.",
            "examples": [
                "Ligar a um servidor e executar comandos de forma interativa.",
                "Gerir múltiplos servidores organizados em grupos (Produção, Dev…).",
                "Usar Vim, htop ou qualquer ferramenta TUI no terminal integrado.",
                "Ativar o reencaminhamento de agente para saltar entre servidores sem copiar a chave privada (PC → A → B).",
            ],
            "cli": [
                "ssh user@192.168.1.10",
                "ssh -p 2222 user@192.168.1.10",
                "ssh -i ~/.ssh/id_ed25519 user@server.example.com",
                "ssh -A user@servidor-A  # reencaminhamento de agente: salto para servidor-B possível a partir de A",
            ],
        },
        "ja": {
            "desc": "階層型アドレス帳（グループ/サブグループ）を持つ組み込みSSHターミナル。キーとパスワード認証、エージェント転送（-A）、2000行スクロールバック、ダイナミックPTY、全VT100/xtermシーケンス対応。",
            "examples": [
                "サーバーに接続してコマンドをインタラクティブに実行する。",
                "グループ（本番、開発…）で複数のサーバーを管理する。",
                "組み込みターミナルでVim、htopなどのTUIツールを使用する。",
                "エージェント転送を有効にして秘密鍵をコピーせずにサーバー間を移動する（PC → A → B）。",
            ],
            "cli": [
                "ssh user@192.168.1.10",
                "ssh -p 2222 user@192.168.1.10",
                "ssh -i ~/.ssh/id_ed25519 user@server.example.com",
                "ssh -A user@server-A  # エージェント転送：AからサーバーBへのSSH接続が可能",
            ],
        },
        "zh": {
            "desc": "内置SSH终端，带有层级地址簿（组/子组）。支持密钥和密码认证、代理转发（-A）、2000行滚动缓冲区、动态PTY、所有VT100/xterm序列。",
            "examples": [
                "连接服务器并交互式执行命令。",
                "按组（生产、开发…）管理多个服务器。",
                "在内置终端中使用Vim、htop等TUI工具。",
                "启用代理转发，无需复制私钥即可在服务器间跳转（PC → A → B）。",
            ],
            "cli": [
                "ssh user@192.168.1.10",
                "ssh -p 2222 user@192.168.1.10",
                "ssh -i ~/.ssh/id_ed25519 user@server.example.com",
                "ssh -A user@服务器A  # 代理转发：可从A跳转至服务器B",
            ],
        },
    },
    "SSH Keys": {
        "fr": {
            "desc": "Gestionnaire de clés SSH : liste les paires de ~/.ssh/ (type, bits, commentaire, fingerprint SHA256). Génération Ed25519/RSA avec passphrase optionnelle, copie clé publique, déploiement via ssh-copy-id en terminal inline.",
            "examples": [
                "Générer une clé Ed25519 pour accéder à un serveur ou GitHub.",
                "Copier rapidement la clé publique pour la coller dans authorized_keys.",
                "Déployer une clé sur un nouveau serveur via ssh-copy-id en un clic.",
                "Inventorier et supprimer les anciennes paires inutilisées.",
            ],
            "cli": [
                "ssh-keygen -t ed25519 -C \"user@host\"",
                "ssh-keygen -t rsa -b 4096 -C \"user@host\"",
                "ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.1.10",
                "ssh-keygen -l -f ~/.ssh/id_ed25519.pub",
            ],
        },
        "en": {
            "desc": "SSH key manager: lists pairs from ~/.ssh/ (type, bits, comment, SHA256 fingerprint). Ed25519/RSA generation with optional passphrase, copy public key, deploy via ssh-copy-id in an inline terminal.",
            "examples": [
                "Generate an Ed25519 key to access a server or GitHub.",
                "Quickly copy the public key to paste into authorized_keys.",
                "Deploy a key to a new server via ssh-copy-id in one click.",
                "Inventory and delete old unused key pairs.",
            ],
            "cli": [
                "ssh-keygen -t ed25519 -C \"user@host\"",
                "ssh-keygen -t rsa -b 4096 -C \"user@host\"",
                "ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.1.10",
                "ssh-keygen -l -f ~/.ssh/id_ed25519.pub",
            ],
        },
        "es": {
            "desc": "Gestor de claves SSH: lista los pares de ~/.ssh/ (tipo, bits, comentario, fingerprint SHA256). Generación Ed25519/RSA con passphrase opcional, copiar clave pública, despliegue via ssh-copy-id en terminal inline.",
            "examples": [
                "Generar una clave Ed25519 para acceder a un servidor o GitHub.",
                "Copiar rápidamente la clave pública para pegarla en authorized_keys.",
                "Desplegar una clave en un nuevo servidor via ssh-copy-id con un clic.",
                "Inventariar y eliminar pares de claves antiguos en desuso.",
            ],
            "cli": [
                "ssh-keygen -t ed25519 -C \"user@host\"",
                "ssh-keygen -t rsa -b 4096 -C \"user@host\"",
                "ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.1.10",
                "ssh-keygen -l -f ~/.ssh/id_ed25519.pub",
            ],
        },
        "de": {
            "desc": "SSH-Schlüsselmanager: listet Paare aus ~/.ssh/ (Typ, Bits, Kommentar, SHA256-Fingerabdruck). Ed25519/RSA-Generierung mit optionaler Passphrase, öffentlichen Schlüssel kopieren, Bereitstellung über ssh-copy-id im Inline-Terminal.",
            "examples": [
                "Einen Ed25519-Schlüssel für den Zugriff auf einen Server oder GitHub generieren.",
                "Den öffentlichen Schlüssel schnell kopieren, um ihn in authorized_keys einzufügen.",
                "Schlüssel mit einem Klick über ssh-copy-id auf einem neuen Server bereitstellen.",
                "Alte ungenutzte Schlüsselpaare inventarisieren und löschen.",
            ],
            "cli": [
                "ssh-keygen -t ed25519 -C \"user@host\"",
                "ssh-keygen -t rsa -b 4096 -C \"user@host\"",
                "ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.1.10",
                "ssh-keygen -l -f ~/.ssh/id_ed25519.pub",
            ],
        },
        "it": {
            "desc": "Gestore di chiavi SSH: elenca le coppie da ~/.ssh/ (tipo, bit, commento, fingerprint SHA256). Generazione Ed25519/RSA con passphrase opzionale, copia chiave pubblica, distribuzione via ssh-copy-id in terminale inline.",
            "examples": [
                "Generare una chiave Ed25519 per accedere a un server o GitHub.",
                "Copiare rapidamente la chiave pubblica da incollare in authorized_keys.",
                "Distribuire una chiave su un nuovo server via ssh-copy-id in un clic.",
                "Inventariare ed eliminare le vecchie coppie inutilizzate.",
            ],
            "cli": [
                "ssh-keygen -t ed25519 -C \\\"user@host\\\"",
                "ssh-keygen -t rsa -b 4096 -C \\\"user@host\\\"",
                "ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.1.10",
                "ssh-keygen -l -f ~/.ssh/id_ed25519.pub",
            ],
        },
        "pt": {
            "desc": "Gestor de chaves SSH: lista os pares de ~/.ssh/ (tipo, bits, comentário, fingerprint SHA256). Geração Ed25519/RSA com frase-passe opcional, cópia de chave pública, distribuição via ssh-copy-id em terminal inline.",
            "examples": [
                "Gerar uma chave Ed25519 para aceder a um servidor ou GitHub.",
                "Copiar rapidamente a chave pública para colar em authorized_keys.",
                "Distribuir uma chave num novo servidor via ssh-copy-id com um clique.",
                "Inventariar e eliminar pares de chaves antigos não utilizados.",
            ],
            "cli": [
                "ssh-keygen -t ed25519 -C \\\"user@host\\\"",
                "ssh-keygen -t rsa -b 4096 -C \\\"user@host\\\"",
                "ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.1.10",
                "ssh-keygen -l -f ~/.ssh/id_ed25519.pub",
            ],
        },
        "ja": {
            "desc": "SSHキーマネージャー：~/.ssh/のキーペアを一覧表示（タイプ、ビット数、コメント、SHA256フィンガープリント）。Ed25519/RSA生成（オプションのパスフレーズ）、公開鍵のコピー、インラインターミナルでssh-copy-idによる配備。",
            "examples": [
                "サーバーまたはGitHubにアクセスするEd25519キーを生成する。",
                "authorized_keysに貼り付けるために公開鍵をすばやくコピーする。",
                "ワンクリックでssh-copy-idを使って新しいサーバーにキーを配備する。",
                "古い未使用キーペアをインベントリして削除する。",
            ],
            "cli": [
                "ssh-keygen -t ed25519 -C \"user@host\"",
                "ssh-keygen -t rsa -b 4096 -C \"user@host\"",
                "ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.1.10",
                "ssh-keygen -l -f ~/.ssh/id_ed25519.pub",
            ],
        },
        "zh": {
            "desc": "SSH密钥管理器：列出~/.ssh/中的密钥对（类型、位数、注释、SHA256指纹）。支持Ed25519/RSA生成（可选密码短语）、复制公钥、在内联终端通过ssh-copy-id部署。",
            "examples": [
                "生成Ed25519密钥以访问服务器或GitHub。",
                "快速复制公钥以粘贴到authorized_keys。",
                "一键通过ssh-copy-id将密钥部署到新服务器。",
                "清点并删除旧的未使用密钥对。",
            ],
            "cli": [
                "ssh-keygen -t ed25519 -C \"user@host\"",
                "ssh-keygen -t rsa -b 4096 -C \"user@host\"",
                "ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.1.10",
                "ssh-keygen -l -f ~/.ssh/id_ed25519.pub",
            ],
        },
    },
    "Remote Desktop": {
        "fr": {
            "desc": "Profils de connexion Bureau à distance (RDP) vers des machines Windows. Groupes/sous-groupes, lance xfreerdp. Mot de passe demandé à la connexion, jamais stocké.",
            "examples": [
                "Se connecter à un PC Windows depuis Linux en double-clic.",
                "Gérer plusieurs serveurs Windows par site ou par client.",
                "Configurer une connexion en plein écran 1920×1080.",
                "Accéder à un serveur en domaine Active Directory.",
            ],
            "cli": [
                "xfreerdp /v:192.168.1.100 /u:Administrateur /dynamic-resolution",
                "xfreerdp /v:192.168.1.100 /u:user /d:DOMAIN /f",
                "xfreerdp3 /v:192.168.1.100 /u:user /p:password /cert:ignore",
            ],
        },
        "en": {
            "desc": "Remote Desktop (RDP) connection profiles to Windows machines. Groups/subgroups, launches xfreerdp. Password prompted at connection time, never stored.",
            "examples": [
                "Connect to a Windows PC from Linux with a double-click.",
                "Manage multiple Windows servers by site or client.",
                "Set up a 1920×1080 fullscreen connection.",
                "Access a server on an Active Directory domain.",
            ],
            "cli": [
                "xfreerdp /v:192.168.1.100 /u:Administrator /dynamic-resolution",
                "xfreerdp /v:192.168.1.100 /u:user /d:DOMAIN /f",
                "xfreerdp3 /v:192.168.1.100 /u:user /p:password /cert:ignore",
            ],
        },
        "es": {
            "desc": "Perfiles de conexión de Escritorio Remoto (RDP) hacia máquinas Windows. Grupos/subgrupos, lanza xfreerdp. La contraseña se solicita en la conexión, nunca se almacena.",
            "examples": [
                "Conectarse a un PC Windows desde Linux con doble clic.",
                "Gestionar múltiples servidores Windows por sitio o cliente.",
                "Configurar una conexión en pantalla completa 1920×1080.",
                "Acceder a un servidor en un dominio Active Directory.",
            ],
            "cli": [
                "xfreerdp /v:192.168.1.100 /u:Administrador /dynamic-resolution",
                "xfreerdp /v:192.168.1.100 /u:user /d:DOMAIN /f",
                "xfreerdp3 /v:192.168.1.100 /u:user /p:password /cert:ignore",
            ],
        },
        "de": {
            "desc": "Remotedesktop-Verbindungsprofile (RDP) zu Windows-Rechnern. Gruppen/Untergruppen, startet xfreerdp. Passwort wird bei der Verbindung abgefragt, nie gespeichert.",
            "examples": [
                "Per Doppelklick von Linux aus mit einem Windows-PC verbinden.",
                "Mehrere Windows-Server nach Standort oder Kunde verwalten.",
                "Eine 1920×1080-Vollbildverbindung einrichten.",
                "Auf einen Server in einer Active Directory-Domäne zugreifen.",
            ],
            "cli": [
                "xfreerdp /v:192.168.1.100 /u:Administrator /dynamic-resolution",
                "xfreerdp /v:192.168.1.100 /u:user /d:DOMAIN /f",
                "xfreerdp3 /v:192.168.1.100 /u:user /p:password /cert:ignore",
            ],
        },
        "it": {
            "desc": "Profili di connessione Desktop Remoto (RDP) verso macchine Windows. Gruppi/sottogruppi, avvia xfreerdp. La password viene richiesta alla connessione, mai memorizzata.",
            "examples": [
                "Connettersi a un PC Windows da Linux con un doppio clic.",
                "Gestire più server Windows per sito o cliente.",
                "Configurare una connessione a schermo intero 1920×1080.",
                "Accedere a un server su un dominio Active Directory.",
            ],
            "cli": [
                "xfreerdp /v:192.168.1.100 /u:Administrator /dynamic-resolution",
                "xfreerdp /v:192.168.1.100 /u:user /d:DOMAIN /f",
                "xfreerdp3 /v:192.168.1.100 /u:user /p:password /cert:ignore",
            ],
        },
        "pt": {
            "desc": "Perfis de ligação de Ambiente de Trabalho Remoto (RDP) para máquinas Windows. Grupos/subgrupos, lança xfreerdp. Palavra-passe pedida na ligação, nunca armazenada.",
            "examples": [
                "Ligar a um PC Windows a partir do Linux com um duplo clique.",
                "Gerir múltiplos servidores Windows por site ou cliente.",
                "Configurar uma ligação em ecrã inteiro 1920×1080.",
                "Aceder a um servidor num domínio Active Directory.",
            ],
            "cli": [
                "xfreerdp /v:192.168.1.100 /u:Administrator /dynamic-resolution",
                "xfreerdp /v:192.168.1.100 /u:user /d:DOMAIN /f",
                "xfreerdp3 /v:192.168.1.100 /u:user /p:password /cert:ignore",
            ],
        },
        "ja": {
            "desc": "Windowsマシンへのリモートデスクトップ（RDP）接続プロファイル。グループ/サブグループ、xfreerdpを起動。パスワードは接続時に入力を求められ、保存されない。",
            "examples": [
                "ダブルクリックでLinuxからWindowsマシンに接続する。",
                "サイトまたはクライアント別に複数のWindowsサーバーを管理する。",
                "1920×1080フルスクリーン接続を設定する。",
                "Active Directoryドメイン上のサーバーにアクセスする。",
            ],
            "cli": [
                "xfreerdp /v:192.168.1.100 /u:Administrator /dynamic-resolution",
                "xfreerdp /v:192.168.1.100 /u:user /d:DOMAIN /f",
                "xfreerdp3 /v:192.168.1.100 /u:user /p:password /cert:ignore",
            ],
        },
        "zh": {
            "desc": "连接Windows机器的远程桌面（RDP）配置文件。支持组/子组，启动xfreerdp。密码在连接时提示输入，从不保存。",
            "examples": [
                "双击从Linux连接到Windows机器。",
                "按站点或客户管理多台Windows服务器。",
                "设置1920×1080全屏连接。",
                "访问Active Directory域上的服务器。",
            ],
            "cli": [
                "xfreerdp /v:192.168.1.100 /u:Administrator /dynamic-resolution",
                "xfreerdp /v:192.168.1.100 /u:user /d:DOMAIN /f",
                "xfreerdp3 /v:192.168.1.100 /u:user /p:password /cert:ignore",
            ],
        },
    },
    "VNC": {
        "fr": {
            "desc": "Profils de connexion VNC. Lance vncviewer (TigerVNC) vers Linux, macOS (ARD) ou Windows. Auth DH(30) macOS gérée nativement. Mot de passe jamais stocké.",
            "examples": [
                "Note : Linux n'a pas de serveur VNC par défaut — installer x11vnc, tigervnc-server ou wayvnc (Wayland).",
                "Accéder au bureau graphique d'un serveur Linux distant.",
                "Se connecter à un Mac via Apple Remote Desktop (ARD).",
                "Gérer plusieurs machines VNC en groupes.",
            ],
            "cli": [
                "vncviewer 192.168.1.100::5900",
                "vncviewer -FullScreen 192.168.1.100::5901",
                "vncviewer 192.168.1.100:1",
            ],
        },
        "en": {
            "desc": "VNC connection profiles. Launches vncviewer (TigerVNC) to Linux, macOS (ARD) or Windows. macOS DH(30) auth handled natively. Password never stored.",
            "examples": [
                "Note: Linux has no VNC server by default — install x11vnc, tigervnc-server or wayvnc (Wayland).",
                "Access the graphical desktop of a remote Linux server.",
                "Connect to a Mac via Apple Remote Desktop (ARD).",
                "Manage multiple VNC machines in groups.",
            ],
            "cli": [
                "vncviewer 192.168.1.100::5900",
                "vncviewer -FullScreen 192.168.1.100::5901",
                "vncviewer 192.168.1.100:1",
            ],
        },
        "es": {
            "desc": "Perfiles de conexión VNC. Lanza vncviewer (TigerVNC) hacia Linux, macOS (ARD) o Windows. Auth DH(30) de macOS gestionada nativamente. Contraseña nunca almacenada.",
            "examples": [
                "Nota: Linux no tiene servidor VNC por defecto — instalar x11vnc, tigervnc-server o wayvnc (Wayland).",
                "Acceder al escritorio gráfico de un servidor Linux remoto.",
                "Conectarse a un Mac via Apple Remote Desktop (ARD).",
                "Gestionar múltiples máquinas VNC en grupos.",
            ],
            "cli": [
                "vncviewer 192.168.1.100::5900",
                "vncviewer -FullScreen 192.168.1.100::5901",
                "vncviewer 192.168.1.100:1",
            ],
        },
        "de": {
            "desc": "VNC-Verbindungsprofile. Startet vncviewer (TigerVNC) zu Linux, macOS (ARD) oder Windows. macOS-DH(30)-Auth nativ unterstützt. Passwort wird nie gespeichert.",
            "examples": [
                "Hinweis: Linux hat keinen VNC-Server standardmäßig — x11vnc, tigervnc-server oder wayvnc (Wayland) installieren.",
                "Auf den grafischen Desktop eines entfernten Linux-Servers zugreifen.",
                "Über Apple Remote Desktop (ARD) mit einem Mac verbinden.",
                "Mehrere VNC-Maschinen in Gruppen verwalten.",
            ],
            "cli": [
                "vncviewer 192.168.1.100::5900",
                "vncviewer -FullScreen 192.168.1.100::5901",
                "vncviewer 192.168.1.100:1",
            ],
        },
        "it": {
            "desc": "Profili di connessione VNC. Avvia vncviewer (TigerVNC) verso Linux, macOS (ARD) o Windows. Auth DH(30) macOS gestita nativamente. Password mai memorizzata.",
            "examples": [
                "Nota: Linux non ha un server VNC predefinito — installare x11vnc, tigervnc-server o wayvnc (Wayland).",
                "Accedere al desktop grafico di un server Linux remoto.",
                "Connettersi a un Mac via Apple Remote Desktop (ARD).",
                "Gestire più macchine VNC in gruppi.",
            ],
            "cli": [
                "vncviewer 192.168.1.100::5900",
                "vncviewer -FullScreen 192.168.1.100::5901",
                "vncviewer 192.168.1.100:1",
            ],
        },
        "pt": {
            "desc": "Perfis de ligação VNC. Lança vncviewer (TigerVNC) para Linux, macOS (ARD) ou Windows. Auth DH(30) do macOS gerida nativamente. Palavra-passe nunca armazenada.",
            "examples": [
                "Nota: o Linux não tem servidor VNC por defeito — instalar x11vnc, tigervnc-server ou wayvnc (Wayland).",
                "Aceder ao ambiente de trabalho gráfico de um servidor Linux remoto.",
                "Ligar a um Mac via Apple Remote Desktop (ARD).",
                "Gerir múltiplas máquinas VNC em grupos.",
            ],
            "cli": [
                "vncviewer 192.168.1.100::5900",
                "vncviewer -FullScreen 192.168.1.100::5901",
                "vncviewer 192.168.1.100:1",
            ],
        },
        "ja": {
            "desc": "VNC接続プロファイル。Linux、macOS（ARD）、Windowsへvncviewer（TigerVNC）を起動。macOSのDH(30)認証をネイティブサポート。パスワードは保存されない。",
            "examples": [
                "注：LinuxにはデフォルトのVNCサーバーがない。x11vnc、tigervnc-server、またはwayvnc（Wayland）をインストールすること。",
                "リモートLinuxサーバーのグラフィカルデスクトップにアクセスする。",
                "Apple Remote Desktop（ARD）経由でMacに接続する。",
                "複数のVNCマシンをグループで管理する。",
            ],
            "cli": [
                "vncviewer 192.168.1.100::5900",
                "vncviewer -FullScreen 192.168.1.100::5901",
                "vncviewer 192.168.1.100:1",
            ],
        },
        "zh": {
            "desc": "VNC连接配置文件。启动vncviewer（TigerVNC）连接到Linux、macOS（ARD）或Windows。原生支持macOS DH(30)认证。密码从不保存。",
            "examples": [
                "注意：Linux默认没有VNC服务器——请安装x11vnc、tigervnc-server或wayvnc（Wayland）。",
                "访问远程Linux服务器的图形桌面。",
                "通过Apple Remote Desktop（ARD）连接Mac。",
                "在组中管理多台VNC机器。",
            ],
            "cli": [
                "vncviewer 192.168.1.100::5900",
                "vncviewer -FullScreen 192.168.1.100::5901",
                "vncviewer 192.168.1.100:1",
            ],
        },
    },
    "Traceroute": {
        "fr": {
            "desc": "Chemin réseau vers une destination avec géolocalisation en temps réel sur une carte monde interactive (Natural Earth). Supporte traceroute et tracepath. Carte zoomable/pannable.",
            "examples": [
                "Visualiser géographiquement le chemin vers un serveur étranger.",
                "Identifier à quel hop un paquet est perdu ou ralenti.",
                "Comparer les routes vers deux CDN différents.",
                "Détecter si le trafic passe par un pays inattendu.",
            ],
            "cli": [
                "traceroute -n google.com",
                "tracepath -b google.com",
                "mtr -n --report google.com",
                "traceroute -I -n 8.8.8.8",
            ],
        },
        "en": {
            "desc": "Network path to a destination with real-time geolocation on an interactive world map (Natural Earth). Supports traceroute and tracepath. Zoomable/pannable map.",
            "examples": [
                "Visually see the geographic path to a foreign server.",
                "Identify at which hop a packet is lost or slowed.",
                "Compare routes to two different CDNs.",
                "Detect if traffic passes through an unexpected country.",
            ],
            "cli": [
                "traceroute -n google.com",
                "tracepath -b google.com",
                "mtr -n --report google.com",
                "traceroute -I -n 8.8.8.8",
            ],
        },
        "es": {
            "desc": "Camino de red hacia un destino con geolocalización en tiempo real en un mapa mundial interactivo (Natural Earth). Soporta traceroute y tracepath. Mapa con zoom y panorámica.",
            "examples": [
                "Visualizar geográficamente el camino hacia un servidor extranjero.",
                "Identificar en qué salto se pierde o ralentiza un paquete.",
                "Comparar las rutas hacia dos CDN diferentes.",
                "Detectar si el tráfico pasa por un país inesperado.",
            ],
            "cli": [
                "traceroute -n google.com",
                "tracepath -b google.com",
                "mtr -n --report google.com",
                "traceroute -I -n 8.8.8.8",
            ],
        },
        "de": {
            "desc": "Netzwerkpfad zu einem Ziel mit Echtzeit-Geolokalisierung auf einer interaktiven Weltkarte (Natural Earth). Unterstützt traceroute und tracepath. Zoom- und schwenkbare Karte.",
            "examples": [
                "Geografischen Pfad zu einem ausländischen Server visualisieren.",
                "Identifizieren, bei welchem Hop ein Paket verloren geht oder verlangsamt wird.",
                "Routen zu zwei verschiedenen CDNs vergleichen.",
                "Erkennen, ob Traffic durch ein unerwartetes Land geleitet wird.",
            ],
            "cli": [
                "traceroute -n google.com",
                "tracepath -b google.com",
                "mtr -n --report google.com",
                "traceroute -I -n 8.8.8.8",
            ],
        },
        "it": {
            "desc": "Percorso di rete verso una destinazione con geolocalizzazione in tempo reale su una mappa mondiale interattiva (Natural Earth). Supporta traceroute e tracepath. Mappa con zoom e panoramica.",
            "examples": [
                "Visualizzare geograficamente il percorso verso un server straniero.",
                "Identificare in quale hop un pacchetto viene perso o rallentato.",
                "Confrontare i percorsi verso due CDN diversi.",
                "Rilevare se il traffico passa per un paese inaspettato.",
            ],
            "cli": [
                "traceroute -n google.com",
                "tracepath -b google.com",
                "mtr -n --report google.com",
                "traceroute -I -n 8.8.8.8",
            ],
        },
        "pt": {
            "desc": "Caminho de rede para um destino com geolocalização em tempo real num mapa mundial interativo (Natural Earth). Suporta traceroute e tracepath. Mapa com zoom e panorâmica.",
            "examples": [
                "Visualizar geograficamente o caminho para um servidor estrangeiro.",
                "Identificar em que hop um pacote é perdido ou atrasado.",
                "Comparar os caminhos para dois CDN diferentes.",
                "Detetar se o tráfego passa por um país inesperado.",
            ],
            "cli": [
                "traceroute -n google.com",
                "tracepath -b google.com",
                "mtr -n --report google.com",
                "traceroute -I -n 8.8.8.8",
            ],
        },
        "ja": {
            "desc": "インタラクティブな世界地図（Natural Earth）上でリアルタイムのジオロケーションを表示しながら宛先へのネットワーク経路を可視化。tracerouteとtracepathをサポート。ズーム/パン可能な地図。",
            "examples": [
                "外国のサーバーへの地理的な経路を視覚的に確認する。",
                "どのホップでパケットが失われたり遅延したりするかを特定する。",
                "2つの異なるCDNへの経路を比較する。",
                "トラフィックが予期しない国を経由していないか検出する。",
            ],
            "cli": [
                "traceroute -n google.com",
                "tracepath -b google.com",
                "mtr -n --report google.com",
                "traceroute -I -n 8.8.8.8",
            ],
        },
        "zh": {
            "desc": "在交互式世界地图（Natural Earth）上实时显示到目标的网络路径和地理位置。支持traceroute和tracepath。地图可缩放/平移。",
            "examples": [
                "直观查看到外国服务器的地理路径。",
                "识别数据包在哪个跳点丢失或变慢。",
                "比较到两个不同CDN的路由。",
                "检测流量是否经过意外的国家。",
            ],
            "cli": [
                "traceroute -n google.com",
                "tracepath -b google.com",
                "mtr -n --report google.com",
                "traceroute -I -n 8.8.8.8",
            ],
        },
    },
    "MTR": {
        "fr": {
            "desc": "Combine traceroute et ping : statistiques de perte et latence en continu pour chaque saut via mtr --report. Tableau Hop/Hôte/Perte%/Envoyés/Dernier/Moy/Min/Max/Gigue. Export CSV/TXT.",
            "examples": [
                "Identifier quel routeur est responsable d'une latence élevée.",
                "Mesurer la perte de paquets par saut vers un serveur de jeu.",
                "Comparer la qualité de deux liens internet vers le même hôte.",
                "Générer un rapport à partager avec le support d'un hébergeur.",
            ],
            "cli": [
                "mtr --report -c 10 google.com",
                "mtr -n --report google.com",
                "mtr --report-wide -c 100 8.8.8.8",
                "mtr --json google.com",
            ],
        },
        "en": {
            "desc": "Combines traceroute and ping: continuous loss and latency stats per hop via mtr --report. Hop/Host/Loss%/Sent/Last/Avg/Min/Max/Jitter table. CSV/TXT export.",
            "examples": [
                "Identify which router is responsible for high latency.",
                "Measure packet loss per hop to a game server.",
                "Compare quality of two internet links to the same host.",
                "Generate a report to share with a hosting provider's support.",
            ],
            "cli": [
                "mtr --report -c 10 google.com",
                "mtr -n --report google.com",
                "mtr --report-wide -c 100 8.8.8.8",
                "mtr --json google.com",
            ],
        },
        "es": {
            "desc": "Combina traceroute y ping: estadísticas continuas de pérdida y latencia por salto via mtr --report. Tabla Hop/Host/Pérdida%/Enviados/Último/Med/Mín/Máx/Jitter. Exportación CSV/TXT.",
            "examples": [
                "Identificar qué router es responsable de una latencia elevada.",
                "Medir la pérdida de paquetes por salto hacia un servidor de juegos.",
                "Comparar la calidad de dos enlaces de internet hacia el mismo host.",
                "Generar un informe para compartir con el soporte de un proveedor de alojamiento.",
            ],
            "cli": [
                "mtr --report -c 10 google.com",
                "mtr -n --report google.com",
                "mtr --report-wide -c 100 8.8.8.8",
                "mtr --json google.com",
            ],
        },
        "de": {
            "desc": "Kombiniert Traceroute und Ping: kontinuierliche Verlust- und Latenzstatistiken pro Hop über mtr --report. Hop/Host/Verlust%/Gesendet/Letzter/Avg/Min/Max/Jitter-Tabelle. CSV/TXT-Export.",
            "examples": [
                "Identifizieren, welcher Router für hohe Latenz verantwortlich ist.",
                "Paketverlust pro Hop zu einem Game-Server messen.",
                "Qualität zweier Internetverbindungen zum selben Host vergleichen.",
                "Bericht zum Teilen mit dem Support eines Hosting-Anbieters erstellen.",
            ],
            "cli": [
                "mtr --report -c 10 google.com",
                "mtr -n --report google.com",
                "mtr --report-wide -c 100 8.8.8.8",
                "mtr --json google.com",
            ],
        },
        "it": {
            "desc": "Combina traceroute e ping: statistiche continue di perdita e latenza per ogni hop via mtr --report. Tabella Hop/Host/Perdita%/Inviati/Ultimo/Media/Min/Max/Jitter. Export CSV/TXT.",
            "examples": [
                "Identificare quale router è responsabile di una latenza elevata.",
                "Misurare la perdita di pacchetti per hop verso un server di gioco.",
                "Confrontare la qualità di due collegamenti internet verso lo stesso host.",
                "Generare un rapporto da condividere con il supporto di un provider.",
            ],
            "cli": [
                "mtr --report -c 10 google.com",
                "mtr -n --report google.com",
                "mtr --report-wide -c 100 8.8.8.8",
                "mtr --json google.com",
            ],
        },
        "pt": {
            "desc": "Combina traceroute e ping: estatísticas contínuas de perda e latência por hop via mtr --report. Tabela Hop/Host/Perda%/Enviados/Último/Méd/Mín/Máx/Jitter. Exportação CSV/TXT.",
            "examples": [
                "Identificar qual router é responsável por uma latência elevada.",
                "Medir a perda de pacotes por hop para um servidor de jogos.",
                "Comparar a qualidade de duas ligações à internet para o mesmo host.",
                "Gerar um relatório para partilhar com o suporte de um fornecedor.",
            ],
            "cli": [
                "mtr --report -c 10 google.com",
                "mtr -n --report google.com",
                "mtr --report-wide -c 100 8.8.8.8",
                "mtr --json google.com",
            ],
        },
        "ja": {
            "desc": "tracerouteとpingを組み合わせ：mtr --report経由で各ホップの継続的な損失と遅延統計。ホップ/ホスト/損失%/送信数/最終/平均/最小/最大/ジッターのテーブル。CSV/TXTエクスポート。",
            "examples": [
                "どのルーターが高遅延の原因かを特定する。",
                "ゲームサーバーへの各ホップのパケット損失を測定する。",
                "同じホストへの2つのインターネット回線の品質を比較する。",
                "ホスティングプロバイダーのサポートと共有するレポートを生成する。",
            ],
            "cli": [
                "mtr --report -c 10 google.com",
                "mtr -n --report google.com",
                "mtr --report-wide -c 100 8.8.8.8",
                "mtr --json google.com",
            ],
        },
        "zh": {
            "desc": "结合traceroute和ping：通过mtr --report持续统计每个跳点的丢包和延迟。跳点/主机/丢包%/已发/最新/平均/最小/最大/抖动表格。支持CSV/TXT导出。",
            "examples": [
                "识别哪个路由器导致高延迟。",
                "测量到游戏服务器每个跳点的丢包率。",
                "比较到同一主机的两条互联网链路质量。",
                "生成报告与托管商技术支持共享。",
            ],
            "cli": [
                "mtr --report -c 10 google.com",
                "mtr -n --report google.com",
                "mtr --report-wide -c 100 8.8.8.8",
                "mtr --json google.com",
            ],
        },
    },
    "Firewall": {
        "fr": {
            "desc": "Lit et affiche les règles nftables et iptables/ip6tables sans root (fichiers de config), avec ruleset live via pkexec. Colonnes Table/Chain/Règle/Port/Action/Commentaire, filtrage live, coloration par action.",
            "examples": [
                "Vérifier les règles actives sans mémoriser la syntaxe nft/iptables.",
                "Filtrer les règles par port ou par chaîne (INPUT, OUTPUT).",
                "Comparer le fichier de config vs le ruleset live.",
                "Identifier une règle DROP qui bloque un service.",
            ],
            "cli": [
                "nft list ruleset",
                "iptables -L -n -v --line-numbers",
                "ip6tables -L -n -v",
                "nft list table inet filter",
            ],
        },
        "en": {
            "desc": "Reads and displays nftables and iptables/ip6tables rules without root (config files), with live ruleset via pkexec. Table/Chain/Rule/Port/Action/Comment columns, live filter, action color coding.",
            "examples": [
                "Review active rules without memorizing nft/iptables syntax.",
                "Filter rules by port or chain (INPUT, OUTPUT).",
                "Compare config file vs live ruleset.",
                "Identify a DROP rule blocking a service.",
            ],
            "cli": [
                "nft list ruleset",
                "iptables -L -n -v --line-numbers",
                "ip6tables -L -n -v",
                "nft list table inet filter",
            ],
        },
        "es": {
            "desc": "Lee y muestra las reglas nftables e iptables/ip6tables sin root (archivos de config), con ruleset live via pkexec. Columnas Tabla/Cadena/Regla/Puerto/Acción/Comentario, filtrado live, coloración por acción.",
            "examples": [
                "Revisar las reglas activas sin memorizar la sintaxis nft/iptables.",
                "Filtrar reglas por puerto o cadena (INPUT, OUTPUT).",
                "Comparar el archivo de configuración con el ruleset live.",
                "Identificar una regla DROP que bloquea un servicio.",
            ],
            "cli": [
                "nft list ruleset",
                "iptables -L -n -v --line-numbers",
                "ip6tables -L -n -v",
                "nft list table inet filter",
            ],
        },
        "de": {
            "desc": "Liest und zeigt nftables- und iptables/ip6tables-Regeln ohne Root (Konfigurationsdateien), mit Live-Ruleset über pkexec. Spalten Tabelle/Chain/Regel/Port/Aktion/Kommentar, Live-Filter, Aktionsfarbkodierung.",
            "examples": [
                "Aktive Regeln prüfen, ohne nft/iptables-Syntax auswendig zu kennen.",
                "Regeln nach Port oder Chain (INPUT, OUTPUT) filtern.",
                "Konfigurationsdatei mit Live-Ruleset vergleichen.",
                "Eine DROP-Regel identifizieren, die einen Dienst blockiert.",
            ],
            "cli": [
                "nft list ruleset",
                "iptables -L -n -v --line-numbers",
                "ip6tables -L -n -v",
                "nft list table inet filter",
            ],
        },
        "it": {
            "desc": "Legge e visualizza le regole nftables e iptables/ip6tables senza root (file di config), con ruleset live via pkexec. Colonne Tabella/Catena/Regola/Porta/Azione/Commento, filtro live, colorazione per azione.",
            "examples": [
                "Verificare le regole attive senza memorizzare la sintassi nft/iptables.",
                "Filtrare le regole per porta o catena (INPUT, OUTPUT).",
                "Confrontare il file di configurazione con il ruleset live.",
                "Identificare una regola DROP che blocca un servizio.",
            ],
            "cli": [
                "nft list ruleset",
                "iptables -L -n -v --line-numbers",
                "ip6tables -L -n -v",
                "nft list table inet filter",
            ],
        },
        "pt": {
            "desc": "Lê e apresenta as regras nftables e iptables/ip6tables sem root (ficheiros de config), com ruleset live via pkexec. Colunas Tabela/Cadeia/Regra/Porta/Ação/Comentário, filtro live, codificação de cor por ação.",
            "examples": [
                "Rever as regras ativas sem memorizar a sintaxe nft/iptables.",
                "Filtrar regras por porta ou cadeia (INPUT, OUTPUT).",
                "Comparar o ficheiro de configuração com o ruleset live.",
                "Identificar uma regra DROP que bloqueia um serviço.",
            ],
            "cli": [
                "nft list ruleset",
                "iptables -L -n -v --line-numbers",
                "ip6tables -L -n -v",
                "nft list table inet filter",
            ],
        },
        "ja": {
            "desc": "nftablesとiptables/ip6tablesのルールをルートなしで読み取り・表示（設定ファイル）、pkexec経由でライブルールセットも取得。テーブル/チェーン/ルール/ポート/アクション/コメント列、ライブフィルター、アクション別色分け。",
            "examples": [
                "nft/iptablesの構文を暗記せずにアクティブなルールを確認する。",
                "ポートまたはチェーン（INPUT、OUTPUT）でルールをフィルタリングする。",
                "設定ファイルとライブルールセットを比較する。",
                "サービスをブロックしているDROPルールを特定する。",
            ],
            "cli": [
                "nft list ruleset",
                "iptables -L -n -v --line-numbers",
                "ip6tables -L -n -v",
                "nft list table inet filter",
            ],
        },
        "zh": {
            "desc": "无需root即可读取并显示nftables和iptables/ip6tables规则（配置文件），通过pkexec获取实时规则集。表/链/规则/端口/动作/注释列，实时筛选，按动作着色。",
            "examples": [
                "无需记忆nft/iptables语法即可查看活动规则。",
                "按端口或链（INPUT、OUTPUT）筛选规则。",
                "对比配置文件与实时规则集。",
                "识别阻止服务的DROP规则。",
            ],
            "cli": [
                "nft list ruleset",
                "iptables -L -n -v --line-numbers",
                "ip6tables -L -n -v",
                "nft list table inet filter",
            ],
        },
    },
    "Speed Test": {
        "fr": {
            "desc": "Onglet Internet : débit descendant (25 Mo), montant (10 Mo) et ping via Cloudflare (speed.cloudflare.com) par curl. Onglet LAN : débit point-à-point via iperf3 (client uniquement) contre un serveur public par pays ou un serveur personnalisé sauvegardé. Résultats en temps réel, historique 5 tests (Internet), graphique de tendance.",
            "examples": [
                "Mesurer le débit réel sans navigateur.",
                "Comparer les débits Wi-Fi vs Ethernet.",
                "Surveiller l'évolution du débit dans le temps.",
                "Détecter une dégradation de connexion chez un client.",
                "Mesurer le débit LAN réel entre deux machines, ou comparer IPv4/IPv6, via iperf3.",
            ],
            "cli": [
                "curl -o /dev/null -s -w '%{speed_download}\\n' https://speed.cloudflare.com/__down?bytes=25000000",
                "curl -o /dev/null -s -w '%{speed_upload}\\n' -T /dev/zero https://speed.cloudflare.com/__up",
                "ping -c 10 1.1.1.1 | tail -1",
                "iperf3 -c <serveur> -p 5201 -J -t 10",
            ],
        },
        "en": {
            "desc": "Internet tab: download (25 MB), upload (10 MB) and ping via Cloudflare (speed.cloudflare.com) using curl. LAN tab: point-to-point throughput via iperf3 (client only) against a public server by country or a saved custom server. Real-time results, 5-test history (Internet), trend chart.",
            "examples": [
                "Measure actual throughput without a browser.",
                "Compare Wi-Fi vs Ethernet speeds.",
                "Monitor speed over time with the history chart.",
                "Detect connection degradation at a client site.",
                "Measure real LAN throughput between two machines, or compare IPv4/IPv6, via iperf3.",
            ],
            "cli": [
                "curl -o /dev/null -s -w '%{speed_download}\\n' https://speed.cloudflare.com/__down?bytes=25000000",
                "curl -o /dev/null -s -w '%{speed_upload}\\n' -T /dev/zero https://speed.cloudflare.com/__up",
                "ping -c 10 1.1.1.1 | tail -1",
                "iperf3 -c <server> -p 5201 -J -t 10",
            ],
        },
        "es": {
            "desc": "Pestaña Internet: descarga (25 MB), subida (10 MB) y ping via Cloudflare (speed.cloudflare.com) mediante curl. Pestaña LAN: rendimiento punto a punto mediante iperf3 (solo cliente) contra un servidor público por país o un servidor personalizado guardado. Resultados en tiempo real, historial de 5 pruebas (Internet), gráfico de tendencia.",
            "examples": [
                "Medir el rendimiento real sin abrir un navegador.",
                "Comparar las velocidades Wi-Fi vs Ethernet.",
                "Monitorear la evolución de la velocidad en el tiempo.",
                "Detectar una degradación de la conexión en un sitio cliente.",
                "Medir el rendimiento LAN real entre dos máquinas, o comparar IPv4/IPv6, con iperf3.",
            ],
            "cli": [
                "curl -o /dev/null -s -w '%{speed_download}\\n' https://speed.cloudflare.com/__down?bytes=25000000",
                "curl -o /dev/null -s -w '%{speed_upload}\\n' -T /dev/zero https://speed.cloudflare.com/__up",
                "ping -c 10 1.1.1.1 | tail -1",
                "iperf3 -c <servidor> -p 5201 -J -t 10",
            ],
        },
        "de": {
            "desc": "Internet-Tab: Download (25 MB), Upload (10 MB) und Ping über Cloudflare (speed.cloudflare.com) mit curl. LAN-Tab: Punkt-zu-Punkt-Durchsatz über iperf3 (nur Client) gegen einen öffentlichen Server nach Land oder einen gespeicherten benutzerdefinierten Server. Echtzeitergebnisse, 5-Test-Verlauf (Internet), Trenddiagramm.",
            "examples": [
                "Tatsächlichen Durchsatz ohne Browser messen.",
                "Wi-Fi- vs. Ethernet-Geschwindigkeiten vergleichen.",
                "Geschwindigkeitsentwicklung im Zeitverlauf überwachen.",
                "Verbindungsverschlechterung bei einem Kunden erkennen.",
                "Echten LAN-Durchsatz zwischen zwei Rechnern messen oder IPv4/IPv6 mit iperf3 vergleichen.",
            ],
            "cli": [
                "curl -o /dev/null -s -w '%{speed_download}\\n' https://speed.cloudflare.com/__down?bytes=25000000",
                "curl -o /dev/null -s -w '%{speed_upload}\\n' -T /dev/zero https://speed.cloudflare.com/__up",
                "ping -c 10 1.1.1.1 | tail -1",
                "iperf3 -c <Server> -p 5201 -J -t 10",
            ],
        },
        "it": {
            "desc": "Scheda Internet: download (25 MB), upload (10 MB) e ping via Cloudflare (speed.cloudflare.com) usando curl. Scheda LAN: throughput punto-punto tramite iperf3 (solo client) verso un server pubblico per paese o un server personalizzato salvato. Risultati in tempo reale, storico 5 test (Internet), grafico di tendenza.",
            "examples": [
                "Misurare il throughput reale senza browser.",
                "Confrontare le velocità Wi-Fi vs Ethernet.",
                "Monitorare la velocità nel tempo con il grafico storico.",
                "Rilevare una degradazione della connessione presso un cliente.",
                "Misurare il throughput LAN reale tra due macchine, o confrontare IPv4/IPv6, con iperf3.",
            ],
            "cli": [
                "curl -o /dev/null -s -w '%{speed_download}\\\\n' https://speed.cloudflare.com/__down?bytes=25000000",
                "curl -o /dev/null -s -w '%{speed_upload}\\\\n' -T /dev/zero https://speed.cloudflare.com/__up",
                "ping -c 10 1.1.1.1 | tail -1",
                "iperf3 -c <server> -p 5201 -J -t 10",
            ],
        },
        "pt": {
            "desc": "Aba Internet: download (25 MB), upload (10 MB) e ping via Cloudflare (speed.cloudflare.com) usando curl. Aba LAN: throughput ponto a ponto via iperf3 (somente cliente) contra um servidor público por país ou um servidor personalizado salvo. Resultados em tempo real, histórico de 5 testes (Internet), gráfico de tendência.",
            "examples": [
                "Medir o throughput real sem browser.",
                "Comparar velocidades Wi-Fi vs Ethernet.",
                "Monitorizar a velocidade ao longo do tempo com o gráfico histórico.",
                "Detetar degradação da ligação num site cliente.",
                "Medir o throughput LAN real entre duas máquinas, ou comparar IPv4/IPv6, via iperf3.",
            ],
            "cli": [
                "curl -o /dev/null -s -w '%{speed_download}\\\\n' https://speed.cloudflare.com/__down?bytes=25000000",
                "curl -o /dev/null -s -w '%{speed_upload}\\\\n' -T /dev/zero https://speed.cloudflare.com/__up",
                "ping -c 10 1.1.1.1 | tail -1",
                "iperf3 -c <servidor> -p 5201 -J -t 10",
            ],
        },
        "ja": {
            "desc": "インターネットタブ：curl経由でCloudflare（speed.cloudflare.com）によるダウンロード（25 MB）、アップロード（10 MB）、pingを測定。LANタブ：iperf3（クライアントのみ）による国別の公開サーバーまたは保存済みカスタムサーバーへの1対1スループット測定。リアルタイム結果、5テスト履歴（インターネット）、トレンドチャート。",
            "examples": [
                "ブラウザを使わずに実際のスループットを測定する。",
                "Wi-FiとEthernetの速度を比較する。",
                "履歴チャートで時間経過による速度を監視する。",
                "クライアントサイトでの接続劣化を検出する。",
                "iperf3で2台のマシン間の実際のLANスループットを測定、またはIPv4/IPv6を比較する。",
            ],
            "cli": [
                "curl -o /dev/null -s -w '%{speed_download}\\n' https://speed.cloudflare.com/__down?bytes=25000000",
                "curl -o /dev/null -s -w '%{speed_upload}\\n' -T /dev/zero https://speed.cloudflare.com/__up",
                "ping -c 10 1.1.1.1 | tail -1",
                "iperf3 -c <サーバー> -p 5201 -J -t 10",
            ],
        },
        "zh": {
            "desc": "互联网标签页：通过curl使用Cloudflare（speed.cloudflare.com）测量下载（25 MB）、上传（10 MB）速度和ping值。局域网标签页：通过iperf3（仅客户端）针对按国家分类的公共服务器或已保存的自定义服务器测量点对点吞吐量。实时显示结果，保留5次历史记录（互联网），显示趋势图。",
            "examples": [
                "无需浏览器即可测量实际吞吐量。",
                "比较Wi-Fi和Ethernet的速度。",
                "通过历史图表监控速度变化趋势。",
                "检测客户端连接质量下降。",
                "使用iperf3测量两台设备之间的真实局域网吞吐量，或比较IPv4/IPv6。",
            ],
            "cli": [
                "curl -o /dev/null -s -w '%{speed_download}\\n' https://speed.cloudflare.com/__down?bytes=25000000",
                "curl -o /dev/null -s -w '%{speed_upload}\\n' -T /dev/zero https://speed.cloudflare.com/__up",
                "ping -c 10 1.1.1.1 | tail -1",
                "iperf3 -c <服务器> -p 5201 -J -t 10",
            ],
        },
    },
    "Bandwidth": {
        "fr": {
            "desc": "Surveille le débit réseau en temps réel sur une interface. Graphique glissant 60 secondes, courbes download/upload, vitesses actuelles, totaux session et pics.",
            "examples": [
                "Visualiser l'utilisation de la bande passante pendant un backup.",
                "Identifier quelle interface consomme le plus (Ethernet, Wi-Fi, VPN).",
                "Détecter un trafic réseau anormal en fond de tâche.",
                "Mesurer la vitesse d'un transfert vers un NAS.",
            ],
            "cli": [
                "cat /proc/net/dev",
                "watch -n 1 'cat /proc/net/dev | grep eth0'",
                "nethogs eth0",
                "iftop -i eth0",
            ],
        },
        "en": {
            "desc": "Monitors network throughput in real time on a selected interface. 60-second sliding chart, download/upload curves, current speeds, session totals and peaks.",
            "examples": [
                "Visualize bandwidth usage during a backup.",
                "Identify which interface consumes the most (Ethernet, Wi-Fi, VPN).",
                "Detect unexpected background network traffic.",
                "Measure effective transfer speed to a NAS.",
            ],
            "cli": [
                "cat /proc/net/dev",
                "watch -n 1 'cat /proc/net/dev | grep eth0'",
                "nethogs eth0",
                "iftop -i eth0",
            ],
        },
        "es": {
            "desc": "Monitorea el rendimiento de red en tiempo real en una interfaz seleccionada. Gráfico deslizante de 60 segundos, curvas download/upload, velocidades actuales, totales de sesión y picos.",
            "examples": [
                "Visualizar el uso de ancho de banda durante un backup.",
                "Identificar qué interfaz consume más (Ethernet, Wi-Fi, VPN).",
                "Detectar tráfico de red inesperado en segundo plano.",
                "Medir la velocidad de transferencia efectiva hacia un NAS.",
            ],
            "cli": [
                "cat /proc/net/dev",
                "watch -n 1 'cat /proc/net/dev | grep eth0'",
                "nethogs eth0",
                "iftop -i eth0",
            ],
        },
        "de": {
            "desc": "Überwacht den Netzwerkdurchsatz in Echtzeit auf einer ausgewählten Schnittstelle. 60-Sekunden-Gleitdiagramm, Download/Upload-Kurven, aktuelle Geschwindigkeiten, Sitzungssummen und Spitzenwerte.",
            "examples": [
                "Bandbreitennutzung während eines Backups visualisieren.",
                "Identifizieren, welche Schnittstelle am meisten verbraucht (Ethernet, Wi-Fi, VPN).",
                "Unerwarteten Hintergrund-Netzwerktraffic erkennen.",
                "Effektive Übertragungsgeschwindigkeit zu einem NAS messen.",
            ],
            "cli": [
                "cat /proc/net/dev",
                "watch -n 1 'cat /proc/net/dev | grep eth0'",
                "nethogs eth0",
                "iftop -i eth0",
            ],
        },
        "it": {
            "desc": "Monitora il throughput di rete in tempo reale su un'interfaccia selezionata. Grafico scorrevole 60 secondi, curve download/upload, velocità attuali, totali sessione e picchi.",
            "examples": [
                "Visualizzare l'utilizzo della banda durante un backup.",
                "Identificare quale interfaccia consuma di più (Ethernet, Wi-Fi, VPN).",
                "Rilevare traffico di rete inatteso in background.",
                "Misurare la velocità di trasferimento effettiva verso un NAS.",
            ],
            "cli": [
                "cat /proc/net/dev",
                "watch -n 1 'cat /proc/net/dev | grep eth0'",
                "nethogs eth0",
                "iftop -i eth0",
            ],
        },
        "pt": {
            "desc": "Monitoriza o débito de rede em tempo real numa interface selecionada. Gráfico deslizante de 60 segundos, curvas download/upload, velocidades atuais, totais de sessão e picos.",
            "examples": [
                "Visualizar o uso de largura de banda durante um backup.",
                "Identificar qual interface consome mais (Ethernet, Wi-Fi, VPN).",
                "Detetar tráfego de rede inesperado em segundo plano.",
                "Medir a velocidade de transferência efetiva para um NAS.",
            ],
            "cli": [
                "cat /proc/net/dev",
                "watch -n 1 'cat /proc/net/dev | grep eth0'",
                "nethogs eth0",
                "iftop -i eth0",
            ],
        },
        "ja": {
            "desc": "選択したインターフェース上のネットワークスループットをリアルタイムで監視。60秒スライドチャート、ダウンロード/アップロード曲線、現在の速度、セッション合計とピーク値。",
            "examples": [
                "バックアップ中の帯域幅使用量を可視化する。",
                "どのインターフェースが最も消費しているか特定する（Ethernet、Wi-Fi、VPN）。",
                "バックグラウンドの予期しないネットワークトラフィックを検出する。",
                "NASへの実際の転送速度を測定する。",
            ],
            "cli": [
                "cat /proc/net/dev",
                "watch -n 1 'cat /proc/net/dev | grep eth0'",
                "nethogs eth0",
                "iftop -i eth0",
            ],
        },
        "zh": {
            "desc": "实时监控所选接口的网络吞吐量。60秒滑动图表，下载/上传曲线，当前速度、会话总量和峰值。",
            "examples": [
                "在备份期间可视化带宽使用情况。",
                "识别哪个接口消耗最多（Ethernet、Wi-Fi、VPN）。",
                "检测意外的后台网络流量。",
                "测量到NAS的实际传输速度。",
            ],
            "cli": [
                "cat /proc/net/dev",
                "watch -n 1 'cat /proc/net/dev | grep eth0'",
                "nethogs eth0",
                "iftop -i eth0",
            ],
        },
    },
    "Wake on LAN": {
        "fr": {
            "desc": "Envoie un Magic Packet UDP natif Python pour démarrer un équipement à distance. Carnet d'hôtes persistant (JSON) avec nom, adresse MAC et broadcast.",
            "examples": [
                "Démarrer un PC de bureau avant d'y accéder via SSH ou RDP.",
                "Réveiller un NAS en veille avant un accès aux fichiers.",
                "Tester si le WoL est bien activé dans le BIOS.",
                "Gérer plusieurs équipements (PC, serveurs, NAS) dans un carnet centralisé.",
            ],
            "cli": [
                "wakeonlan AA:BB:CC:DD:EE:FF",
                "wakeonlan -i 192.168.1.255 AA:BB:CC:DD:EE:FF",
                "etherwake -i eth0 AA:BB:CC:DD:EE:FF",
            ],
        },
        "en": {
            "desc": "Sends a native Python UDP Magic Packet to remotely start a device. Persistent host book (JSON) with name, MAC and broadcast address.",
            "examples": [
                "Start a desktop PC before accessing it via SSH or RDP.",
                "Wake up a sleeping NAS before accessing files.",
                "Test if WoL is enabled in the BIOS.",
                "Manage multiple WoL devices (PCs, servers, NAS) in a centralized book.",
            ],
            "cli": [
                "wakeonlan AA:BB:CC:DD:EE:FF",
                "wakeonlan -i 192.168.1.255 AA:BB:CC:DD:EE:FF",
                "etherwake -i eth0 AA:BB:CC:DD:EE:FF",
            ],
        },
        "es": {
            "desc": "Envía un Magic Packet UDP Python nativo para arrancar un dispositivo remotamente. Libreta de hosts persistente (JSON) con nombre, dirección MAC y broadcast.",
            "examples": [
                "Arrancar un PC de escritorio antes de acceder por SSH o RDP.",
                "Despertar un NAS en suspensión antes de acceder a los archivos.",
                "Probar si WoL está habilitado en el BIOS.",
                "Gestionar múltiples dispositivos (PCs, servidores, NAS) en una libreta centralizada.",
            ],
            "cli": [
                "wakeonlan AA:BB:CC:DD:EE:FF",
                "wakeonlan -i 192.168.1.255 AA:BB:CC:DD:EE:FF",
                "etherwake -i eth0 AA:BB:CC:DD:EE:FF",
            ],
        },
        "de": {
            "desc": "Sendet ein natives Python-UDP-Magic-Paket, um ein Gerät fernzustarten. Persistentes Host-Buch (JSON) mit Name, MAC-Adresse und Broadcast.",
            "examples": [
                "Desktop-PC starten, bevor über SSH oder RDP darauf zugegriffen wird.",
                "Schlafenden NAS aufwecken, bevor auf Dateien zugegriffen wird.",
                "Prüfen, ob WoL im BIOS aktiviert ist.",
                "Mehrere WoL-Geräte (PCs, Server, NAS) in einem zentralen Buch verwalten.",
            ],
            "cli": [
                "wakeonlan AA:BB:CC:DD:EE:FF",
                "wakeonlan -i 192.168.1.255 AA:BB:CC:DD:EE:FF",
                "etherwake -i eth0 AA:BB:CC:DD:EE:FF",
            ],
        },
        "it": {
            "desc": "Invia un Magic Packet UDP Python nativo per avviare un dispositivo da remoto. Rubrica host persistente (JSON) con nome, indirizzo MAC e broadcast.",
            "examples": [
                "Avviare un PC desktop prima di accedervi via SSH o RDP.",
                "Svegliare un NAS in sospensione prima di accedere ai file.",
                "Testare se il WoL è abilitato nel BIOS.",
                "Gestire più dispositivi WoL (PC, server, NAS) in una rubrica centralizzata.",
            ],
            "cli": [
                "wakeonlan AA:BB:CC:DD:EE:FF",
                "wakeonlan -i 192.168.1.255 AA:BB:CC:DD:EE:FF",
                "etherwake -i eth0 AA:BB:CC:DD:EE:FF",
            ],
        },
        "pt": {
            "desc": "Envia um Magic Packet UDP Python nativo para iniciar remotamente um dispositivo. Livro de hosts persistente (JSON) com nome, endereço MAC e broadcast.",
            "examples": [
                "Iniciar um PC de secretária antes de aceder via SSH ou RDP.",
                "Acordar um NAS em suspensão antes de aceder aos ficheiros.",
                "Testar se o WoL está ativado no BIOS.",
                "Gerir múltiplos dispositivos WoL (PCs, servidores, NAS) num livro centralizado.",
            ],
            "cli": [
                "wakeonlan AA:BB:CC:DD:EE:FF",
                "wakeonlan -i 192.168.1.255 AA:BB:CC:DD:EE:FF",
                "etherwake -i eth0 AA:BB:CC:DD:EE:FF",
            ],
        },
        "ja": {
            "desc": "デバイスをリモートで起動するためのネイティブPython UDP Magic Packetを送信。名前、MACアドレス、ブロードキャストアドレスを持つ永続的なホストブック（JSON）。",
            "examples": [
                "SSHまたはRDPでアクセスする前にデスクトップPCを起動する。",
                "ファイルにアクセスする前にスリープ中のNASを起こす。",
                "BIOSでWoLが有効になっているかテストする。",
                "複数のWoLデバイス（PC、サーバー、NAS）を一元管理する。",
            ],
            "cli": [
                "wakeonlan AA:BB:CC:DD:EE:FF",
                "wakeonlan -i 192.168.1.255 AA:BB:CC:DD:EE:FF",
                "etherwake -i eth0 AA:BB:CC:DD:EE:FF",
            ],
        },
        "zh": {
            "desc": "发送原生Python UDP魔术包以远程启动设备。持久化主机簿（JSON），包含名称、MAC地址和广播地址。",
            "examples": [
                "通过SSH或RDP访问前先启动台式机。",
                "在访问文件前唤醒处于休眠的NAS。",
                "测试BIOS中是否启用了WoL。",
                "在集中主机簿中管理多个WoL设备（PC、服务器、NAS）。",
            ],
            "cli": [
                "wakeonlan AA:BB:CC:DD:EE:FF",
                "wakeonlan -i 192.168.1.255 AA:BB:CC:DD:EE:FF",
                "etherwake -i eth0 AA:BB:CC:DD:EE:FF",
            ],
        },
    },
    "Topology": {
        "fr": {
            "desc": "Carte visuelle interactive des équipements LAN découverts via nmap -sn. Nœuds déplaçables, icônes distinguant routeur/moniteur/tour PC. IP, MAC, hostname et fabricant au clic ou au survol.",
            "examples": [
                "Vue graphique rapide de tous les équipements actifs sur le LAN.",
                "Identifier visuellement la gateway et les équipements autour d'elle.",
                "Détecter un équipement inconnu par son icône ou son fabricant.",
                "Documenter l'infrastructure réseau avec une carte visuelle.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn -oX - 192.168.1.0/24 | grep -E 'addr|hostname'",
                "arp-scan --localnet",
            ],
        },
        "en": {
            "desc": "Interactive visual map of LAN devices discovered via nmap -sn. Draggable nodes, icons distinguishing router/monitor/tower PC. IP, MAC, hostname and manufacturer on click or hover.",
            "examples": [
                "Quick visual overview of all active devices on the LAN.",
                "Visually identify the gateway and devices around it.",
                "Detect an unknown device by its icon or manufacturer.",
                "Document network infrastructure with a visual map.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn -oX - 192.168.1.0/24 | grep -E 'addr|hostname'",
                "arp-scan --localnet",
            ],
        },
        "es": {
            "desc": "Mapa visual interactivo de los dispositivos LAN descubiertos via nmap -sn. Nodos arrastrables, iconos que distinguen router/monitor/torre PC. IP, MAC, hostname y fabricante al hacer clic o pasar el cursor.",
            "examples": [
                "Vista gráfica rápida de todos los dispositivos activos en el LAN.",
                "Identificar visualmente la gateway y los dispositivos a su alrededor.",
                "Detectar un dispositivo desconocido por su icono o fabricante.",
                "Documentar la infraestructura de red con un mapa visual.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn -oX - 192.168.1.0/24 | grep -E 'addr|hostname'",
                "arp-scan --localnet",
            ],
        },
        "de": {
            "desc": "Interaktive visuelle Karte der über nmap -sn entdeckten LAN-Geräte. Verschiebbare Knoten, Icons unterscheiden Router/Monitor/Tower-PC. IP, MAC, Hostname und Hersteller bei Klick oder Hover.",
            "examples": [
                "Schnelle visuelle Übersicht aller aktiven LAN-Geräte.",
                "Gateway und umgebende Geräte visuell identifizieren.",
                "Unbekanntes Gerät über Icon oder Hersteller erkennen.",
                "Netzwerkinfrastruktur mit einer visuellen Karte dokumentieren.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn -oX - 192.168.1.0/24 | grep -E 'addr|hostname'",
                "arp-scan --localnet",
            ],
        },
        "it": {
            "desc": "Mappa visiva interattiva dei dispositivi LAN scoperti via nmap -sn. Nodi trascinabili, icone che distinguono router/monitor/torre PC. IP, MAC, hostname e produttore al clic o al passaggio del mouse.",
            "examples": [
                "Panoramica visiva rapida di tutti i dispositivi attivi sulla LAN.",
                "Identificare visivamente il gateway e i dispositivi attorno ad esso.",
                "Rilevare un dispositivo sconosciuto tramite icona o produttore.",
                "Documentare l'infrastruttura di rete con una mappa visiva.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn -oX - 192.168.1.0/24 | grep -E 'addr|hostname'",
                "arp-scan --localnet",
            ],
        },
        "pt": {
            "desc": "Mapa visual interativo dos dispositivos LAN descobertos via nmap -sn. Nós arrastáveis, ícones distinguindo router/monitor/torre PC. IP, MAC, hostname e fabricante ao clicar ou ao passar o rato.",
            "examples": [
                "Vista geral visual rápida de todos os dispositivos ativos na LAN.",
                "Identificar visualmente o gateway e os dispositivos à sua volta.",
                "Detetar um dispositivo desconhecido pelo ícone ou fabricante.",
                "Documentar a infraestrutura de rede com um mapa visual.",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn -oX - 192.168.1.0/24 | grep -E 'addr|hostname'",
                "arp-scan --localnet",
            ],
        },
        "ja": {
            "desc": "nmap -sn経由で発見されたLANデバイスのインタラクティブなビジュアルマップ。ドラッグ可能なノード、ルーター/モニター/タワーPCを区別するアイコン。クリックまたはホバーでIP、MAC、ホスト名、メーカーを表示。",
            "examples": [
                "LAN上のすべてのアクティブデバイスを素早くビジュアル概観する。",
                "ゲートウェイとその周辺デバイスを視覚的に特定する。",
                "アイコンまたはメーカーで未知のデバイスを検出する。",
                "ビジュアルマップでネットワークインフラをドキュメント化する。",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn -oX - 192.168.1.0/24 | grep -E 'addr|hostname'",
                "arp-scan --localnet",
            ],
        },
        "zh": {
            "desc": "通过nmap -sn发现的LAN设备的交互式可视化地图。可拖拽节点，图标区分路由器/显示器/台式机。点击或悬停可查看IP、MAC、主机名和厂商信息。",
            "examples": [
                "快速直观地查看LAN上所有活动设备。",
                "直观识别网关及其周围的设备。",
                "通过图标或厂商检测未知设备。",
                "用可视化地图记录网络基础设施。",
            ],
            "cli": [
                "nmap -sn 192.168.1.0/24",
                "nmap -sn -oX - 192.168.1.0/24 | grep -E 'addr|hostname'",
                "arp-scan --localnet",
            ],
        },
    },
    "Asset Inventory": {
        "fr": {
            "desc": "Génère un inventaire instantané des équipements actifs sur le réseau. Sans credentials : détection OS via Nmap. Avec SSH : OS exact, CPU, RAM, disques, uptime. WinRM : même données sur Windows. SNMP : description et uptime des équipements réseau. Aucune donnée n'est conservée après fermeture de l'application.",
            "examples": [
                "Scanner 192.168.1.0/24 sans credentials pour lister tous les hôtes actifs.",
                "Fournir un utilisateur SSH pour obtenir CPU/RAM/disque des serveurs Linux.",
                "Utiliser WinRM pour inventorier les machines Windows du domaine.",
                "Interroger les switches et NAS via SNMP v2c avec la communauté 'public'.",
            ],
            "cli": [
                "nmap -O 192.168.1.0/24",
                "ssh user@host 'uname -a && free -h && df -h /'",
                "snmpget -v2c -c public 192.168.1.1 1.3.6.1.2.1.1.1.0",
            ],
        },
        "en": {
            "desc": "Generates an instant inventory of active network devices. Without credentials: OS detection via Nmap. With SSH: exact OS, CPU, RAM, disks, uptime. WinRM: same data on Windows. SNMP: description and uptime for network equipment. No data is retained after the app closes.",
            "examples": [
                "Scan 192.168.1.0/24 without credentials to list all active hosts.",
                "Provide SSH user to get CPU/RAM/disk from Linux servers.",
                "Use WinRM to inventory Windows domain machines.",
                "Query switches and NAS via SNMP v2c with 'public' community.",
            ],
            "cli": [
                "nmap -O 192.168.1.0/24",
                "ssh user@host 'uname -a && free -h && df -h /'",
                "snmpget -v2c -c public 192.168.1.1 1.3.6.1.2.1.1.1.0",
            ],
        },
    },
}


def get_help(label: str) -> dict | None:
    """Return {desc, examples, cli} for the given module label in the current language."""
    entry = _CONTENT.get(label)
    if not entry:
        return None
    lang = _get_settings().language
    # Fall back to English, then French, if the current language has no content
    return entry.get(lang) or entry.get("en") or entry.get("fr")
