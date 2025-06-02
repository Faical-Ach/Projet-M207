# Projet-M207
SDN infrastructure with ONOS, Kubernetes cluster via kubeadm, and GLPI monitoring. Deployment of HTTPS, MySQL, and Samba services in Kubernetes, with dynamic network management and inventory via FusionInventory.

## Getting docker images

1• Install docker:

https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository

2• Install [Contairnet decker image](https://hub.docker.com/r/containernet/containernet), from docker hub:

```bash
docker pull containernet/containernet
```

3• Install [ONOS docker image](https://hub.docker.com/r/onosproject/onos), from docker hub:

```bash
docker pull onosproject/onos
```

# After cloning the repository with 'git clone', navigate into the project directory:

```bash
cd Projet-M207
```

4• Create a Docker ubuntu gateway to allow access to the internet and other networks:

We need to creat first *dockerfile*

```bash
FROM ubuntu:xenial

RUN apt-get update && apt-get install -y \
    iproute2 \
    net-tools \
    iputils-ping \
    iptables \
    dnsutils \
    curl \
    tcpdump \
    vim \
    python && \
    apt-get clean
```

Then we will build it

```bash
docker build -t gateway .
```

## Executing the infrastructure
After the images are pulled and the build process is complete, you can launch your emulated data-plane and ONOS controller.

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

execute the Onos Command Line Interface (CLI) or client console by executing:

```bash
./apache-karaf-4.2.14/bin/client
```

Make sure the output contains the Onos GUI. Now, you can go to your Onos GUI using your browser and going to the address localhost:8181/onos/ui/. The default username / password is onos/rocks. Check the GUI and explore the main menu (bars at the left upper corner).

Go to the main menu -> Applications. Enable the following applications (select and hit the play button near the upper right corner):

• OpenFlow Base Provider (org.onosproject.openflow-base)

• Proxy ARP/NDP (org.onosproject.proxyarp), just to avoid taking care of ARP ourselves :)

• LLDP Link Provider (org.onosproject.lldpprovider)

• Host Location Provider (org.onosproject.hostprovider)

## Kubernetes Cluster Setup: Master & Worker Nodes

Folow this configuration step by step:

### For both master and worker nodes:
```bash
# Disable swap
sudo swapoff -a
# Permanently disable swap by commenting out swap entries in /etc/fstab

# Load necessary kernel modules
sudo modprobe overlay
sudo modprobe br_netfilter

# Set sysctl params required by Kubernetes
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.ipv4.ip_forward                 = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF

sudo sysctl --system

# Install container runtime (Docker example)
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable --now docker

# Add Kubernetes apt repo
sudo apt update && sudo apt install -y apt-transport-https curl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

cat <<EOF | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF

sudo apt update

# Install kubeadm, kubelet, kubectl
sudo apt install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

# Enable kubelet service
sudo systemctl enable --now kubelet
```

### Initialize Master Node (on Master only):

```bash
sudo kubeadm init --pod-network-cidr=192.168.0.0/16
```

After initialization, copy the kubeconfig file to use kubectl:

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

Install Pod Network:

```bash
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
```
Do not run this on Worker Nodes — Master Node only

### Join Worker Node:

After excute master node should be give you this:
```bash
kubeadm join <master-ip>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```

Then, Verify Cluster (on Master):
```bash
kubectl get nodes
```

You should be see :
```bash
root@master:~$ kubectl get nodes
NAME     STATUS   ROLES           AGE   VERSION
master   Ready    control-plane   18m   v1.28.15
worker    Ready    <none>          40h   v1.28.15
```

## Creat Services (HTTP,SAMBA,MYSQL):

```bash
nano services-on-master.yaml
```

1• Set this confige: 
```bash
apiVersion: v1
kind: Pod
metadata:
  name: web-server-pod
  labels:
    app: web-server
spec:
  nodeName: wnode
  containers:
  - name: web-server
    image: ubuntu
    command: ["/bin/bash", "-c"]
    args:
      - |
        apt-get update && \
        DEBIAN_FRONTEND=noninteractive apt-get install -y apache2 && \
        apache2ctl -D FOREGROUND
    ports:
    - containerPort: 80
      hostPort: 80
---
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: mysql
  name: mysql-pod
spec:
  nodeName: wnode
  containers:
  - name: mysql
    image: mysql:8.0
    env:
      - name: MYSQL_ROOT_PASSWORD
        value: "Root"  # It's a good practice to wrap values in quotes
    ports:
      - containerPort: 3306
        # hostPort is generally not recommended for Pods; use a Service instead
        hostPort: 30306
    resources:
      requests:
        memory: "512Mi"
        cpu: "500m"
      limits:
        memory: "1Gi"
        cpu: "1"
---
apiVersion: v1
kind: Pod
metadata:
  name: samba-pod
  labels:
    app: samba
spec:
  nodeName: wnode
  hostNetwork: true
  containers:
  - name: samba
    image: dperson/samba
    args:
      - "-u"
      - "smbuser;Root"
      - "-s"
      - "shared;/shared;yes;no;no;smbuser"
    ports:
      - containerPort: 445
    volumeMounts:
      - mountPath: /shared
        name: samba-data
  volumes:
    - name: samba-data
      hostPath:
        path: /srv/samba/shared
        type: DirectoryOrCreate

```

2• Create File web-server-service.yaml
we use this service to redirect trafic to my web-server-pod also 
allow me to use port 80 instead of node port 30080

```bash
nano web-server-service.yaml
```

Then:
```bash
apiVersion: v1
kind: Service
metadata:
  name: web-server-service
spec:
  selector:
    app: web-server
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: NodePort

```

3• We Will create mysql-service.yaml also :

```bash
nano mysql-service.yaml
```

Then:
```bash
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
spec:
  type: NodePort
  selector:
    app: mysql
  ports:
    - port: 3306
      targetPort: 3306
      nodePort: 30306  # 30000–32767
```

