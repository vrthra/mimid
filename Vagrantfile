# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "generic/ubuntu1804"
  config.vm.box_check_update = false
  # config.vm.network "private_network", ip: "192.168.10.50"
  config.vm.network "forwarded_port", guest: 8888, host: 8888

  # we do not want a synced folder other than the default.
  # we will be extracting the tarred up mimid to home.
  config.vm.synced_folder "./mimid", "/vagrant/mimid"

  config.vm.provider "virtualbox" do |v|
    v.memory = 10240
    v.cpus = 2
  end

  # apt-get -y install openjdk-11-jre-headless make docker.io graphviz python3-venv python3-pip libjson-c-dev
  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get -y install openjdk-11-jdk-headless make graphviz python3.7 python3-venv python3-pip ninja-build cmake subversion pkg-config  llvm-4.0 llvm-4.0-dev zlib1g-dev python3-software-properties python3-apt libclang-8-dev clang-format-8 clang-8 clang-4.0
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 2
    pip3 install wheel
    pip3 install graphviz
    pip3 install jupyter
    pip3 install pudb
    pip3 install astor
    pip3 install clang
    pip3 install fuzzingbook
    pip3 install meson==0.46.1

    cp /vagrant/mimid/src/Parser.py /usr/local/lib/python3.7/dist-packages/fuzzingbook/Parser.py
    cp /vagrant/mimid/src/GrammarMiner.py /usr/local/lib/python3.7/dist-packages/fuzzingbook/GrammarMiner.py
    pip3 install jupyter_contrib_nbextensions
    pip3 install jupyter_nbextensions_configurator
    jupyter contrib nbextension install --sys-prefix
    jupyter nbextension enable toc2/main --sys-prefix

    echo cd /home/vagrant/mimid >  /home/vagrant/startjupyter.sh
    echo jupyter notebook --ip 0.0.0.0 --port 8888 >> /home/vagrant/startjupyter.sh
    chmod +x /home/vagrant/startjupyter.sh

    echo cd /home/vagrant/mimid >  /home/vagrant/start_py_tests.sh
    echo jupyter nbconvert --to notebook --execute src/PymimidBook.ipynb --ExecutePreprocessor.timeout=36000 --output=PymimidBook_.ipynb >>  /home/vagrant/start_py_tests.sh
    echo jupyter nbconvert --to html src/PymimidBook_.ipynb --output=~/PymimidBook.html >>  /home/vagrant/start_py_tests.sh
    echo python3 src/py_tables.py >>  /home/vagrant/start_py_tests.sh
    chmod +x /home/vagrant/start_py_tests.sh

    echo cd /home/vagrant/mimid/Cmimid >  /home/vagrant/start_c_tests.sh
    echo make precision fuzz >>  /home/vagrant/start_c_tests.sh
    echo python3 src/c_tables.py >>  /home/vagrant/start_c_tests.sh
    chmod +x /home/vagrant/start_c_tests.sh
  SHELL
end
