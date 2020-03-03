VERSION=0.27
docker build -t hengel2810/se09-vault-init:$VERSION .
docker push hengel2810/se09-vault-init:$VERSION

#docker run \
#  -e POSTGRES_HOST="se09-cluster-do-user-5039378-0.a.db.ondigitalocean.com" \
#  -e POSTGRES_PORT=25060 \
#  -e POSTGRES_USER="vault" \
#  -e POSTGRES_PASSWORD="f6nav8y15rrgw9uh" \
#  -e POSTGRES_DB_NAME="vault" \
#  hengel2810/se09-vault-init

#  -e POSTGRES_HOST=localhost \
#  -e POSTGRES_PORT=5432 \
#  -e POSTGRES_USER=postgres \
#  -e POSTGRES_PASSWORD=postgres \
#  -e POSTGRES_DB_NAME=test \