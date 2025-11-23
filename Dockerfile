FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Create uploads directory and set permissions
RUN mkdir -p public/uploads && chown -R node:node /app

# Switch to non-root user
USER node

EXPOSE 3000

CMD ["node", "server.js"]
