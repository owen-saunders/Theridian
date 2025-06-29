#!/bin/bash
set -e

echo "🚀 Setting up Django API Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install Poetry first:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
else
    print_status "Poetry is installed."
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
else
    print_status "Docker is running."
fi

# Check if .env file exists
if [ ! -f .env.docker ]; then
    print_warning ".env file not found. Copying from .env.example..."
    cp .env.example .env.docker
    print_warning "Please edit .env.docker file with your configuration before continuing."
    echo "Press any key to continue..."
    read -n 1 -s
else
    print_status ".env.docker file found."
fi

# Install Python dependencies
print_status "Installing Python dependencies with Poetry..."
poetry install --no-root

# Install development dependencies
print_status "Installing development dependencies..."
poetry install --with dev --no-root

# Install pre-commit hooks
print_status "Setting up pre-commit hooks..."
poetry run pre-commit install

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p static
mkdir -p media
mkdir -p templates
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p apps/api/tests apps/etl/tests
mkdir -p dagster_home/storage

# Create __init__.py files
print_status "Creating __init__.py files..."
touch apps/__init__.py
touch apps/api/__init__.py
touch apps/etl/__init__.py
touch apps/api/tests/__init__.py
touch apps/etl/tests/__init__.py
touch core/__init__.py
touch core/settings/__init__.py

# Start Docker services
print_status "Starting Docker services..."
docker-compose --env-file .env.docker -f docker-compose.dev.yml up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check if PostgreSQL is ready
print_status "Checking PostgreSQL connection..."
until docker-compose -f docker-compose.dev.yml exec db pg_isready -U postgres; do
    print_warning "Waiting for PostgreSQL..."
    sleep 5
done

# Check if Redis is ready
print_status "Checking Redis connection..."
until docker-compose -f docker-compose.dev.yml exec redis redis-cli ping; do
    print_warning "Waiting for Redis..."
    sleep 5
done

# Check if web service is ready
print_status "Checking web service readiness..."
until docker-compose -f docker-compose.dev.yml exec web curl -s http://localhost:8000/api/health/; do
    print_warning "Waiting for web service..."
    sleep 5
done

# Run Django setup commands
print_status "Running Django setup commands..."

# Make migrations
print_status "Creating initial migrations..."
poetry run python manage.py makemigrations
docker compose -f docker-compose.dev.yml exec web python manage.py makemigrations


# Apply migrations
print_status "Applying migrations..."
docker compose -f docker-compose.dev.yml exec web python manage.py migrate

# Collect static files
print_status "Collecting static files..."
docker compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
print_status "Creating superuser..."
docker compose -f docker-compose.dev.yml exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
"

# Test the setup
print_status "Testing the setup..."
docker compose -f docker-compose.dev.yml exec web python manage.py check

# Run a quick test (Fails if django-debug-toolbar is active, because Debug=False when testing)
# print_status "Running quick tests..."
# docker compose -f docker-compose.dev.yml exec web python manage.py test --keepdb --verbosity=1

print_status "Displaying ps -a output..."
docker compose -f docker-compose.dev.yml ps -a

print_warning "If Services are exiting with errors, check the logs:"
echo "docker compose -f docker-compose.dev.yml logs -f"

print_warning "You may need to rebuild a service if you change its Dockerfile or dependencies:"
echo "docker compose -f docker-compose.dev.yml build <service_name>"

print_status "✅ Setup completed successfully!"
echo ""
echo "🎉 Your Django API Platform is ready!"
echo ""
echo "📋 Available services:"
echo "   • API Server: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/api/docs/"
echo "   • Admin Panel: http://localhost:8000/admin/ (admin/admin123)"
echo "   • Dagster UI: http://localhost:3000"
echo "   • Grafana: http://localhost:3001 (admin/admin)"
echo "   • Prometheus: http://localhost:9090"
echo "   • RabbitMQ: http://localhost:15672 (admin/admin)"
echo ""
echo "🚀 To start developing:"
echo "   poetry run python manage.py runserver"
echo ""
echo "📚 Check the README.md for more information."
