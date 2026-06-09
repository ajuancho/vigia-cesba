FROM node:20-alpine AS base
WORKDIR /app

FROM base AS deps
COPY apps/web/package.json ./
RUN npm install --no-audit --no-fund

FROM base AS build
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web/. ./
RUN npm run build

FROM base AS run
ENV NODE_ENV=production
COPY --from=build /app ./
EXPOSE 3000
CMD ["npm", "run", "start"]
