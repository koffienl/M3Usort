docker stop M3Usort
docker rm M3Usort

docker rmi m3usort
docker builder prune -a -f
docker build -t m3usort .

docker run --name M3Usort -d \
  -e IN_DOCKER=true \
  -p 6060:6060 \
  -v /docker/m3udata/config.py:/data/M3Usort/config.py \
  -v /docker/m3udata/logs:/data/M3Usort/logs/ \
  -v /docker/m3udata/files:/data/M3Usort/files/ \
  -v /docker/m3udata/Movies:/data/Movies/ \
  -v /docker/m3udata/Series:/data/Series/ \
  m3usort
