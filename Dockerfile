# TODO: Make the image use the production tools (gunicorn and nginx)

# Step 1. Use base image with python
FROM python:3.11-slim as develop-stage

# Step 2. Install Python dependencies and Node.js
WORKDIR /app
RUN apt-get update && apt-get install -y nodejs npm \
&& npm install -g @quasar/cli \
&& apt-get clean && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 3. Install Node.js dependencies for the Vue app
COPY framework/web_app/package*.json ./
RUN npm install

# Step 4. Copy all files (minus ignored via .dockerignore)
COPY . .

# Step 5. Build the Vue app
FROM develop-stage as build-stage
WORKDIR /app/framework/web_app
RUN quasar build
WORKDIR /app

# # Step 6. Install Nginx and Gunicorn
# FROM nginx:stable-alpine as production-stage
# COPY nginx.conf /etc/nginx/conf.d/default.conf
# COPY --from=build-stage /app/framework/web_app/dist/spa /usr/share/nginx/html

# RUN pip install gunicorn
# # RUN apt-get update && apt-get install -y nginx \
# #     && pip install gunicorn \
# #     && apt-get clean && rm -rf /var/lib/apt/lists/*

# # Step 7. Add bash to image
# RUN apk add --no-cache bash

# Step 8. Expose the necessary ports
EXPOSE 5170 5172 5174

# Step 9. Run services
COPY startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh
CMD ["bash", "/usr/local/bin/startup.sh"]

# CMD ["python", "framework/dora_api/startup.py"]
# CMD ["bash", "-c", "python framework/dora_api/startup.py & python framework/merchant_api/startup.py & python framework/emailer/startup.py & quasar serve /app/framework/web_app/dist/spa & wait"]
