# Use official Node.js base image
FROM node:14

# Create app directory
WORKDIR /usr/src/app

# Install app dependencies
COPY package.json package-lock.json ./
RUN npm install

# Bundle app source
COPY . .

# Expose port
EXPOSE 3000 8080

# Run the app
CMD ["npm", "start"]
