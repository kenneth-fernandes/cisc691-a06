FROM mongo:6.0-jammy

COPY init-mongo.js /docker-entrypoint-initdb.d/

CMD ["mongod", "--auth"]