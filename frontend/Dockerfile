FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./
COPY --from=builder /app/.next/static ./.next/static

# Copy full build (needed for npm start fallback)
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules

# Create startup script that handles both standalone and regular mode
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'set -e' >> /app/start.sh && \
    echo 'if [ -f "./.next/standalone/server.js" ]; then' >> /app/start.sh && \
    echo '  echo "Starting with standalone server..."' >> /app/start.sh && \
    echo '  cd ./.next/standalone && node server.js' >> /app/start.sh && \
    echo 'else' >> /app/start.sh && \
    echo '  echo "Starting with npm start..."' >> /app/start.sh && \
    echo '  npm start' >> /app/start.sh && \
    echo 'fi' >> /app/start.sh && \
    chmod +x /app/start.sh

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Use the startup script
CMD ["/app/start.sh"]

