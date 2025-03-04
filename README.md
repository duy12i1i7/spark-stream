
# Mục tiêu

Trong bài viết này mình sẽ cài đặt Hadoop bản mới nhất (3.3.4 vào thời điểm viết bài này) trên 3 node Ubuntu 20.04 và OpenJdk11. Để thuận tiện cho việc setup và thử nghiệm, mình sẽ sử dụng Docker để giả lập 3 node này.

# Cài đặt môi trường

## Tạo Network trên Docker

Đầu tiên, tạo một bridge network mới trên Docker (Nếu chưa cài Docker, các bạn xem hướng dẫn cài đặt tại [đây](#)):

```bash
docker network create hadoop
```

## Tạo Container trên Image Ubuntu 20.04

```bash
docker run -it --name node01 -p 9870:9870 -p 8088:8088 -p 19888:19888 --hostname node01 --network hadoop ubuntu:20.04
```

> **Lưu ý:** Mình đang sử dụng MacOS nên cần binding port từ container ra máy host. Bạn không cần làm điều này nếu sử dụng Linux hoặc Windows.

## Cài đặt Các Package Cần Thiết

```bash
apt update
apt install -y wget tar ssh default-jdk
```

## Tạo User Hadoop

```bash
groupadd hadoop
useradd -g hadoop -m -s /bin/bash hdfs
useradd -g hadoop -m -s /bin/bash yarn
useradd -g hadoop -m -s /bin/bash mapred
```

> Vì lý do bảo mật, Hadoop khuyến nghị mỗi dịch vụ nên chạy trên một user khác nhau, xem chi tiết tại [đây](#).

## Tạo SSH-Key Trên Mỗi User

```bash
su <username>
ssh-keygen -m PEM -P '' -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 0600 ~/.ssh/authorized_keys
```

## Khởi Động SSH Service

```bash
service ssh start
```

## Thêm Hostname Vào File `/etc/hosts`

Thêm dòng sau vào file `/etc/hosts`:

```
172.20.0.2      node01
```

> **Lưu ý:** `172.20.0.2` là IP của container trên máy của mình, bạn hãy thay bằng IP máy của bạn.

## Kiểm Tra Kết Nối SSH

```bash
ssh <username>@node01
```

# Download Hadoop Và Cấu Hình

## Download Và Cài Đặt Hadoop

Lên trang chủ download của Hadoop để lấy link tải bản mới nhất, sau đó thực hiện:

```bash
wget https://dlcdn.apache.org/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz
tar -xvzf hadoop-3.3.4.tar.gz
mv hadoop-3.3.4 /lib/hadoop
mkdir /lib/hadoop/logs
chgrp hadoop -R /lib/hadoop
chmod g+w -R /lib/hadoop
```

## Cấu Hình Biến Môi Trường

Thêm các biến môi trường vào file `/etc/bash.bashrc` để tất cả các user trên hệ thống đều có thể sử dụng:

```bash
export JAVA_HOME=/usr/lib/jvm/default-java
export HADOOP_HOME=/lib/hadoop
export PATH=$PATH:$HADOOP_HOME/bin

export HDFS_NAMENODE_USER="hdfs"
export HDFS_DATANODE_USER="hdfs"
export HDFS_SECONDARYNAMENODE_USER="hdfs"
export YARN_RESOURCEMANAGER_USER="yarn"
export YARN_NODEMANAGER_USER="yarn"

export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
```

Cập nhật biến môi trường:

```bash
source /etc/bash.bashrc
```

Cũng cần cập nhật biến môi trường trong file `$HADOOP_HOME/etc/hadoop/hadoop-env.sh`:

```bash
export JAVA_HOME=/usr/lib/jvm/default-java
```

## Thiết Lập Cấu Hình Cho Hadoop

### Cấu Hình `core-site.xml`

Mở file `$HADOOP_HOME/etc/hadoop/core-site.xml` và thêm nội dung sau (xem full cấu hình tại [đây](#)):

```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://node01:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/home/${user.name}/hadoop</value>
    </property>
</configuration>
```

> `/home/${user.name}/hadoop` là thư mục lưu dữ liệu trên HDFS, bạn có thể thay đổi nếu muốn.

### Cấu Hình `hdfs-site.xml`

Mở file `$HADOOP_HOME/etc/hadoop/hdfs-site.xml` và thêm nội dung sau (xem full cấu hình tại [đây](#)):

```xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.permissions.superusergroup</name>
        <value>hadoop</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir.perm</name>
        <value>774</value>
    </property>
</configuration>
```

> **Chú thích:** Cấu hình `dfs.replication` thiết lập số bản sao thực tế được lưu trữ đối với dữ liệu trên HDFS.

### Cấu Hình `yarn-site.xml`

Mở file `$HADOOP_HOME/etc/hadoop/yarn-site.xml` và thêm nội dung sau (xem full cấu hình tại [đây](#)):

```xml
<configuration>
    <property>
        <name>yarn.resourcemanager.hostname</name>
        <value>node01</value>
    </property>
    <property>
        <name>yarn.nodemanager.resource.memory-mb</name>
        <value>-1</value>
    </property>
    <property>
        <name>yarn.nodemanager.resource.detect-hardware-capabilities</name>
        <value>true</value>
    </property>
</configuration>
```

# Chạy Hadoop Trên 1 Node

## Format File Trên Name Node

```bash
su hdfs
$HADOOP_HOME/bin/hdfs namenode -format
exit
```

## Khởi Động Các Dịch Vụ Hadoop (Chạy Dưới Account Root)

```bash
$HADOOP_HOME/sbin/start-all.sh
```

```markdown
# Thêm Node Mới Vào Cụm

Để thêm một node mới vào cụm, trên node đó cũng thực hiện đầy đủ các bước đã nêu ở trên. Do sử dụng Docker, mình sẽ tạo một image từ container hiện có.

## Tạo Image Từ Container Hiện Có

```bash
docker commit node01 hadoop
```

## Chạy Container Mới Từ Image Đã Tạo

```bash
docker run -it --name node02 --hostname node02 --network hadoop hadoop
```

## Trên Node02: Khởi Động SSH và Xoá Thư Mục Data Cũ

```bash
service ssh start
rm -rf /home/hdfs/hadoop
rm -rf /home/yarn/hadoop
```

## Cập Nhật IP và Hostname

### Trên Node02

Mở file `/etc/hosts` và thêm:

```
172.20.0.3      node02
172.20.0.2      node01
```

### Trên Node01

Bổ sung thêm IP và hostname của node02 trong file `/etc/hosts`:

```
172.20.0.2      node01
172.20.0.3      node02
```

### Cập Nhật File Workers

Mở file `$HADOOP_HOME/etc/hadoop/workers` và cập nhật nội dung:

```
node01
node02
```

## Khởi Động Các Dịch Vụ Hadoop Trên Node01

```bash
$HADOOP_HOME/sbin/start-all.sh
```
```markdown
# Hướng Dẫn Sử Dụng Cơ Bản

## Khởi Động Các Dịch Vụ Hadoop

Để start tất cả các dịch vụ trong cụm Hadoop, hãy vào master node (trong bài này là `node01`) sử dụng account `root`:

```bash
$HADOOP_HOME/sbin/start-all.sh
```

> **Lưu ý:**  
> - Master node cần có IP và hostname của tất cả các slave node trong file `/etc/hosts`.  
> - Mỗi account `hdfs`, `yarn`, `mapred` của master node đều phải có thể SSH đến account tương ứng trên các slave node.  
> - Mỗi slave node phải có thể kết nối đến master node thông qua hostname.

## Tắt Các Dịch Vụ Hadoop

Để tắt tất cả các dịch vụ của cụm Hadoop, thực hiện lệnh sau:

```bash
$HADOOP_HOME/sbin/stop-all.sh
```
```markdown
# Cài đặt Spark

Bạn lên trang chủ của Spark tại [đây](#) để lấy link download. Vào thời điểm viết bài này phiên bản Spark mới nhất là **3.3.4**, tuy nhiên khi thử nghiệm mình thấy phiên bản này không tương thích với DBT và Hive nên mình sử dụng phiên bản Spark thấp hơn là **3.3.2**.

> **Lưu ý:**  
> Vì đã có sẵn cụm Hadoop rồi (bạn xem lại [hướng dẫn tại đây](#)) nên chúng ta chỉ cần cài Spark trên 1 node (mình cài trên node01). Khi chạy job Spark, cấu hình `--master yarn` sẽ giúp job được chạy trên tất cả các node.

## Tải Và Cài Đặt Spark

```bash
wget https://archive.apache.org/dist/spark/spark-3.3.2/spark-3.3.2-bin-hadoop3.tgz
tar -xzvf spark-3.3.2-bin-hadoop3.tgz
mv spark-3.3.2-bin-hadoop3 /lib/spark
mkdir /lib/spark/logs
chgrp hadoop -R /lib/spark
chmod g+w -R /lib/spark
```

## Cấu Hình Biến Môi Trường

Thêm các biến môi trường sau vào file `/etc/bash.bashrc`:

```bash
export SPARK_HOME=/lib/spark
export PATH=$PATH:$SPARK_HOME/bin
```

Cập nhật biến môi trường:

```bash
source /etc/bash.bashrc
```

## Cấu Hình Spark

Tạo file cấu hình `spark-env.sh`:

```bash
cp $SPARK_HOME/conf/spark-env.sh.template $SPARK_HOME/conf/spark-env.sh
```

Thêm cấu hình classpath vào file `$SPARK_HOME/conf/spark-env.sh`:

```bash
export SPARK_DIST_CLASSPATH=$(hadoop classpath)
```

## Kiểm Tra Chạy Spark Ở YARN Mode

```bash
spark-shell --master yarn --deploy-mode client
```

### Kết Quả Mong Đợi

```plaintext
Welcome to
      ____              __
     / __/__  ___ _____/ /__
    _\ \/ _ \/ _ `/ __/  '_/
   /___/ .__/\_,_/_/ /_/\_\   version 3.3.2
      /_/
         
Using Scala version 2.12.10 (OpenJDK 64-Bit Server VM, Java 11.0.17)
scala>
```
```
