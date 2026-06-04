# Mallard dashboard image. Built by infra/docker-compose.yml (service: web).
FROM node:22-slim AS base
ENV NODE_ENV=production
WORKDIR /app
RUN corepack enable

# Install dependencies first (better layer caching).
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Build.
COPY . .
RUN pnpm build

EXPOSE 3000
CMD ["pnpm", "start"]
