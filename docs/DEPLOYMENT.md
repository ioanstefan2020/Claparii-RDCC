# Ghid de Instalare & Rulare PrimaZi pe Server Oracle Cloud (Docker)

Acest ghid conține pașii exacți pentru a rula aplicația **PrimaZi** pe o mașină virtuală Oracle Cloud Always Free (Ubuntu sau Oracle Linux), astfel încât să fie accesibilă public pe internet pentru juriu și demo.

---

## Pasul 1: Conectare pe serverul Oracle Cloud

Conectează-te prin SSH pe serverul tău:
```bash
ssh -i /cale/catre/cheia-ta.key ubuntu@<IP_PUBLIC_SERVER>
# (sau opc@<IP_PUBLIC_SERVER> dacă ai ales imaginea Oracle Linux)
```

---

## Pasul 2: Instalare Docker & Docker Compose (dacă nu sunt instalate)

Rulează aceste comenzi pe server:
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```
*(Dacă ești pe Oracle Linux, înlocuiește `apt-get` cu `dnf`).*

---

## Pasul 3: Clonarea depozitului privat GitHub

Fiind un depozit privat, ai 2 opțiuni foarte simple:

### Opțiunea A (Recomandată: Token GitHub Personal Access)
1. Mergi pe GitHub: **Settings -> Developer Settings -> Personal access tokens -> Tokens (classic)**.
2. Generează un token cu bifa `repo`.
3. Pe serverul Oracle, rulează comanda de clonare cu token:
```bash
git clone https://<GITHUB_TOKEN>@github.com/ioanstefan2020/Claparii-RDCC.git primazi
cd primazi
```

### Opțiunea B (Direct de pe laptopul tău cu `rsync` sau `scp`)
Dacă nu vrei să creezi un token GitHub pe server, trimite codul direct de pe laptopul tău:
```bash
rsync -avz --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
  -e "ssh -i /cale/catre/cheia.key" \
  /home/chronosec/Projects/Hackathons/RDCC-Accesability/ \
  ubuntu@<IP_PUBLIC_SERVER>:~/primazi/
```

---

## Pasul 4: Configurarea fișierului `.env`

Pe server, în directorul `primazi`:
```bash
cp .env.example .env
nano .env   # sau folosește editorul preferat
```
Completează cheile de acces API (Groq, DeepSeek, Gemini).

---

## Pasul 5: Deschiderea Porturilor (Important pe Oracle Cloud!)

> [!WARNING]
> Pe Oracle Cloud, traficul este blocat implicit atât de **Security List (Panoul Web)**, cât și de **firewall-ul intern Linux (iptables)**. Trebuie deschise ambele:

### A. În panoul Web Oracle Cloud:
1. Mergi la **Compute -> Instances -> instanța ta**.
2. Click pe **Subnet -> Default Security List**.
3. Apasă pe **Add Ingress Rules**:
   - **Source CIDR:** `0.0.0.0/0`
   - **IP Protocol:** `TCP`
   - **Destination Port Range:** `80, 8000`
   - **Description:** `HTTP Web and API`

### B. În consola serverului (Firewall-ul sistemului de operare Linux):
Rulează aceste comenzi pe server:
```bash
# Deschide portul 80 și 8000 în iptables
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT

# Salvează regulile pentru a persista la restart
sudo netfilter-persistent save 2>/dev/null || sudo iptables-save | sudo tee /etc/iptables/rules.v4 2>/dev/null || true

# Dacă serverul folosește UFW (Ubuntu):
sudo ufw allow 80/tcp 2>/dev/null || true
sudo ufw allow 8000/tcp 2>/dev/null || true
```

---

## Pasul 6: Pornirea Aplicației cu Docker Compose

În folderul `primazi` de pe server:
```bash
docker compose up -d --build
```

Verifică starea containerului:
```bash
docker compose ps
docker compose logs -f
```

---

## Pasul 7: Accesarea Aplicației în Browser

Deschide în browserul tău:
- **Aplicația Web:** `http://<IP_PUBLIC_SERVER>/` (se deschide direct pe portul standard HTTP 80!)
- **Health Check API:** `http://<IP_PUBLIC_SERVER>/api/health`
- **Extensia de Browser:** 
  În setările extensiei din browserul tău, setează la **Adresă server API PrimaZi**:
  `http://<IP_PUBLIC_SERVER>:8000` (sau `http://<IP_PUBLIC_SERVER>`)
