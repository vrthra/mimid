# Replication package for _Mining Input Grammars From Dynamic Control Flow_

**IMPORTANT** This package is hosted at Github [in this repository](https://github.com/vrthra/mimid).

Our submission is a tool that implements the algorithm given in the paper
_Mining Input Grammars From Dynamic Control Flow_.
We provide the virtual machine [mimid](https://drive.google.com/open?id=1-v4v6Sz4IB-xpF9tmz1TaqMUPkP-2Fs7)
(hosted on google drive) which contains the complete artifacts necessary to
reproduce our experiments. We describe the process of invoking the virtual
machine below.

We also note that if you are unable to download the vagrant box (It is 3 GB)
You can also take a look at the complete worked out example of how to derive
grammar for an example program at [src/PymimidBook.ipynb](https://github.com/vrthra/mimid/blob/master/src/PymimidBook.ipynb)

The [src/PymimidBook.ipynb](https://github.com/vrthra/mimid/blob/master/src/PymimidBook.ipynb)
notebook also contains all the Python experiments. It can be viewed through
either using the virtual box as explained below, or can be directly viewed using
any of the Jupyter notebook viewers including VSCode, or Github ([from this link](https://github.com/vrthra/mimid/blob/master/src/PymimidBook.ipynb))
(This is a [Jupyter notebook](https://jupyter.org) hosted at Github. Click to view an non-interactive version. If the load fails, click reload until you can view it).

## Prerequisites

### RAM

All experiments done on a base system with **15 GB RAM**, and the VM was
allocated **10 GB RAM**.

### Setup

First, please make sure that the port 8888 is not in use. Our VM forwards its
local port 8888 to the host machine.

#### Download

Next, please download the vagrant box from the following link:

https://drive.google.com/open?id=1-v4v6Sz4IB-xpF9tmz1TaqMUPkP-2Fs7

Unfortunately, due to the way google drive works, you need to navigate to that
link using the browser and click on the file. There is no fail-safe command-line.

This produces a file called `mimid.box` which is 3 GB in size, and should have
the following _md5_ checksum.

```
$ md5sum mimid.box 
f0999bdd1649d48ea8140c976da82404  mimid.box
```



### Software

**IMPORTANT** All executables are compiled and linked in the following vagrant
box, with 10 GB RAM allocated.

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
