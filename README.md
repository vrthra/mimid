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
the following _md5_ checksum. (The commands in the host system are indicated by
leading `$` and the other lines indicate the expected output).

```bash
$ du -ksh mimid.box
2.6G  mimid.box

$ md5sum mimid.box 
f0999bdd1649d48ea8140c976da82404  mimid.box
```

#### Importing the box

The vagrant box can be imported as follows:

```bash
$ vagrant box add mimid ./mimid.box
==> box: Box file was not detected as metadata. Adding it directly...
==> box: Adding box 'mimid' (v0) for provider: 
    box: Unpacking necessary files from: file:///path/to/mimid/mimid.box
==> box: Successfully added box 'mimid' (v0) for 'virtualbox'!

$ vagrant init mimid
A `Vagrantfile` has been placed in this directory. You are now
ready to `vagrant up` your first virtual environment! Please read
the comments in the Vagrantfile as well as documentation on
`vagrantup.com` for more information on using Vagrant.

$ vagrant up

Bringing machine 'default' up with 'virtualbox' provider...
==> default: Importing base box 'mimid'...
==> default: Matching MAC address for NAT networking...
==> default: Setting the name of the VM: vtest_default_1591177746029_82328
==> default: Fixed port collision for 22 => 2222. Now on port 2200.
==> default: Clearing any previously set network interfaces...
==> default: Preparing network interfaces based on configuration...
    default: Adapter 1: nat
==> default: Forwarding ports...
    default: 8888 (guest) => 8888 (host) (adapter 1)
    default: 22 (guest) => 2200 (host) (adapter 1)
==> default: Running 'pre-boot' VM customizations...
==> default: Booting VM...
==> default: Waiting for machine to boot. This may take a few minutes...
    default: SSH address: 127.0.0.1:2200
    default: SSH username: vagrant
    default: SSH auth method: private key
==> default: Machine booted and ready!
==> default: Checking for guest additions in VM...
==> default: Mounting shared folders...
    default: /vagrant => /path/to/mimid
```

#### Verify Box Import

The commands inside the guest system are indicated by a `vm$ ` prefix. Any
time `vm$` is used, it means to either ssh into the vagrant box as below, or if
you are already in the VM, use the shell inside VM.

```bash
$ vagrant ssh

vm$ free -g
              total        used        free      shared  buff/cache   available
Mem:              9           0           9           0           0           9
Swap:             1           0           1
```

## A complete example

```bash
vm$ pwd
/home/vagrant
vm$ ls
mimid  start_c_tests.sh  startjupyter.sh  start_py_tests.sh  taints  toolchains
```

The following are the important files

| File/Directory      | Description |
-------------------------------
| startjupyter.sh              | The script to start Jupyter notebook to view examples.
| start_py_tests.sh            | Start the _Python_ experiments.
| start_c_tests.sh             | Start the _C_ experiments.
| taints/                      | The module to instrument C files.
| toolchains/                  | The original LLVM and Clang tool chain.
| mimid/src/                   | The main _mimid_ algorithm implementation.
| mimid/Cmimid                 | The modularized _mimid_ implementation (in Python) experiments in _C_.
| mimid/src/PymimidBook.ipynb  | The detailed _mimid_ notebook which also contains experiments in _Python_
| mimid/src/c_tables.py        | CLI for viewing the results from Python experiments.
| mimid/src/py_tables.py       | CLI for viewing the results from C experiments.

The most important file here is `mimid/src/PymimidBook.ipynb` which is the
Jupyter notebook that contains the complete algorithm explained and worked out
over two examples: one simple, and the other more complex. It can be
interactively explored using any of the Jupyter notebook viewers including
VSCode or directly using a browser as explained below.

It can also be viewed (read only) directly using the github link [here](https://github.com/vrthra/mimid/blob/master/src/PymimidBook.ipynb)

### Viewing the Jupyter notebook

From within your VM shell, do the following:

```bash
vm$ ./startjupyter.sh
...
     or http://127.0.0.1:8888/?token=ba5e5c480fe4a03d56c358b4a10d7172d2b19ff4537be55e
```

Copy and paste the last line in the host browser. The port `8888` is forwarded
to the host. Click the [src](http://127.0.0.1:8888/tree/src) link from the
browser and within that folder, click the [PymimidBook.ipynb](http://127.0.0.1:8888/notebooks/src/PymimidBook.ipynb)
link. This will let you see the complete set of examples as well as the
Python experiments in an already executed form.

You can either interactively explore the notebook by first clearing the
current values `Kernel>Restart & Clear Output` and executing each cell
one at a time, or by running all the experiments at once by
`Kernel>Restart & Run All`. Other options are also available from menu.


## Starting the experiments

There are two sets of experiments: The Python experiments
(`calc.py`, `mathexpr.py`, `cgidecode.py`, `urlparse.py`, `microjson.py`, `parseclisp.py`)
and the C experiments
(`json.c`, `tiny.c`, `mjs.c`).
We explain the _Python_ part first.

### Python experiments

**IMPORTANT** The system is **very memory intensive**. Hence, do not run the
experiments in parallel (e.g. concurrently from a different shell). If you
do that, you might get a _memory error_.

The following are the Python programs

| Program         | Input Language Kind | Description |
-------------------------------------------------
| `calc.py`       | Context Free        | A simple calculator program.             |
| `mathexpr.py`   | Context Free        | A more complex math expression program which supports functions. |
| `cgidecode.py`  | Regular             | A program to decode CGI encoded strings. |
| `urlparse.py`   | Regular             | A program to parse URLs.                 |
| `microjson.py`  | Context Free        | A program to parse JSON strings.         |
| `parseclisp.py` | Context Free        | A program to parse s-expressions.        |


There are two main ways to run the Python experiments. Either through the
Jupyter notebook as we explained earlier, or if you are on a headless system,
using the command line, which is explained below.

To start the Python experiments, execute the shell command below:

```bash
vm$ ./start_py_tests.sh
```

This will execute the Python experiments embedded in the Jupyter notebook
without requiring a browser, and produce an HTML file `PymimidBook.html`
in the `/home/vagrant` folder which may be viewed offline.

#### Result analysis for Python (CLI)

After running the python experiments using *command line*, the results can be
inspected using the following command line. Note that running it through
Jupyter notebook interface will not produce the `PymimidBook.html` file which
is required for using `py_tables.py`. In that case, please view the results
directly in the notebook `Results` section.

```bash
vm$ python3 ./mimid/src/py_tables.py
Precision (Table 1)     Mimid
-----------------
calc.py
mathexpr.py
cgidecode.py
urlparse.py
microjson.py
parseclisp.py

Recall (Table 2)        Mimid
-----------------
calc.py
mathexpr.py
cgidecode.py
urlparse.py
microjson.py
parseclisp.py
```

### C experiments

The C experiments are not accessible from the Jupyter notebook as it requires
instrumenting the C programs. Further, the set of C programs is intended as
a demonstration of how to use the _mimid_ algorithm in a standalone fashion.

The C experiments are in the directory `mimid/Cmimid`, and the modularized
_mimid_ implementation (in Python) is available under `mimid/Cmimid/src`.

To start the C experiments, execute the shell command below:

```bash
vm$ ./start_c_tests.sh
```

This will execute all the C experiments, and produce results which can be
analyzed as below:

#### Result analysis for C

Note that for `C` there is not `Autogram` implementation available, and hence,
we have nothing to compare against. Hence, the precision and recall is provided
as is. The following command line produces the results (table names are in
correspondence with the paper).

```bash
vm$ python3 ./mimid/src/c_tables.py
Precision (Table 1)     Mimid
-----------------
mjs     97.5%
tiny    92.8%
json    83.8%

Recall (Table 2)        Mimid
-----------------
mjs     90.5%
json    100.0%
tiny    100.0%
```

As before, what this means is that the grammar inferred by `mimid` for `mjs`
(for example) can generate inputs such that 97.5% of such inputs were
accepted by `mjs` (Table 1). Similarly, if one generates valid Javascript
strings, then 90.5% of such inputs would be parsed correctly by a parser
that uses the grammar mined by `mimid` from `mjs` (Table 2).

## How is the algorithm organized

The Jupyter notebook provided has one to one correspondence with the
procedure names in the paper. Each method is thoroughly documented,
and executions of methods can be performed to verify their behavior.

## How to interpret the results

TODO

## How to add a new subject

TODO
