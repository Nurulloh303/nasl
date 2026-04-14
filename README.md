# nasl.ai backend

Productionga yaqin Django + DRF backend.

## Nimalar tayyor

- JWT auth
- Telegram orqali register/login endpoint
- Click payment boshlash va callback qabul qilish
- Token/credit asosidagi balans tizimi
- Har bir generatsiya uchun token yechish
- Xato bo'lsa tokenni qaytarish
- Transaction history
- Swagger docs
- SQLite bilan tez start, PostgreSQL bilan production

## Pricing

- Mini Pack — 22 000 so'm — 50 token — 10 ta generatsiya
- Medium Pack — 50 000 so'm — 110 token — 22 ta generatsiya
- Big Pack — 110 000 so'm — 250 token — 50 ta generatsiya

`GENERATION_TOKEN_COST=5`, demak 1 generatsiya = 5 token.

## Tez start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py loaddata apps/accounts/fixtures/pricing_data.json
python manage.py createsuperuser
python manage.py runserver
```

Local test uchun `.env` ichida:

- `DB_ENGINE=sqlite`
- `CELERY_TASK_ALWAYS_EAGER=True`
- `DEFAULT_GENERATION_PROVIDER=mock`

## Asosiy endpointlar

### Auth
- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/telegram-auth/`
- `GET /api/v1/auth/me/`

### Payment
- `GET /api/v1/payment/pricing/`
- `POST /api/v1/payment/initiate-payment/`
- `POST /api/v1/payment/complete-payment/`
- `GET /api/v1/payment/transactions/`
- `POST /api/v1/payment/buy-demo/`

### Generation
- `POST /api/v1/generate/prompt-preview/`
- `POST /api/v1/generate/submit/`
- `GET /api/v1/generate/requests/`
- `GET /api/v1/generate/requests/<uuid:id>/`

## Telegram auth payload

```json
{
  "telegram_id": "123456789",
  "username": "asilbekdev",
  "first_name": "Asilbek",
  "last_name": "Abdugafforov",
  "full_name": "Asilbek Abdugafforov"
}
```

Javobda `access`, `refresh`, `user` qaytadi.

## Payment flow

1. Frontend pricing oladi.
2. User `tier_id` tanlaydi.
3. `initiate-payment` transaction yaratadi va Click URL qaytaradi.
4. Click callback `complete-payment` ga uradi.
5. Transaction completed bo'ladi.
6. User profiliga token qo'shiladi.
7. `transactions/` orqali tarix ko'rinadi.

## Generation flow

- Userda token bo'lsa 5 token yechiladi.
- Token bo'lmasa, agar bepul limit tugamagan bo'lsa 1 ta bepul generatsiya ishlaydi.
- Generatsiya xato bilan tugasa, token qaytariladi.

## Frontendga kerak bo'ladigan payment response

`GET /api/v1/payment/pricing/` response har tier uchun quyidagilarni beradi:

- `amount`
- `tokens`
- `generations`
- `is_popular`

## Click sozlash

`.env` ichiga quyidagilarni to'ldirasan:

```env
CLICK_MERCHANT_ID=
CLICK_SERVICE_ID=
CLICK_SECRET_KEY=
CLICK_CALLBACK_URL=https://api.seningsayting.uz/api/v1/payment/complete-payment/
CLICK_RETURN_URL=https://seningsayting.uz/payment/success
CLICK_FAIL_URL=https://seningsayting.uz/payment/fail
```

Agar ular bo'sh qolsa, backend demo rejimda `buy-demo/` endpoint bilan ishlaydi.

## Deploy qisqacha

### Ubuntu

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx redis-server postgresql postgresql-contrib
```

```bash
git clone <repo>
cd naslai_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python manage.py migrate
python manage.py loaddata apps/accounts/fixtures/pricing_data.json
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Gunicorn test:

```bash
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

Systemd service namunasi:

```ini
[Unit]
Description=nasl.ai backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/naslai_backend
EnvironmentFile=/var/www/naslai_backend/.env
ExecStart=/var/www/naslai_backend/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

Nginx namunasi:

```nginx
server {
    server_name api.example.com;

    client_max_body_size 50M;

    location /media/ {
        alias /var/www/naslai_backend/media/;
    }

    location /static/ {
        alias /var/www/naslai_backend/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Keyin SSL:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.example.com
```

## Eslatma

Telegram bot token backend uchun shart emas, lekin real Telegram bot ishlashi uchun kerak bo'ladi. Bot user ma'lumotini `telegram-auth/` endpointga yuboradi.
