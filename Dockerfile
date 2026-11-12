FROM node:22-bookworm-slim

WORKDIR /app

COPY sprint-health-web/server/package.json sprint-health-web/server/package-lock.json ./
RUN npm ci --omit=dev

COPY sprint-health-web/server/src ./src

ENV PORT=3001
EXPOSE 3001

CMD ["node", "src/index.js"]
