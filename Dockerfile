FROM node:22-bookworm-slim AS builder

WORKDIR /app

RUN apt-get update -y \
  && apt-get install -y --no-install-recommends openssl \
  && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json ./
RUN npm ci

COPY prisma ./prisma
COPY prisma.config.ts ./
COPY src ./src
COPY tsconfig.json ./

ENV DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/ciatec_research"

RUN npx prisma generate && npm run build

FROM node:22-bookworm-slim AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3333

RUN apt-get update -y \
  && apt-get install -y --no-install-recommends openssl \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd --gid 1001 nodejs \
  && useradd --uid 1001 --gid nodejs --shell /bin/bash --create-home nodejs

COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/prisma.config.ts ./prisma.config.ts
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder /app/node_modules/@prisma/client ./node_modules/@prisma/client

RUN chown -R nodejs:nodejs /app

USER nodejs

EXPOSE 3333

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD node -e "const p=process.env.PORT||'3333';fetch('http://127.0.0.1:'+p+'/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["sh", "-c", "set -e; npx prisma migrate deploy; exec node dist/server.js"]
