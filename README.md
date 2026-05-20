# Restoran Rezervasyon Sitesi  
### Kubernetes ve CI/CD Final Projesi  
**Bartın Üniversitesi – Bilgisayar Mühendisliği Bölümü**  
**Bulut Bilişim Dersi Final Projesi**

**Ad Soyad:** Kerem Ofluoğlu, Metehan Güçlü  

---

## Proje Hakkında

Bu projede Flask tabanlı bir restoran rezervasyon web sitesi Docker container yapısına dönüştürülmüş ve Google Kubernetes Engine (GKE) ortamında çalıştırılmıştır.

Sistem; yüksek erişilebilirlik, ölçeklenebilirlik ve sürdürülebilir dağıtım prensipleriyle tasarlanmıştır.

Kubernetes üzerinde aşağıdaki bileşenler kullanılmıştır:

- Deployment  
- Service  
- Ingress  
- Persistent Volume Claim (PVC)  
- Secret  
- NetworkPolicy  

Ayrıca GitHub Actions tabanlı CI/CD pipeline ile `main` branch'e yapılan her push sonrası otomatik deployment sağlanmıştır.

---

## Kullanılan Teknolojiler

- Docker  
- Kubernetes (GKE – Google Kubernetes Engine)  
- GitHub Actions (CI/CD)  
- GCP Artifact Registry  
- GCP Workload Identity Federation  
- Python / Flask  
- PostgreSQL 16  
- psycopg2  
- NGINX Ingress Controller  
- Ubuntu Linux  

---

## Uygulama Mimarisi

Sistem iki ana container’dan oluşur:

- Flask web uygulaması (restoran rezervasyon sistemi)
- PostgreSQL veritabanı

Kullanıcı akışı:
Kullanıcı → Ingress → restoran-service → Flask Pod’ları → PostgreSQL → PVC

---

## Flask API Endpoints

- `GET /` → Ana sayfa  
- `GET + POST /randevu` → Rezervasyon oluşturma  
- `GET /basarili` → Başarı sayfası  
- `GET /admin` → Tüm rezervasyonları listeleme  
- `GET /health` → Sağlık kontrolü (`{"status": "ok"}`)  

---

## Kubernetes Mimarisi

### Deployment

- `restoran-deployment` → Flask uygulaması (3 replica)
- `postgres-deployment` → PostgreSQL (1 replica)

Özellikler:
- Rolling update desteği  
- Rollback imkanı  
- Immutable image (github.sha tag)  

---

### Service

- `restoran-service` → Flask (80 → 5000)
- `postgres-service` → PostgreSQL (5432)

---

### Ingress

NGINX Ingress Controller kullanılarak dış erişim sağlanır.

---

### Persistent Volume (PVC)

- 1Gi storage kullanılmıştır

---

### Secret

- DB bilgileri (host, user, password) Secret içinde tutulur

---

### NetworkPolicy

- `default-deny` → tüm trafiği kapatır  
- `flask-policy` → sadece nginx ve postgres erişimi  
- `postgres-policy` → sadece flask erişimi  

---

## Docker Yapısı

Dockerfile:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .
COPY templates/ .

EXPOSE 5000

CMD ["python", "app.py"]
