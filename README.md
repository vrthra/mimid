# Replication package for _Mining Input Grammars From Dynamic Control Flow_

Our submission is a tool that implements the algorithm given in the paper _Mining Input Grammars From Dynamic Control Flow_.
We provide a file `artifact.tar.gz` which contains the code to reproduce our
results. The `artifact.tar.gz` contains [src/PymimidBook.ipynb](https://github.com/vrthra/mimid/blob/master/src/PymimidBook.ipynb) which contains the
complete algorithm explained and worked out in one simple example in a [Jupyter notebook](https://jupyter.org/).
It also contains all the Python experiments. It can be viewed through
either the virtual box as explained below, or can be directly viewed using any
of the Jupyter notebook viewers including VSCode, or github ([from this link](https://github.com/vrthra/mimid/blob/master/src/PymimidBook.ipynb)).

## Prerequisites

### RAM

All experiments done on a base system with 15 GB RAM.

### Software

**IMPORTANT** All executables are compiled and linked in the following vagrant
box, with 8 GB RAM allocated. While it can be done on the base system itself,
it is recommended that the user simply use the vagrant box directly. See the
`Vagrantfile` for configuration.

```bash
$ vagrant up --provision
```

To connect

```
$ vagrant ssh
```

The vagrant box had the following operating system.

```bash
$ uname -rvmpio
4.15.0-70-generic #79-Ubuntu SMP Tue Nov 12 10:36:11 UTC 2019 x86_64 x86_64 x86_64 GNU/Linux

$ lsb_release -d
Description:	Ubuntu 18.04.3 LTS
```

#### Python

The algorithm implementation was evaluated using Python version 3.6.8

```bash
$ python3 --version
Python 3.6.8
```

## Viewing the Jupyter notebook

To view the Jupyter notebook, connect to the vagrant image

```
$ vagrant ssh
```

and inside the virtual machine, execute this command

```
vm$ ./startjupyter.sh
...
     or http://127.0.0.1:8888/?token=b7c576c237db3c7aec4e9ac30b69ef1ed6a4fb32b623c93a
```

Copy and paste the last line in your host browser. The port `8888` is forwarded
to the host. Click the [src](http://127.0.0.1:8888/tree/src) link, and within
that folder, click the [PymimidBook.ipynb](http://127.0.0.1:8888/notebooks/src/PymimidBook.ipynb)
link. This will let you see the complete example already executed. You can
restart execution by clicking on Kernel>Restart&Run All or simply clear output
and run one box at a time.

## Experiments

First login to the virtual machine

```bash
$ vagrant ssh
```

Next, change directory to `mimid`

```bash
vm$ cd mimid
vm$ pwd
/home/vagrant/mimid
```

### Starting the experiments

The experiments can be started with the following command:

```bash
$ make all
```

The above command executes _all_ experiments. If needed, individual
experiments can be done with:

TODO

## Result analysis

TODO
## How is the algorithm organized

The Jupyter notebook provided has one to one correspondence with the
procedure names in the paper. Each method is thoroughly documented,
and executions of methods can be performed to verify their behavior.

## How to interpret the results

TODO

## How to add a new subject

TODO
