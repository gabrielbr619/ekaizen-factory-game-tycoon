# Deploy em VPS com Nginx existente

Este runbook publica o jogo em uma VPS que ja possui Docker, Docker Compose, DuckDNS, Certbot e um Nginx de borda em container.

Ele nao substitui o `docker-compose.yml` local. O fluxo local exigido pelo desafio continua sendo:

```bash
docker compose up --build
```

## Topologia de producao

- App dir: `/opt/factory-game-tycoon`
- Compose de producao: `docker-compose.prod.yml`
- Backend: `factory-game-tycoon-backend`, sem porta publica
- Frontend: `factory-game-tycoon-frontend`, sem porta publica direta
- Banco: SQLite persistido no volume Docker `factory-game-tycoon_data`
- Borda HTTPS: container Nginx existente `high-tide-systems-nginx`
- Rede de borda existente: `high-tide-systems-backend_app-network`
- Dominio sugerido: `factory-game-tycoon.duckdns.org`

## Preflight na VPS

```bash
docker --version
docker compose version
docker network inspect high-tide-systems-backend_app-network >/dev/null
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
df -h /
free -h
```

## DNS

No DuckDNS, criar/apontar o subdominio escolhido para o IP publico da VPS.

Exemplo atual da VPS inspecionada:

```txt
factory-game-tycoon.duckdns.org -> 69.62.103.249
```

Validar:

```bash
dig +short factory-game-tycoon.duckdns.org
```

## Publicar codigo

```bash
mkdir -p /opt/factory-game-tycoon
cd /opt/factory-game-tycoon

if [ ! -d .git ]; then
  git clone https://github.com/gabrielbr619/ekaizen-factory-game-tycoon.git .
else
  git fetch origin
  git checkout main
  git pull --ff-only origin main
fi
```

## Configurar ambiente

Criar o `.env` de producao sem imprimir segredo no terminal:

```bash
cd /opt/factory-game-tycoon
umask 077
printf 'SESSION_SECRET=' > .env
openssl rand -hex 32 >> .env
```

## Subir aplicacao

```bash
cd /opt/factory-game-tycoon
docker compose -f docker-compose.prod.yml --env-file .env config
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
docker compose -f docker-compose.prod.yml ps
```

Smoke interno:

```bash
docker exec factory-game-tycoon-frontend wget -qO- http://127.0.0.1/healthz
docker exec factory-game-tycoon-backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).read().decode())"
```

## HTTPS no Nginx existente

Emitir certificado usando o webroot ja montado no container de Nginx:

```bash
certbot certonly --webroot \
  -w /root/nginx/webroot \
  -d factory-game-tycoon.duckdns.org
```

Copiar o certificado para a pasta montada pelo container Nginx, sem imprimir o conteudo da chave:

```bash
install -d -m 700 /root/nginx/ssl/factory-game-tycoon
cp -L /etc/letsencrypt/live/factory-game-tycoon.duckdns.org/fullchain.pem /root/nginx/ssl/factory-game-tycoon/fullchain.pem
cp -L /etc/letsencrypt/live/factory-game-tycoon.duckdns.org/privkey.pem /root/nginx/ssl/factory-game-tycoon/privkey.pem
chmod 600 /root/nginx/ssl/factory-game-tycoon/privkey.pem
```

Instalar o server block:

```bash
cp /opt/factory-game-tycoon/deploy/nginx/factory-game-tycoon.duckdns.org.conf \
  /root/nginx/conf/factory-game-tycoon.duckdns.org.conf

docker exec high-tide-systems-nginx nginx -t
docker exec high-tide-systems-nginx nginx -s reload
```

Smoke publico:

```bash
curl -I https://factory-game-tycoon.duckdns.org
curl -fsS https://factory-game-tycoon.duckdns.org/healthz
```

## Renovacao de certificado

A renovacao do Certbot atualiza `/etc/letsencrypt/live/...`. Depois de renovar, repetir a copia para `/root/nginx/ssl/factory-game-tycoon` e recarregar o Nginx:

```bash
cp -L /etc/letsencrypt/live/factory-game-tycoon.duckdns.org/fullchain.pem /root/nginx/ssl/factory-game-tycoon/fullchain.pem
cp -L /etc/letsencrypt/live/factory-game-tycoon.duckdns.org/privkey.pem /root/nginx/ssl/factory-game-tycoon/privkey.pem
docker exec high-tide-systems-nginx nginx -t
docker exec high-tide-systems-nginx nginx -s reload
```

## Diagnostico rapido

```bash
cd /opt/factory-game-tycoon
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --since 30m backend
docker compose -f docker-compose.prod.yml logs --since 30m frontend
docker logs --since 30m high-tide-systems-nginx
docker exec high-tide-systems-nginx nginx -T | grep -n 'factory-game-tycoon'
```

## Rollback

Rollback de aplicacao para o commit anterior:

```bash
cd /opt/factory-game-tycoon
git log --oneline -5
git checkout <commit-anterior>
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

Rollback do proxy:

```bash
rm -f /root/nginx/conf/factory-game-tycoon.duckdns.org.conf
docker exec high-tide-systems-nginx nginx -t
docker exec high-tide-systems-nginx nginx -s reload
```

Parar somente a aplicacao do desafio sem remover o banco:

```bash
cd /opt/factory-game-tycoon
docker compose -f docker-compose.prod.yml down
```

Remover tambem a persistencia SQLite:

```bash
cd /opt/factory-game-tycoon
docker compose -f docker-compose.prod.yml down -v
```
