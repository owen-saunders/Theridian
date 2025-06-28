# Theridian

Theridian the Tangled Web aims to provide transparency and insight into the UK energy grid through simple data aggregation and visualisation of publicly available energy data from the various separated DNOs and energy data bodies.

---

## 🚀 Features

- Aggregates and visualizes UK energy grid data
- Modular ETL pipeline using Dagster
- Task orchestration with Celery and RabbitMQ
- Monitoring with Prometheus and Grafana
- REST API with Django and Django REST Framework

---

## 🛠️ Development Setup

Either run `scripts/setup.sh` to setup automatically or follow the manual steps below to set up your development environment.

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/theridian.git
cd theridian
```

### 2. Install Python Dependencies

Install dependencies using [Poetry](https://python-poetry.org/):

```bash
poetry install --with dev --no-root
```

### 3. Environment Variables

Copy `.env.example` to `.env` and update values as needed:

```bash
cp .env.example .env
```

### 4. Database Migrations

Apply migrations:

```bash
poetry run python manage.py migrate
```

### 5. Run the Development Server

```bash
poetry run python manage.py runserver
```

---

## 🐳 Docker Development

To start all services (Django, Celery, Dagster, Redis, RabbitMQ, Postgres, etc.):

```bash
docker compose -f docker-compose.dev.yml up --build
```

- The Django app will be available at [http://localhost:8000](http://localhost:8000)
- Dagster UI at [http://localhost:3000](http://localhost:3000)
- Grafana and Prometheus at their respective ports

### Common Docker Commands

- **Run migrations in the container:**
  ```bash
  docker compose -f docker-compose.dev.yml exec web python manage.py migrate
  ```
- **Create a superuser:**
  ```bash
  docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
  ```

---

## 🧪 Testing

Run tests with:

```bash
poetry run python manage.py test
```

---

## 📂 Project Structure

```
apps/           # Django apps (api, etl, etc.)
core/           # Django project settings
scripts/        # Utility and setup scripts
static/         # Static files
templates/      # Django templates
media/          # Uploaded media files
docker-compose.dev.yml
Dockerfile.dev
workspace.yml   # Dagster workspace config
```

---

## 📊 Monitoring

- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Grafana**: [http://localhost:3001](http://localhost:3001)

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Create a new Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 📚 More Information

- See [docs/](docs/) for more details and advanced usage.
- For troubleshooting, check the [FAQ](docs/FAQ.md) or open an

