# Projet-M207
SDN infrastructure with ONOS, Kubernetes cluster via kubeadm, and GLPI monitoring. Deployment of HTTPS, MySQL, and Samba services in Kubernetes, with dynamic network management and inventory via FusionInventory.

## Getting docker images

1. Install docker:

https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository

2. Install [Contairnet decker image](https://hub.docker.com/r/onosproject/onos), from docker hub:

```bash
docker pull containernet/containernet
```

3. Install [ONOS docker image](https://hub.docker.com/r/containernet/containernet), from docker hub:

```bash
docker pull onosproject/onos
```

## Executing the infrastructure
After the images are pulled, and build you can launch your emulated data-plane and onos controller. To do so, the best way is to create a docker-compose file. Create a file called docker-compose.yml with the following contents (or download it from the repository)

```bash
version: '3.3'

services:
  onos:
    image: onosproject/onos:latest
    restart: always
    ports:
      - "8181:8181"
      - "6633:6633"
      - "6653:6653"
    container_name: onos

  containernet: 
    depends_on: 
      - onos
    image: containernet/containernet:v1
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"      
    privileged: true
    pid: host
    tty: true
    container_name: containernet
```

After that, execute the docker composition with:

```bash
docker compose up
```

"open a new terminal"

After a while, both images will be up and running. Log into the Containernet container by executing:

```bash
docker exec -it containernet bash
```

## Configuring SDN components

"open a new terminal"

Connect to the ONOS controller by executing:

```bash
docker exec -it onos bash
```

