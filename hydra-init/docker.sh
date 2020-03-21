VERSION=1.5
docker build -t hengel2810/se09-hydra-init:$VERSION .
docker push hengel2810/se09-hydra-init:$VERSION

#docker run \
#  -e HYDRA_HOST="http://localhost" \
#  -e HYDRA_PORT="4445" \
#  hengel2810/se09-hydra-init:$VERSION
