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
    },
    "SSH": {
        "fr": {
            "desc": "Terminal SSH embarqué avec carnet d'adresses hiérarchique (groupes/sous-groupes). Authentification par clé et mot de passe, scrollback 2000 lignes, PTY dynamique, toutes séquences VT100/xterm.",
            "examples": [
                "Se connecter à un serveur et exécuter des commandes interactivement.",
                "Gérer plusieurs serveurs organisés par groupes (Production, Dev…).",
                "Utiliser Vim, htop ou tout outil TUI dans le terminal embarqué.",
                "Conserver un historique de connexions pour retrouver rapidement un serveur.",
            ],
            "cli": [
                "ssh user@192.168.1.10",
                "ssh -p 2222 user@192.168.1.10",
                "ssh -i ~/.ssh/id_ed25519 user@server.example.com",
                "ssh -L 8080:localhost:80 user@192.168.1.10",
            ],
        },
        "en": {
            "desc": "Embedded SSH terminal with hierarchical address book (groups/subgroups). Key and password auth, 2000-line scrollback, dynamic PTY, all VT100/xterm sequences.",
            "examples": [
                "Connect to a server and run commands interactively.",
                "Manage multiple servers organized in groups (Production, Dev…).",
                "Use Vim, htop or any TUI tool in the embedded terminal.",
                "Keep a connection history to quickly find a server.",
            ],
            "cli": [
                "ssh user@192.168.1.10",
                "ssh -p 2222 user@192.168.1.10",
                "ssh -i ~/.ssh/id_ed25519 user@server.example.com",
                "ssh -L 8080:localhost:80 user@192.168.1.10",
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
    },
    "VNC": {
        "fr": {
            "desc": "Profils de connexion VNC. Lance vncviewer (TigerVNC) vers Linux, macOS (ARD) ou Windows. Auth DH(30) macOS gérée nativement. Mot de passe jamais stocké.",
            "examples": [
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
    },
    "Speed Test": {
        "fr": {
            "desc": "Mesure le débit descendant (25 Mo), montant (10 Mo) et le ping via Cloudflare (speed.cloudflare.com) par curl. Résultats en temps réel, historique 5 tests, graphique de tendance.",
            "examples": [
                "Mesurer le débit réel sans navigateur.",
                "Comparer les débits Wi-Fi vs Ethernet.",
                "Surveiller l'évolution du débit dans le temps.",
                "Détecter une dégradation de connexion chez un client.",
            ],
            "cli": [
                "curl -o /dev/null -s -w '%{speed_download}\\n' https://speed.cloudflare.com/__down?bytes=25000000",
                "curl -o /dev/null -s -w '%{speed_upload}\\n' -T /dev/zero https://speed.cloudflare.com/__up",
                "ping -c 10 1.1.1.1 | tail -1",
            ],
        },
        "en": {
            "desc": "Measures download (25 MB), upload (10 MB) and ping via Cloudflare (speed.cloudflare.com) using curl. Real-time results, 5-test history, trend chart.",
            "examples": [
                "Measure actual throughput without a browser.",
                "Compare Wi-Fi vs Ethernet speeds.",
                "Monitor speed over time with the history chart.",
                "Detect connection degradation at a client site.",
            ],
            "cli": [
                "curl -o /dev/null -s -w '%{speed_download}\\n' https://speed.cloudflare.com/__down?bytes=25000000",
                "curl -o /dev/null -s -w '%{speed_upload}\\n' -T /dev/zero https://speed.cloudflare.com/__up",
                "ping -c 10 1.1.1.1 | tail -1",
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
