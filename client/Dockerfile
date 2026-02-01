# Build Stage
FROM node:20-slim AS build-stage

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
# Install dependencies with retry and increased timeout
RUN npm config set fetch-retry-maxtimeout 600000 && \
    npm config set fetch-retry-mintimeout 10000 && \
    npm ci

# Copy project files
COPY . .

# Build the app for production
RUN npm run build

# Production Stage
FROM nginx:alpine AS production-stage

# Copy the built files from the previous stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom nginx configuration if needed (optional)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
