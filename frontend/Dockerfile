FROM node:20-alpine

WORKDIR /app

# Install deps first (layer cache)
COPY package*.json ./
RUN npm ci --ignore-scripts

# Copy source
COPY . .

EXPOSE 5173

# Vite dev server — bind to 0.0.0.0 so Docker port mapping works
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
