FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Create uploads directory
RUN mkdir -p public/uploads

EXPOSE 3000

CMD ["node", "server.js"]
