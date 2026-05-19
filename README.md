Restoran Rezervasyon Sitesi
Kubernetes ve CI/CD Final Projesi
Bartın Üniversitesi
Bilgisayar Mühendisliği Bölümü
Bulut Bilişim Dersi Final Projesi
Ad Soyad: Kerem Ofluoğlu, Metehan Güçlü

Proje Hakkında
Bu projede Flask tabanlı bir restoran rezervasyon web sitesi Docker container yapısına dönüştürülmüş ve Google Kubernetes Engine (GKE) ortamında çalıştırılmıştır. Proje kapsamında uygulama yüksek erişilebilirlik, ölçeklenebilirlik ve sürdürülebilir dağıtım mantığıyla yapılandırılmıştır.
Sistem; Kubernetes üzerinde Deployment, Service, Ingress, Persistent Volume Claim, Secret ve NetworkPolicy kullanılarak çalıştırılmıştır. Ayrıca GitHub Actions tabanlı bir CI/CD pipeline kurulmuş, main branch'e yapılan her push ile otomatik deployment süreci gerçekleştirilmektedir.
Proje boyunca amaç; klasik bir web uygulamasını modern bulut teknolojileri kullanarak container tabanlı bir mimariye taşımak ve otomatik dağıtım süreçlerini uygulamalı olarak gerçekleştirmektir.

Kullanılan Teknolojiler
  • Docker
  • Kubernetes (GKE — Google Kubernetes Engine)
  •	GitHub Actions (CI/CD)
  •	GCP Artifact Registry (europe-west1)
  •	GCP Workload Identity Federation
  •	Python / Flask
  •	PostgreSQL 16
  •	psycopg2
  •	Kubernetes Ingress (nginx)
  •	Ubuntu Linux

Uygulama Mimarisi
Projede temel olarak iki ana container bulunmaktadır:
•	Restoran rezervasyon sitesinin çalıştığı Flask (Python) web container'ı
•	Veritabanı işlemlerini yöneten PostgreSQL container'ı

Kullanıcı web sitesine eriştiğinde istekler Ingress üzerinden restoran-service'e, oradan Flask pod'larına yönlendirilir. Rezervasyon bilgileri (ad-soyad, telefon, tarih, saat, kişi sayısı, notlar) PostgreSQL veritabanının randevular tablosunda tutulmaktadır.

Flask uygulamasındaki rotalar:
•	GET /  — Ana sayfa (index.html)
•	GET+POST /randevu  — Rezervasyon formu; POST geldiğinde DB'ye INSERT
•	GET /basarili  — Başarılı rezervasyon sayfası
•	GET /admin  — Tüm rezervasyonları listeleyen yönetim paneli (SELECT *)
•	GET /health  — {"status": "ok"} döndüren sağlık kontrolü

Uygulama container mantığıyla çalıştığı için sistem farklı ortamlara kolayca taşınabilmektedir.

Kubernetes Mimarisi
Projede Kubernetes üzerinde aşağıdaki bileşenler kullanılmıştır:

Deployment
Deployment yapısı ile uygulamanın belirli sayıda Pod ile çalışması sağlanmıştır. Sistem istenildiğinde kolayca ölçeklenebilmektedir.

Kullanılan deployment'lar:
•	restoran-deployment — 3 replica, Flask uygulaması, port 5000
•	postgres-deployment — 1 replica, PostgreSQL 16, port 5432

Her iki deployment da veritabanı bağlantı bilgilerini restoran-secret üzerinden env değişkeni olarak almaktadır. Image tag olarak github.sha kullanılmaktadır; bu sayede her deployment immutable (değiştirilemez) bir image sürümüne karşılık gelir.

Deployment sayesinde:
•	Otomatik Pod yönetimi
•	Rolling update
•	Rollback işlemleri
•	Replica kontrolü
gerçekleştirilmektedir.

Service
Kubernetes Service yapısı ile Pod'ların birbirlerine ve Ingress üzerinden dış dünyaya açılması sağlanmıştır.

Projede:
•	Web uygulaması için ClusterIP Service (restoran-service) — 80 → 5000
•	Veritabanı için ClusterIP Service (postgres-service) — 5432 → 5432
kullanılmıştır.

Dış erişim, ClusterIP'nin önüne konumlanan Ingress (nginx) üzerinden sağlanmaktadır.

Ingress
Dışarıdan gelen HTTP trafiği restoran-ingress üzerinden restoran-service'e yönlendirilmektedir. nginx ingress controller kullanılmış olup tüm path prefix'leri (/) servis tarafından karşılanmaktadır.

Persistent Volume ve PVC
PostgreSQL verilerinin Pod silinse bile kaybolmaması amacıyla PersistentVolumeClaim kullanılmıştır.

Kullanılan PVC:
•	Ad: restoran-volume
•	Kapasite: 1Gi
•	Erişim modu: ReadWriteOnce
•	PGDATA env değişkeni ile /var/lib/postgresql/data/pgdata subdirectory'sine yönlendirilmiştir

Bu yapı sayesinde container yeniden başlasa ya da silinse bile tüm rezervasyon verileri korunmaktadır.

Secret
Veritabanı bağlantı bilgileri (host, name, user, password) Kubernetes Secret olarak saklanmakta ve her iki deployment'a da env değişkeni olarak inject edilmektedir. Bu sayede hassas bilgiler YAML dosyalarına açık metin olarak yazılmamaktadır.

NetworkPolicy
Güvenlik amacıyla Kubernetes NetworkPolicy kullanılmıştır. Üç ayrı kural tanımlanmıştır:

•	flask-policy — Yalnızca ingress-nginx namespace'inden gelen trafiğin :5000'e ulaşmasına ve yalnızca postgres pod'larına :5432 ile DNS (UDP/TCP 53) üzerinden egress açılmasına izin verir
•	postgres-policy — Yalnızca restoran pod'larının :5432'ye erişmesine izin verir
•	default-deny — Diğer tüm ingress ve egress trafiğini engeller

Bu yapı sayesinde Kubernetes ağı içerisinde minimum ayrıcalık prensibine dayalı güvenli bir iletişim modeli oluşturulmuştur.

Docker Yapısı
Uygulama için özel bir Dockerfile hazırlanmıştır. Temel image olarak python:3.12-slim kullanılmış ve katmanlar şu sırayla oluşturulmuştur:

1.	FROM python:3.12-slim — Hafif base image
2.	WORKDIR /app — Çalışma dizini
3.	COPY requirements.txt . && pip install — Bağımlılıklar (Flask, psycopg2-binary vb.)
4.	COPY app.py . && COPY templates/ — Uygulama dosyaları
5.	EXPOSE 5000 — Port tanımı
6.	CMD ["python", "app.py"] — Başlatma komutu

Docker image oluşturulduktan sonra GCP Artifact Registry'nin europe-west1 bölgesine (europe-west1-docker.pkg.dev) yüklenmektedir. Her build'de github.sha ile etiketlenmekte, bu sayede Kubernetes cluster içindeki Pod'lar her zaman doğru ve izlenebilir image sürümünü çekmektedir.

CI/CD Pipeline Süreci
Projede GitHub Actions kullanılarak otomatik CI/CD pipeline sistemi kurulmuştur. Pipeline yalnızca main branch'e push yapıldığında tetiklenmektedir.

Süreç şu şekilde çalışmaktadır:
7.	Proje GitHub repository'sine (main branch) push edilir
8.	GitHub Actions workflow otomatik olarak tetiklenir
9.	actions/checkout ile kaynak kod alınır
10.	google-github-actions/auth ile GCP Workload Identity Federation üzerinden kimlik doğrulaması yapılır (key'siz, güvenli yöntem)
11.	gcloud auth configure-docker ile Artifact Registry'ye Docker erişimi ayarlanır
12.	get-gke-credentials ile restoran-cluster'a (europe-west1-b) kubectl erişimi kurulur
13.	docker build ile ./app dizininden image oluşturulur; image:github.sha ile etiketlenir
14.	docker push ile image Artifact Registry'ye gönderilir
15.	sed ile YAML içindeki $IMAGE_TAG, github.sha ile değiştirilir
16.	kubectl apply ile tüm k8s manifest dosyaları uygulanır (secret, pvc, deployments, network-policy, ingress)
17.	kubectl set image ile deployment güncel image'a geçirilir

Bu yapı sayesinde manuel deployment ihtiyacı tamamen ortadan kalkmıştır.

Sistem Mimarisi
Projenin genel çalışma yapısı aşağıdaki gibidir:

GitHub (main push)  →  GitHub Actions  →  GCP Artifact Registry  →  GKE Cluster

GKE Cluster içindeki trafik akışı:

Kullanıcı  →  Ingress (nginx)  →  restoran-service (ClusterIP)  →  Flask Pods  →  postgres-service  →  PostgreSQL Pod  →  PVC

Bu mimari sayesinde:
•	Kod değişiklikleri otomatik dağıtılmaktadır
•	Tüm sürümler Artifact Registry'de izlenebilir şekilde saklanmaktadır
•	Ağ güvenliği NetworkPolicy ile minimum ayrıcalık prensibiyle sağlanmaktadır
•	Veriler PVC sayesinde kalıcı olarak korunmaktadır
•	3 replica ile yüksek erişilebilirlik sağlanmaktadır

Rolling Update İşlemi
Deployment güncellemesi sırasında Kubernetes rolling update mekanizması kullanılmaktadır. CI/CD pipeline'ında her push'ta kubectl set image komutu çalışır:

kubectl set image deployment/restoran-deployment restoran=europe-west1-docker.pkg.dev/<PROJECT>/restoran/restoran:<SHA>

Bu işlem sayesinde:
•	Sistem tamamen kapanmadan güncelleme yapılmaktadır
•	Yeni Pod'lar çalışır duruma gelirken eski Pod'lar kontrollü şekilde kapatılmaktadır
•	3 replica sayesinde güncelleme süresince hizmet kesintisiz devam etmektedir

Rollback İşlemi
Hatalı bir güncelleme durumunda sistem önceki sürüme döndürülebilmektedir:

kubectl rollout undo deployment/restoran-deployment

Belirli bir revizyona dönmek için:

kubectl rollout history deployment/restoran-deployment
kubectl rollout undo deployment/restoran-deployment --to-revision=<N>

Bu özellik, üretim ortamında hızlı hata giderme açısından Kubernetes'in en kritik avantajlarından biridir.

Ölçekleme (Scaling)
Projede uygulama varsayılan olarak 3 replica ile çalışacak şekilde yapılandırılmıştır. Yük altında ihtiyaç duyulursa replica sayısı manuel olarak artırılabilir:

kubectl scale deployment restoran-deployment --replicas=5

Mevcut durumu kontrol etmek için:

kubectl get deployment restoran-deployment
kubectl get pods -l app=restoran

Ölçekleme işlemi Deployment seviyesinde gerçekleştiğinden Service ve Ingress katmanları herhangi bir değişiklik gerektirmeden yeni Pod'lara otomatik olarak trafik yönlendirir.

Deployment, Service, PV/PVC ve NetworkPolicy Kullanımı
Projede kullanılan tüm Kubernetes kaynakları ve rolleri özet olarak:

•	restoran-deployment — Flask uygulamasını 3 replica ile çalıştırır; secret'ten env alır, image:sha ile güncellenir
•	postgres-deployment — PostgreSQL'i 1 replica ile çalıştırır; PVC'yi mount eder
•	restoran-service — ClusterIP, 80:5000 forward, Ingress'in hedefi
•	postgres-service — ClusterIP, 5432:5432, yalnızca cluster içinden erişilebilir
•	restoran-ingress — nginx, dış HTTP trafiğini restoran-service'e yönlendirir
•	restoran-volume (PVC) — 1Gi ReadWriteOnce, PostgreSQL veri kalıcılığını sağlar
•	restoran-secret — base64 kodlu DB bağlantı bilgileri, her iki deployment'a inject edilir
•	flask-policy — Flask pod'larına yalnızca nginx'ten giriş, yalnızca postgres'e ve DNS'e çıkış
•	postgres-policy — PostgreSQL'e yalnızca restoran pod'larından giriş
•	default-deny — Tanımlanmayan tüm trafik engellenir

Repository İçeriği
Repository içerisinde aşağıdaki dosyalar bulunmaktadır:

•	app/Dockerfile — Python:3.12-slim tabanlı image tanımı
•	app/app.py — Flask uygulama kodu (rotalar, DB bağlantısı, init_db)
•	app/requirements.txt — Python bağımlılıkları (Flask, psycopg2-binary)
•	app/templates/ — HTML şablonları (index, randevu, basarili, admin)
•	k8s/restoran-deployment.yaml — Flask deployment + restoran-service
•	k8s/postgres-deployment.yaml — PostgreSQL deployment + postgres-service
•	k8s/ingress.yaml — nginx Ingress kaynağı
•	k8s/pvc.yaml — PersistentVolumeClaim (restoran-volume, 1Gi)
•	k8s/secret.yaml — Opaque Secret (DB bilgileri)
•	k8s/network-policy.yaml — flask-policy, postgres-policy, default-deny
•	.github/workflows/deploy.yaml — GitHub Actions CI/CD pipeline

Kazanımlar
Bu proje sayesinde:

•	Docker container mantığı ve çok katmanlı image oluşturma öğrenildi
•	Kubernetes temel bileşenleri (Deployment, Service, Ingress, PVC, Secret, NetworkPolicy) uygulamalı şekilde kullanıldı
•	GitHub Actions ile CI/CD süreçleri deneyimlendi
•	GCP Workload Identity Federation ile güvenli, key'siz kimlik doğrulama kuruldu
•	GCP Artifact Registry ile image versiyonlama ve dağıtım yönetimi gerçekleştirildi
•	Rolling update ve rollback işlemleri uygulandı
•	Kubernetes NetworkPolicy ile minimum ayrıcalık prensibi hayata geçirildi
•	Gerçek bir web uygulamasının GKE ortamına taşınma süreci deneyimlendi

Sonuç
Bu projede Flask tabanlı bir restoran rezervasyon uygulaması modern container teknolojileri kullanılarak GKE ortamına taşınmıştır. GitHub Actions destekli CI/CD pipeline ile uygulamanın her push'ta otomatik olarak build edilip deploy edilmesi sağlanmıştır.

Proje kapsamında Deployment, Service, Ingress, Persistent Volume Claim, Secret, NetworkPolicy, rolling update, rollback ve ölçekleme işlemleri başarıyla uygulanmıştır. Güvenlik katmanı olarak üç ayrı NetworkPolicy kuralıyla cluster içi trafik sıkı biçimde kontrol altına alınmıştır.

Bulut bilişim teknolojilerinin gerçek kullanım senaryoları uygulamalı olarak deneyimlenmiş ve modern yazılım dağıtım süreçleri öğrenilmiştir.
