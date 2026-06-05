from __future__ import annotations
from nmlinux.core.settings import get as _get_settings


_CONTENT: dict[str, dict[str, dict]] = {
    "Dashboard": {
        "fr": {
            "desc": "Le Dashboard affiche en un coup d'œil toutes les informations réseau essentielles de la machine locale : nom d'hôte, adresse IPv4/IPv6 locale, passerelle, serveurs DNS actifs, adresse IP publique et géolocalisation approximative via ip-api.com.",
            "examples": [
                "Vérifier rapidement l'IP locale et la passerelle avant de diagnostiquer un problème de connectivité.",
                "Confirmer que les bons serveurs DNS sont utilisés après un changement de configuration réseau.",
                "Connaître son IP publique sans ouvrir un navigateur.",
                "Identifier sa position géographique apparente (utile avec un VPN).",
            ],
        },
        "en": {
            "desc": "The Dashboard shows at a glance all essential network info for the local machine: hostname, IPv4/IPv6, gateway, active DNS servers, public IP and approximate geolocation via ip-api.com.",
            "examples": [
                "Quickly check local IP and gateway before diagnosing a connectivity issue.",
                "Confirm the correct DNS servers are in use after a network config change.",
                "Know your public IP without opening a browser.",
                "See your apparent geographic location (useful with a VPN).",
            ],
        },
    },
    "Connections": {
        "fr": {
            "desc": "Affiche et gère toutes les connexions réseau NetworkManager (Ethernet, Wi-Fi, VPN, WireGuard). Permet de connecter, déconnecter, éditer ou supprimer une connexion, avec un filtre par type et une barre CLI pédagogique montrant les commandes nmcli équivalentes.",
            "examples": [
                "Activer ou désactiver rapidement une connexion VPN sans passer par les paramètres système.",
                "Voir les détails IP/DNS/SSID d'une connexion Wi-Fi active.",
                "Supprimer un ancien profil Wi-Fi qui n'est plus nécessaire.",
                "Apprendre les commandes nmcli en observant la barre CLI lors de chaque action.",
            ],
        },
        "en": {
            "desc": "Displays and manages all NetworkManager connections (Ethernet, Wi-Fi, VPN, WireGuard). Connect, disconnect, edit or delete connections with type filtering and a CLI bar showing the equivalent nmcli commands.",
            "examples": [
                "Quickly activate or deactivate a VPN without going through system settings.",
                "See IP/DNS/SSID details of an active Wi-Fi connection.",
                "Delete an old Wi-Fi profile that is no longer needed.",
                "Learn nmcli commands by watching the CLI bar during each action.",
            ],
        },
    },
    "Interfaces": {
        "fr": {
            "desc": "Liste toutes les interfaces réseau actives (Ethernet, Wi-Fi, loopback, bridges…) avec leur état, adresse MAC, adresses IPv4 et IPv6. Un clic sur une interface affiche le détail complet dans un panneau latéral.",
            "examples": [
                "Vérifier quelle interface est utilisée et son état up/down.",
                "Retrouver l'adresse MAC d'une interface pour configurer un pare-feu ou un DHCP statique.",
                "Contrôler qu'une interface a bien reçu une adresse IP après connexion.",
                "Identifier les interfaces virtuelles créées par Docker, libvirt ou WireGuard.",
            ],
        },
        "en": {
            "desc": "Lists all active network interfaces (Ethernet, Wi-Fi, loopback, bridges…) with their state, MAC address, IPv4 and IPv6 addresses. Click an interface to see full details in a side panel.",
            "examples": [
                "Check which interface is in use and its up/down state.",
                "Find an interface's MAC address to configure a firewall or static DHCP.",
                "Verify that an interface received an IP address after connecting.",
                "Identify virtual interfaces created by Docker, libvirt or WireGuard.",
            ],
        },
    },
    "Wi-Fi": {
        "fr": {
            "desc": "Scanne les réseaux sans fil disponibles et affiche le SSID, BSSID, canal, fréquence, niveau de signal (barres ▂▄▆█) et type de sécurité. Le réseau connecté apparaît en premier.",
            "examples": [
                "Détecter les réseaux Wi-Fi dans les environs et comparer les niveaux de signal.",
                "Vérifier si un réseau est en 2,4 GHz ou 5 GHz avant de se connecter.",
                "Identifier les réseaux non sécurisés (Open) à proximité.",
                "Choisir le meilleur canal pour son propre point d'accès en voyant les canaux utilisés.",
            ],
        },
        "en": {
            "desc": "Scans available wireless networks and shows SSID, BSSID, channel, frequency, signal strength (bars ▂▄▆█) and security type. The connected network appears first.",
            "examples": [
                "Detect nearby Wi-Fi networks and compare signal levels.",
                "Check if a network is on 2.4 GHz or 5 GHz before connecting.",
                "Identify unsecured (Open) networks nearby.",
                "Choose the best channel for your own access point by seeing which channels are in use.",
            ],
        },
    },
    "Subnet": {
        "fr": {
            "desc": "Calculateur de sous-réseau CIDR : à partir d'une adresse IP et d'un masque (ex. 192.168.1.0/24), calcule l'adresse réseau, le masque de sous-réseau, le wildcard, le broadcast, la plage d'hôtes valides et le nombre total d'hôtes. Fonctionne en IPv4 et IPv6.",
            "examples": [
                "Calculer la plage d'adresses disponibles avant d'attribuer des IPs fixes dans un réseau.",
                "Vérifier si deux adresses IP appartiennent au même sous-réseau.",
                "Déterminer le broadcast d'un réseau pour configurer des règles de pare-feu.",
                "Planifier le découpage d'un réseau en plusieurs sous-réseaux (subnetting).",
            ],
        },
        "en": {
            "desc": "CIDR subnet calculator: from an IP address and mask (e.g. 192.168.1.0/24), computes network address, subnet mask, wildcard, broadcast, valid host range and total host count. Supports IPv4 and IPv6.",
            "examples": [
                "Calculate the available address range before assigning static IPs.",
                "Check if two IP addresses belong to the same subnet.",
                "Determine the broadcast address to configure firewall rules.",
                "Plan subnetting by splitting a network into multiple subnets.",
            ],
        },
    },
    "DNS": {
        "fr": {
            "desc": "Interroge n'importe quel serveur DNS via dig. Supporte tous les types d'enregistrements (A, AAAA, MX, TXT, NS, CNAME, PTR, SOA, ANY). Permet de spécifier un serveur DNS alternatif et d'effectuer des lookups inversés (PTR) automatiquement depuis une adresse IP.",
            "examples": [
                "Vérifier si un enregistrement A pointe bien vers la bonne adresse IP.",
                "Tester la propagation DNS d'un domaine nouvellement configuré en interrogeant plusieurs serveurs.",
                "Chercher les enregistrements MX d'un domaine pour diagnostiquer des problèmes d'email.",
                "Faire un reverse lookup (PTR) d'une adresse IP pour identifier un serveur.",
            ],
        },
        "en": {
            "desc": "Queries any DNS server using dig. Supports all record types (A, AAAA, MX, TXT, NS, CNAME, PTR, SOA, ANY). Lets you specify an alternative DNS server and automatically performs reverse (PTR) lookups from an IP address.",
            "examples": [
                "Verify that an A record points to the correct IP address.",
                "Test DNS propagation for a newly configured domain by querying multiple servers.",
                "Look up MX records for a domain to diagnose email delivery issues.",
                "Do a reverse PTR lookup on an IP address to identify a server.",
            ],
        },
    },
    "Ping": {
        "fr": {
            "desc": "Moniteur de ping multi-hôtes en continu : envoie des paquets ICMP à intervalles configurables (1-30s) vers plusieurs destinations simultanées et affiche les statistiques RTT (min/moy/max) et le taux de perte en temps réel.",
            "examples": [
                "Surveiller simultanément la passerelle, le DNS public (8.8.8.8) et un serveur distant pour isoler un problème réseau.",
                "Mesurer la stabilité d'une connexion internet sur une longue période.",
                "Vérifier qu'un équipement réseau répond bien après un redémarrage.",
                "Comparer la latence vers plusieurs CDN ou serveurs de jeux.",
            ],
        },
        "en": {
            "desc": "Continuous multi-host ping monitor: sends ICMP packets at configurable intervals (1-30s) to multiple simultaneous destinations and shows RTT stats (min/avg/max) and packet loss in real time.",
            "examples": [
                "Monitor gateway, public DNS (8.8.8.8) and a remote server simultaneously to isolate a network issue.",
                "Measure internet connection stability over a long period.",
                "Verify that a network device responds after a reboot.",
                "Compare latency to multiple CDNs or game servers.",
            ],
        },
    },
    "IP Scanner": {
        "fr": {
            "desc": "Découvre les équipements actifs sur un réseau local par balayage ARP/ping sur une plage CIDR ou d'adresses. Pour chaque hôte trouvé, affiche l'IP, le hostname (via DNS/mDNS/NetBIOS), l'adresse MAC et le fabricant (base OUI 39 000 entrées).",
            "examples": [
                "Inventorier tous les équipements connectés au réseau (192.168.1.0/24).",
                "Retrouver l'adresse IP d'un équipement dont on ne connaît que le nom.",
                "Détecter un équipement inconnu sur le réseau en identifiant son fabricant via l'OUI.",
                "Exporter la liste au format CSV pour un audit d'inventaire réseau.",
            ],
        },
        "en": {
            "desc": "Discovers active devices on a local network by ARP/ping scanning a CIDR range. For each found host, shows IP, hostname (via DNS/mDNS/NetBIOS), MAC address and manufacturer (39,000-entry OUI database).",
            "examples": [
                "Inventory all devices connected to the network (192.168.1.0/24).",
                "Find the IP address of a device you only know the name of.",
                "Detect an unknown device on the network by identifying its manufacturer via OUI.",
                "Export the list as CSV for a network inventory audit.",
            ],
        },
    },
    "Port Scanner": {
        "fr": {
            "desc": "Scanne les ports TCP d'un hôte par connexion directe (sans root requis). Prend en charge les plages de ports, des presets courants (Web, Mail, SSH…) et affiche le service identifié pour chaque port ouvert. Jusqu'à 200 threads simultanés.",
            "examples": [
                "Vérifier que les bons ports sont ouverts sur un serveur web (80, 443).",
                "Détecter les services actifs sur un serveur avant d'y accéder.",
                "Confirmer qu'un port SSH (22) est fermé sur une machine exposée à Internet.",
                "Rechercher des ports inhabituels ouverts sur un équipement suspect.",
            ],
        },
        "en": {
            "desc": "Scans TCP ports on a host using direct connection (no root required). Supports port ranges, common presets (Web, Mail, SSH…) and shows the identified service for each open port. Up to 200 simultaneous threads.",
            "examples": [
                "Verify that the right ports are open on a web server (80, 443).",
                "Detect active services on a server before accessing it.",
                "Confirm that SSH port (22) is closed on an internet-facing machine.",
                "Look for unusual open ports on a suspicious device.",
            ],
        },
    },
    "Nmap": {
        "fr": {
            "desc": "Scan réseau avancé via nmap avec 7 modes : découverte rapide, scan TCP, SYN (root), détection de services et versions, détection OS, scan complet, et scripts NSE de sécurité. Les résultats XML sont parsés et affichés dans un tableau structuré.",
            "examples": [
                "Identifier le système d'exploitation d'un équipement réseau inconnu (mode OS detection).",
                "Découvrir les versions exactes des services pour évaluer les vulnérabilités.",
                "Effectuer un scan furtif SYN sur un périmètre réseau (nécessite root).",
                "Lancer des scripts NSE pour détecter des vulnérabilités connues (ex: SMB, SSL).",
            ],
        },
        "en": {
            "desc": "Advanced network scanning via nmap with 7 modes: fast discovery, TCP scan, SYN scan (root), service/version detection, OS detection, full scan, and NSE security scripts. XML results are parsed and displayed in a structured table.",
            "examples": [
                "Identify the OS of an unknown network device (OS detection mode).",
                "Discover exact service versions to assess vulnerabilities.",
                "Run a stealthy SYN scan on a network perimeter (requires root).",
                "Launch NSE scripts to detect known vulnerabilities (e.g. SMB, SSL).",
            ],
        },
    },
    "Whois": {
        "fr": {
            "desc": "Effectue une requête WHOIS sur un nom de domaine ou une adresse IP et affiche le résultat brut dans un format monospace lisible. Utile pour obtenir les informations d'enregistrement, les contacts administratifs et les plages IP d'un opérateur.",
            "examples": [
                "Vérifier la date d'expiration d'un nom de domaine.",
                "Identifier le registrar et le propriétaire apparent d'un domaine suspect.",
                "Retrouver l'opérateur réseau (AS) derrière une adresse IP.",
                "Obtenir les contacts abus pour signaler un comportement malveillant.",
            ],
        },
        "en": {
            "desc": "Performs a WHOIS query on a domain name or IP address and displays the raw result in readable monospace format. Useful for registration info, administrative contacts and IP ranges of an operator.",
            "examples": [
                "Check the expiry date of a domain name.",
                "Identify the registrar and apparent owner of a suspicious domain.",
                "Find the network operator (AS) behind an IP address.",
                "Get abuse contacts to report malicious behavior.",
            ],
        },
    },
    "TLS Inspector": {
        "fr": {
            "desc": "Inspecte le certificat TLS/SSL d'un serveur : sujet CN, SANs, émetteur, dates de validité (code couleur vert/orange/rouge), numéro de série, protocole TLS, suite de chiffrement et chaîne de certification complète via openssl s_client. Fonctionne sur les certificats valides, expirés et auto-signés.",
            "examples": [
                "Vérifier l'expiration d'un certificat SSL avant qu'il ne cause une interruption de service.",
                "Contrôler que les bons SANs (Subject Alternative Names) sont présents sur un certificat multi-domaine.",
                "Diagnostiquer des erreurs TLS en inspectant le protocole et le cipher utilisés.",
                "Vérifier la chaîne de certification complète d'un serveur interne avec un CA privé.",
            ],
        },
        "en": {
            "desc": "Inspects a server's TLS/SSL certificate: subject CN, SANs, issuer, validity dates (green/orange/red color coding), serial number, TLS protocol, cipher suite and full certificate chain via openssl s_client. Works on valid, expired and self-signed certificates.",
            "examples": [
                "Check SSL certificate expiry before it causes a service outage.",
                "Verify the correct SANs are present on a multi-domain certificate.",
                "Diagnose TLS errors by inspecting the protocol and cipher in use.",
                "Verify the full certificate chain of an internal server with a private CA.",
            ],
        },
    },
    "SMB / NFS": {
        "fr": {
            "desc": "Liste les partages réseau SMB/Samba et les exports NFS d'un serveur ou NAS. L'onglet SMB utilise smbclient -L (avec identifiants optionnels) et affiche nom/type/commentaire de chaque partage. L'onglet NFS utilise showmount -e et liste les chemins exportés et les clients autorisés.",
            "examples": [
                "Voir tous les partages disponibles sur un NAS avant de les monter.",
                "Vérifier quels répertoires sont exportés en NFS sur un serveur Linux.",
                "Accéder à un partage Samba avec des identifiants de domaine.",
                "Diagnostiquer pourquoi un partage réseau n'est pas accessible.",
            ],
        },
        "en": {
            "desc": "Lists SMB/Samba shares and NFS exports from a server or NAS. The SMB tab uses smbclient -L (with optional credentials) and shows each share's name/type/comment. The NFS tab uses showmount -e and lists exported paths and allowed clients.",
            "examples": [
                "See all available shares on a NAS before mounting them.",
                "Check which directories are exported via NFS on a Linux server.",
                "Access a Samba share with domain credentials.",
                "Diagnose why a network share is not accessible.",
            ],
        },
    },
    "Hosts File": {
        "fr": {
            "desc": "Affiche et modifie le fichier /etc/hosts dans une interface tabulaire. Permet d'ajouter, modifier, supprimer ou activer/désactiver des entrées sans éditer le fichier manuellement. La sauvegarde utilise pkexec (authentification polkit) pour les droits root nécessaires.",
            "examples": [
                "Ajouter un alias local (ex: monserveur.local → 192.168.1.10) pour faciliter la connexion.",
                "Bloquer un domaine indésirable en le redirigeant vers 0.0.0.0.",
                "Désactiver temporairement une entrée sans la supprimer (toggle).",
                "Tester un changement de DNS avant la propagation en forçant localement l'IP.",
            ],
        },
        "en": {
            "desc": "Displays and edits /etc/hosts in a table interface. Add, edit, delete or enable/disable entries without manually editing the file. Saving uses pkexec (polkit auth) for the required root privileges.",
            "examples": [
                "Add a local alias (e.g. myserver.local → 192.168.1.10) for easy access.",
                "Block an unwanted domain by redirecting it to 0.0.0.0.",
                "Temporarily disable an entry without deleting it (toggle).",
                "Test a DNS change before propagation by forcing the IP locally.",
            ],
        },
    },
    "SNMP": {
        "fr": {
            "desc": "Interroge des équipements réseau compatibles SNMP (routeurs, switches, NAS, imprimantes…) via snmpwalk ou snmpget. Supporte les versions v1/v2c avec 10 presets d'OID courants (nom système, uptime, interfaces, CPU, mémoire…).",
            "examples": [
                "Lire l'uptime d'un switch ou d'un routeur via SNMP.",
                "Récupérer la liste des interfaces réseau d'un équipement avec leurs états.",
                "Interroger la charge CPU et mémoire d'un serveur compatible SNMP.",
                "Tester la communauté SNMP d'un équipement avant de l'intégrer dans un outil de supervision.",
            ],
        },
        "en": {
            "desc": "Queries SNMP-compatible network devices (routers, switches, NAS, printers…) via snmpwalk or snmpget. Supports v1/v2c with 10 common OID presets (system name, uptime, interfaces, CPU, memory…).",
            "examples": [
                "Read the uptime of a switch or router via SNMP.",
                "Retrieve the network interface list of a device with their states.",
                "Query CPU and memory load on an SNMP-compatible server.",
                "Test the SNMP community of a device before adding it to a monitoring tool.",
            ],
        },
    },
    "SNTP / NTP": {
        "fr": {
            "desc": "Teste la synchronisation avec un ou plusieurs serveurs de temps NTP via un client UDP pur Python (RFC 4330). Affiche l'offset, le délai de roundtrip, le stratum et la source de référence. Jusqu'à 5 requêtes moyennées pour une mesure plus précise.",
            "examples": [
                "Vérifier que le serveur NTP local est accessible et répond correctement.",
                "Mesurer la dérive d'horloge d'un serveur par rapport à un NTP de référence.",
                "Tester plusieurs serveurs du pool ntp.org et comparer leurs délais.",
                "Diagnostiquer des problèmes de certificats TLS liés à une horloge système incorrecte.",
            ],
        },
        "en": {
            "desc": "Tests synchronization with NTP time servers via a pure Python UDP client (RFC 4330). Shows offset, roundtrip delay, stratum and reference source. Up to 5 averaged requests for more precise measurement.",
            "examples": [
                "Verify that the local NTP server is reachable and responding correctly.",
                "Measure clock drift of a server against a reference NTP.",
                "Test multiple ntp.org pool servers and compare their delays.",
                "Diagnose TLS certificate issues caused by an incorrect system clock.",
            ],
        },
    },
    "SSH": {
        "fr": {
            "desc": "Terminal SSH embarqué avec carnet d'adresses hiérarchique (groupes et sous-groupes). Supporte l'authentification par clé et par mot de passe, le scrollback de 2000 lignes, le redimensionnement dynamique du PTY et toutes les séquences VT100/xterm (ZSH, Vim, htop…).",
            "examples": [
                "Se connecter à un serveur distant et exécuter des commandes interactivement.",
                "Gérer plusieurs serveurs organisés par groupes (Production, Staging, Dev).",
                "Utiliser Vim, htop ou tout outil TUI directement dans le terminal embarqué.",
                "Conserver un historique de connexions pour retrouver rapidement un serveur.",
            ],
        },
        "en": {
            "desc": "Embedded SSH terminal with hierarchical address book (groups and subgroups). Supports key and password authentication, 2000-line scrollback, dynamic PTY resizing and all VT100/xterm sequences (ZSH, Vim, htop…).",
            "examples": [
                "Connect to a remote server and run commands interactively.",
                "Manage multiple servers organized by groups (Production, Staging, Dev).",
                "Use Vim, htop or any TUI tool directly in the embedded terminal.",
                "Keep a connection history to quickly find a server.",
            ],
        },
    },
    "SSH Keys": {
        "fr": {
            "desc": "Gestionnaire de clés SSH : liste toutes les paires de clés dans ~/.ssh/ avec le type (Ed25519/RSA), la taille en bits, le commentaire et l'empreinte SHA256. Permet de générer de nouvelles clés avec passphrase optionnelle, de copier la clé publique dans le presse-papiers et de déployer la clé sur un serveur via ssh-copy-id dans un terminal inline.",
            "examples": [
                "Générer une clé Ed25519 pour accéder à un serveur ou un dépôt GitHub.",
                "Copier rapidement sa clé publique pour la coller dans authorized_keys ou GitHub.",
                "Déployer une clé sur un nouveau serveur via ssh-copy-id en un clic.",
                "Inventorier toutes les clés SSH existantes et supprimer les anciennes paires inutilisées.",
            ],
        },
        "en": {
            "desc": "SSH key manager: lists all key pairs in ~/.ssh/ with type (Ed25519/RSA), bit size, comment and SHA256 fingerprint. Generate new keys with optional passphrase, copy the public key to clipboard and deploy the key to a server via ssh-copy-id in an inline terminal.",
            "examples": [
                "Generate an Ed25519 key to access a server or GitHub repository.",
                "Quickly copy your public key to paste into authorized_keys or GitHub.",
                "Deploy a key to a new server via ssh-copy-id in one click.",
                "Inventory all existing SSH keys and delete old unused pairs.",
            ],
        },
    },
    "Remote Desktop": {
        "fr": {
            "desc": "Gestionnaire de profils de connexion Bureau à distance (RDP) vers des machines Windows. Organise les connexions en groupes et sous-groupes, lance xfreerdp avec les paramètres configurés (résolution, plein écran, domaine). Le mot de passe est demandé à la connexion, jamais stocké.",
            "examples": [
                "Se connecter à un PC Windows du bureau depuis Linux en un double-clic.",
                "Gérer plusieurs serveurs Windows organisés par site ou par client.",
                "Configurer une connexion en plein écran 1920×1080 pour un poste fixe.",
                "Accéder à un serveur Windows en domaine Active Directory.",
            ],
        },
        "en": {
            "desc": "Manages Remote Desktop (RDP) connection profiles to Windows machines. Organizes connections in groups and subgroups, launches xfreerdp with configured parameters (resolution, fullscreen, domain). Password is prompted at connection time, never stored.",
            "examples": [
                "Connect to a Windows desktop from Linux with a double-click.",
                "Manage multiple Windows servers organized by site or client.",
                "Set up a 1920×1080 fullscreen connection for a workstation.",
                "Access a Windows server on an Active Directory domain.",
            ],
        },
    },
    "VNC": {
        "fr": {
            "desc": "Gestionnaire de profils de connexion VNC. Lance vncviewer (TigerVNC) vers des machines Linux, macOS (ARD) ou Windows avec prise en charge de l'authentification DH(30) macOS. Le mot de passe est demandé à la connexion, jamais stocké.",
            "examples": [
                "Accéder au bureau graphique d'un serveur Linux distant.",
                "Se connecter à un Mac via Apple Remote Desktop (ARD).",
                "Gérer plusieurs machines VNC organisées par groupes.",
                "Détecter automatiquement si vncviewer est installé, avec instructions par distro.",
            ],
        },
        "en": {
            "desc": "Manages VNC connection profiles. Launches vncviewer (TigerVNC) to Linux, macOS (ARD) or Windows machines with macOS DH(30) auth support. Password is prompted at connection time, never stored.",
            "examples": [
                "Access the graphical desktop of a remote Linux server.",
                "Connect to a Mac via Apple Remote Desktop (ARD).",
                "Manage multiple VNC machines organized in groups.",
                "Auto-detect if vncviewer is installed, with per-distro install instructions.",
            ],
        },
    },
    "Traceroute": {
        "fr": {
            "desc": "Affiche le chemin réseau vers une destination avec géolocalisation en temps réel de chaque saut public sur une carte monde interactive (Natural Earth). Supporte traceroute et tracepath. La carte est zoomable/pannable, les points sont cliquables pour le détail.",
            "examples": [
                "Visualiser géographiquement le chemin d'un paquet vers un serveur étranger.",
                "Identifier à quel hop un paquet est perdu ou ralenti.",
                "Comparer les routes vers deux CDN différents.",
                "Détecter si le trafic passe par un pays inattendu (routage asymétrique).",
            ],
        },
        "en": {
            "desc": "Shows the network path to a destination with real-time geolocation of each public hop on an interactive world map (Natural Earth). Supports traceroute and tracepath. The map is zoomable/pannable with clickable points.",
            "examples": [
                "Visually see the geographic path of a packet to a foreign server.",
                "Identify at which hop a packet is lost or slowed down.",
                "Compare routes to two different CDNs.",
                "Detect if traffic passes through an unexpected country (asymmetric routing).",
            ],
        },
    },
    "MTR": {
        "fr": {
            "desc": "Combine traceroute et ping : affiche les statistiques de perte et de latence en continu pour chaque saut réseau via mtr --report. Tableau Hop/Hôte/Perte%/Envoyés/Dernier/Moy/Min/Max/Gigue avec coloration selon la perte.",
            "examples": [
                "Diagnostiquer une latence élevée en identifiant quel routeur est responsable.",
                "Mesurer la perte de paquets sur chaque saut vers un serveur de jeu.",
                "Comparer la qualité de deux liens internet (FTTH vs 4G) vers le même hôte.",
                "Générer un rapport MTR à partager avec le support d'un hébergeur.",
            ],
        },
        "en": {
            "desc": "Combines traceroute and ping: shows continuous loss and latency statistics for each network hop via mtr --report. Hop/Host/Loss%/Sent/Last/Avg/Min/Max/Jitter table with loss-based color coding.",
            "examples": [
                "Diagnose high latency by identifying which router is responsible.",
                "Measure packet loss on each hop to a game server.",
                "Compare quality of two internet links (FTTH vs 4G) to the same host.",
                "Generate an MTR report to share with a hosting provider's support.",
            ],
        },
    },
    "Firewall": {
        "fr": {
            "desc": "Lit et affiche les règles pare-feu nftables et iptables/ip6tables sans droits root (fichiers de config), avec possibilité d'afficher le ruleset live via pkexec. Colonnes Table/Chain/Règle/Port/Action/Commentaire avec filtrage en temps réel et coloration par action.",
            "examples": [
                "Vérifier rapidement les règles actives sans mémoriser la syntaxe nft/iptables.",
                "Filtrer les règles par port ou par chaîne (INPUT, OUTPUT, FORWARD).",
                "Comparer la configuration dans le fichier vs le ruleset live (pkexec).",
                "Identifier une règle DROP ou REJECT qui bloque un service.",
            ],
        },
        "en": {
            "desc": "Reads and displays nftables and iptables/ip6tables firewall rules without root (config files), with option to show live ruleset via pkexec. Table/Chain/Rule/Port/Action/Comment columns with live filtering and action-based color coding.",
            "examples": [
                "Quickly review active rules without memorizing nft/iptables syntax.",
                "Filter rules by port or chain (INPUT, OUTPUT, FORWARD).",
                "Compare config file vs live ruleset (pkexec).",
                "Identify a DROP or REJECT rule that is blocking a service.",
            ],
        },
    },
    "Speed Test": {
        "fr": {
            "desc": "Mesure le débit descendant (25 Mo), montant (10 Mo) et le ping via les serveurs Cloudflare (speed.cloudflare.com) à l'aide de curl. Affiche les résultats en temps réel, conserve un historique des 5 derniers tests et affiche un graphique de tendance.",
            "examples": [
                "Mesurer le débit réel d'une connexion internet depuis le terminal sans navigateur.",
                "Comparer les débits sur Wi-Fi vs Ethernet pour justifier un câblage.",
                "Surveiller l'évolution du débit dans le temps avec l'historique graphique.",
                "Détecter une dégradation de la connexion chez un client ou en déplacement.",
            ],
        },
        "en": {
            "desc": "Measures download (25 MB), upload (10 MB) and ping via Cloudflare servers (speed.cloudflare.com) using curl. Shows results in real time, keeps a history of the last 5 tests and displays a trend chart.",
            "examples": [
                "Measure actual internet throughput without a browser.",
                "Compare Wi-Fi vs Ethernet speeds to justify cabling.",
                "Monitor speed over time with the history chart.",
                "Detect connection degradation at a client site or on the road.",
            ],
        },
    },
    "Bandwidth": {
        "fr": {
            "desc": "Surveille le débit réseau en temps réel sur une interface sélectionnée. Affiche un graphique glissant de 60 secondes avec les courbes de download et upload, les vitesses actuelles, les totaux depuis le début du monitoring et les pics enregistrés.",
            "examples": [
                "Visualiser en temps réel l'utilisation de la bande passante pendant un téléchargement ou backup.",
                "Identifier quelle interface consomme le plus de trafic (Ethernet, Wi-Fi, VPN).",
                "Détecter un trafic réseau anormal ou inattendu en fond de tâche.",
                "Mesurer la vitesse effective d'un transfert local (NAS, VM) sur le réseau.",
            ],
        },
        "en": {
            "desc": "Monitors network throughput in real time on a selected interface. Shows a 60-second sliding chart with download and upload curves, current speeds, session totals and recorded peaks.",
            "examples": [
                "Visualize real-time bandwidth usage during a download or backup.",
                "Identify which interface consumes the most traffic (Ethernet, Wi-Fi, VPN).",
                "Detect unexpected background network traffic.",
                "Measure effective transfer speed of a local transfer (NAS, VM) on the network.",
            ],
        },
    },
    "Wake on LAN": {
        "fr": {
            "desc": "Envoie un Magic Packet UDP natif Python pour démarrer à distance un équipement via le réseau local. Gère un carnet d'hôtes persistant (JSON) avec nom, adresse MAC et adresse broadcast.",
            "examples": [
                "Démarrer un PC de bureau à distance avant d'y accéder via SSH ou RDP.",
                "Réveiller un NAS en veille avant un accès aux fichiers.",
                "Tester si le Wake on LAN est bien activé dans le BIOS d'un équipement.",
                "Gérer plusieurs équipements WoL (PC, serveurs, NAS) dans un carnet centralisé.",
            ],
        },
        "en": {
            "desc": "Sends a native Python UDP Magic Packet to remotely start a device over the local network. Manages a persistent host book (JSON) with name, MAC address and broadcast address.",
            "examples": [
                "Start a desktop PC remotely before accessing it via SSH or RDP.",
                "Wake up a sleeping NAS before accessing files.",
                "Test if Wake on LAN is enabled in a device's BIOS.",
                "Manage multiple WoL devices (PCs, servers, NAS) in a centralized book.",
            ],
        },
    },
    "Topology": {
        "fr": {
            "desc": "Génère une carte visuelle interactive des équipements découverts sur le réseau local via nmap -sn. Les nœuds sont déplaçables, les icônes distinguent routeur/moniteur/tour PC. Affiche l'IP, le MAC, le hostname et le fabricant au clic ou au survol.",
            "examples": [
                "Obtenir une vue graphique rapide des équipements actifs sur le LAN.",
                "Identifier visuellement la gateway et les équipements connectés autour d'elle.",
                "Détecter un équipement inconnu sur le réseau par son icône ou son fabricant.",
                "Utiliser la carte comme support visuel pour documenter l'infrastructure réseau.",
            ],
        },
        "en": {
            "desc": "Generates an interactive visual map of devices discovered on the local network via nmap -sn. Nodes are draggable, icons distinguish router/monitor/tower PC. Shows IP, MAC, hostname and manufacturer on click or hover.",
            "examples": [
                "Get a quick visual overview of active devices on the LAN.",
                "Visually identify the gateway and devices connected around it.",
                "Detect an unknown device on the network by its icon or manufacturer.",
                "Use the map as a visual support for documenting network infrastructure.",
            ],
        },
    },
}


def get_help(label: str) -> dict | None:
    """Return {desc, examples} for the given module label in the current language."""
    entry = _CONTENT.get(label)
    if not entry:
        return None
    lang = _get_settings().get("language", "fr")
    return entry.get(lang) or entry.get("fr")
