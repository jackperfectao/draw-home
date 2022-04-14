cd $(dirname "$0")
scp -r cert $1:/home/admin/
scp nginx.rpm $1:~/
ssh $1 rpm -ivh nginx.rpm
ssh $1 mkdir -p /home/admin/nginx/conf/extra/
scp nginx.conf $1:/home/admin/nginx/conf/
ssh $1 service nginx start
