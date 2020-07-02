FROM ubuntu:18.04
LABEL maintainer="Calvin Rose"
ENV DEBIAN_FRONTEND=noninteractive

# Get correct node version as ubuntu's default version is too old
# Then install deps
RUN dpkg --add-architecture i386 \
    && apt-get -y update \
    && apt-get -y upgrade \
    && apt-get -y install curl python3 python3-pip nginx supervisor redis-server \
    && curl -sL https://deb.nodesource.com/setup_12.x | bash - \
    && apt-get install -y nodejs \
    && pip3 install pipenv \
    && mkdir -p /app/logs/

# Build frontend -> /app/frontend
COPY frontend/ /app/frontend-temp/
WORKDIR /app/frontend-temp
RUN npm i \
    && npx ng build --configuration=production \
    && mkdir -p /app/frontend \
    && cp -r dist/* /app/frontend/

# Remove temporary frontend
WORKDIR /app/backend
RUN rm -rf /app/frontend-temp

# Build backend -> /app/backend
COPY backend/ /app/backend/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV COMPILER_HUB_DATABASE_CREDENTIALS="dbname=cvf2 user=postgres password=cvtf123! host=cv-framework.nvidia.com port=5431"
ENV COMPILER_HUB_DATABASE_READONLY_CREDENTIALS="dbname=cvf2 user=postgres_readonly password=cvtf456! host=cv-framework.nvidia.com port=5431"
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --python `which python3`

# Configuration files
COPY nginx/docker.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Ports
EXPOSE 80

# Supervisord runs all of the child processes
CMD ["supervisord"]
