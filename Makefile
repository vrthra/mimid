python=python3

clean: ; rm -rf *.log
clobber: clean;
	-$(MAKE) box-remove
	-rm -rf artifact artifact.tar.gz
	-rm -rf .db
results:; mkdir -p results

artifact.tar.gz: Vagrantfile Makefile
	rm -rf artifact && mkdir -p artifact/mimid
	cp README.md artifact/README.txt
	cp -r README.md src Cmimid Makefile Vagrantfile taints.tar.gz etc/setup_llvm_clang.sh  etc/json-c-0.13.1-20180305.tar.gz artifact/mimid
	cp -r etc/json.tar.gz etc/py_tables.py etc/c_tables.py artifact/mimid/src
	cp -r Vagrantfile artifact/
	tar -cf artifact1.tar artifact
	gzip artifact1.tar
	mv artifact1.tar.gz artifact.tar.gz

ARTIFACT=artifact.tar.gz

# PACKAGING
# https://github.com/json-c/json-c/archive/json-c-0.13.1-20180305.tar.gz
box-create: mimid.box
mimid.box: $(ARTIFACT)
	cd artifact && vagrant up
	cd artifact && vagrant ssh -c 'cd /vagrant; tar -cpf ~/mimid.tar mimid/Cmimid mimid/src mimid/Makefile mimid/README.md; cd ~/; tar -xpf ~/mimid.tar; rm -f ~/mimid.tar'
	cd artifact && vagrant ssh -c 'cd ~/ && zcat /vagrant/mimid/taints.tar.gz | tar -xpf -'
	cd artifact && vagrant ssh -c 'cd ~/ && echo export PATH="/usr/local/opt/llvm@4/bin:/usr/local/bin:$$PATH" > ~/.init.sh'
	cat toolchains.tar.gz.1 toolchains.tar.gz.2 > artifact/mimid/toolchains.tar.gz
	cd artifact && vagrant ssh -c 'cd ~/taints/ && cp /vagrant/mimid/setup_llvm_clang.sh ./scripts/ && ./scripts/setup_llvm_clang.sh'
	# cp artifact/mimid/toolchain.tar.gz .
	cd artifact && vagrant ssh -c 'zcat /vagrant/mimid/json-c-0.13.1-20180305.tar.gz | tar -xvpf -'
	cd artifact && vagrant ssh -c 'cd /home/vagrant/json-c-json-c-0.13.1-20180305 && ./configure --prefix=/usr && make'
	cd artifact && vagrant ssh -c 'cd /home/vagrant/json-c-json-c-0.13.1-20180305 && sudo make install'
	cd artifact && vagrant ssh -c 'cd /home/vagrant/ && rm -rf json-c-json-c-0.13.1-20180305'
	cd artifact && vagrant ssh -c 'cd ~/taints/ && source ~/.init.sh && meson build/debug --prefix="$$(pwd)/install"'
	cd artifact && vagrant ssh -c 'cd ~/taints/ && source ~/.init.sh && ninja -C build/debug install'
	cd artifact && vagrant package --output ../mimid1.box --vagrantfile ../Vagrantfile.new
	mv mimid1.box mimid.box

box-hash:
	md5sum mimid.box

box-add: | mimid.box
	-vagrant destroy $$(vagrant global-status | grep mimid | sed -e 's# .*##g')
	rm -rf vtest && mkdir -p vtest && cp mimid.box vtest
	cd vtest && vagrant box add mimid ./mimid.box
	cd vtest && vagrant init mimid
	cd vtest && vagrant up

box-status:
	vagrant global-status | grep mimid
	vagrant box list | grep mimid

box-remove:
	-vagrant destroy $$(vagrant global-status | grep mimid | sed -e 's# .*##g')
	vagrant box remove mimid

show-ports:
	 sudo netstat -ln --program | grep 8888

box-connect1:
	cd artifact; vagrant ssh
box-connect2:
	cd vtest; vagrant ssh

REMOTE=anonymous-fse2020:
REMOTE=mimid-fse2020:

rupload:
	rm -rf mimid.fse2020 && mkdir -p mimid.fse2020
	cp mimid.box mimid.fse2020
	rclone --contimeout=24h -v copy mimid.fse2020 $(REMOTE)fse2020/

rls:
	rclone ls $(REMOTE)

rrm:
	rclone delete $(REMOTE)fse2020/mimid.box

rlink:
	rclone link $(REMOTE)fse2020/

rsync:
	rsync -avz  --partial-dir=.rsync-partial --progress --rsh="ssh" mimid.box shuttle:/scratch/rahul/vm/
