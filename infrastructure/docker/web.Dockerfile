FROM node:22-alpine

WORKDIR /app

COPY package.json /app/package.json
COPY apps/web/package.json /app/apps/web/package.json
COPY packages/schemas/package.json /app/packages/schemas/package.json

RUN npm install

COPY apps/web /app/apps/web
COPY packages/schemas /app/packages/schemas

WORKDIR /app/apps/web

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
