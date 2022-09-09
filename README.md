# Randomized Multi-DAG Task Generator for Scheduling and Allocation Research

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![License](http://img.shields.io/:license-mit-blue.svg)](http://badges.mit-license.org)

**dag-gen-rnd** --- A randomized multiple Direct Acyclic Graph (DAG) task generator designed for scheduling and allocation research in parallel and multi-core computing. 

**dag-gen-rnd** supports both command line (`daggen-cli`) and graphical user interface (`daggen-gui`; in development). This generator can be easily configured through a `.json` file and is highly extensible for other purposes.

Supported generation algorithms:

- `nfj`: Nested fork-join
- `rnd`: standard randomized DAG (layer-by-layer)
- `rnd_legacy`: default randomized DAG

The utilization generation is based on:

- UUnifast
- UUnifast-discard

---

## Requirements

- `Python >= 3.7`
- `NetworkX >= 2.4`
- `Matplotlib >= 3.1.3`
- `pygraphviz >= 1.5`
- `numpy >= 1.17`
- `tqdm >= 4.45.0`
- `pyqt5` (optional for GUI)

---

## Installation on Linux

Install dependencies using apt:

`$ sudo apt install python3-dev graphviz libgraphviz-dev pkg-config xdot`

Execute these commands to create a python virtual environment:

```
$> pip3 install env
$> python3 -m venv env
$> source env/bin/activate
$> python3 -m pip install --upgrade pip
$> python3 -m pip install --upgrade Pillow
$> pip3 install -r requirements.txt
```

(Optional) To use the GUI, you need to install Qt5 for python:

`$ sudo apt install python3-pyqt5`

---

## Configuration

Use the configuration file `config.json` to configure parameters.

To generate single DAG task, set `multi-DAG`=`false`, then in `single_task`:

- `multi-DAG`: false
- `set_number`: number of dags to be generated
- `fname_prefix` and `fname_int_sufix`: the resulting filename is `fname_prefix``fname_int_sufix`. **DONT USE '-' or '_'** in the resulting filename since it will affect the automation flow.
- `dummy_source_and_sink`: use it always false since tasks w time 0 will crash when running SCHED_DEADLINE
- 

When generating single DAGs:

 - `max_period`:  end to end period in ns,
 - `max_bytes`: max number of bytes send per message,
 - `max_acc_tasks`: max number of tasks to be randomized. ,
 - `acc_ids`: a list of int index for the accelerator island. For example, if the platform has one island of cpu and one island w acc, then the list is [1]. if there are two cpu islands (like big.little) and two accelarators, then the list is [2,3],
 - `random_non_scalable_C`: boolean indicating whether the non scalable part of C is randomized, up to 10% the size of C. If false, it will be zero.

## Controling the DAG size

The following parameters are used to control the DAG size. First, it randomizes the number of layers in the graph, between `layer_num_min` and `layer_num_max`. Then, for each layer, it randomizes the number of nodes of the layer according to `parallelism`. The parameter `connect_prob` controls the edge density. It should be a value lower than 1.0.

## Feasibility Check

There is a simple feasibility generated run for the generated DAG such that this DAG is more likely, but not guaranteed,to be have a feasible task placement. This check is important, otherwise *dag-rand-gen* would generate lot's of unfeasible DAGs and we would need to manually check for each DAG if it is actually unfeasible, wasting a lot of time. With this check, the vast majority of the generated DAG is feasible. However, some DAGs, specially for bigger DAGS with more tasks then the number of cores, could be unfeasible. 

The process is like this. After the DAG structure is defined, there is a step that assigns random runtime to the tasks. The sum of the tasks runtime is then normalized according to the DAG period `max_period`.
All times are assuming that their **tasks are placed on a CPU island with capacity 1.0**. Note that, when running the optimization, the platform model must include a CPU island with capacity 1.0. Otherwise, the random dag generator would require additional inputs, like the capacity of all platform island, making it more complex and less reusable. 

Then, assuming that all task could be placed on this island with capacity 1.0, which is obvioulsy a simplistic assumption, it calculates the longest path in the DAG. This path must be shorted than the DAG end-to-end deadline, which is currently set equals to the DAG period `max_period`. If this is not the case, the DAG is discarded.

When there are islands representing hardware accelerators, as long as the capacity for their islands is greater than 1.0
and the accelerator does not have frequency scaling, it is guaranteed that if a task is assigned to an accelerator, 
it's runtime will be only faster than the runtime assuming the CPU island with capacity 1.0. This way, the feasibility still holds.

In the future, when the model and experimental is expanded to support frequency scaling in the hardware accelerators, it is just a matter to ensure that the task runtime assuming the accelerator at its lowest frequency is lower than the runtime assuming the CPU island with capacity 1.0.

---

## Usage

First, change the configurations in `config.json`. Then, depending on your perference:

### 1. Use the command line interface

`$ python3 src/daggen-cli.py`


---

## Examples

Here are some simple examples of generated DAGs:

![](doc/example_1.png)

![](doc/example_2.png)

![](doc/example_3.png)

or more complicated DAGs:

![](doc/example_4.png)

![](doc/example_5.png)

![](doc/example_6.png)

---

## Known Issues

1. This code is not tested on Windows, but it should not have too many problems. The only potential issue is that the difference is in folder naming where Windows uses a backslash (`\`), instead of a forwardslash (`/`). I will test it and make it compatitable in the future. 
2. In some cases, the critical path could be larger than the period.

---

## Publications used the generator

- Shuai Zhao, Xiaotian Dai, Iain Bate. "DAG Scheduling and Analysis on Multi-core Systems by Modelling Parallelism and Dependency". Transactions on Parallel and Distributed Systems (TPDS). IEEE. 2022.
- Shuai Zhao, Xiaotian Dai, Iain Bate, Alan Burns, Wanli Chang. "DAG scheduling and analysis on multiprocessor systems: Exploitation of parallelism and dependency". In Real-Time Systems Symposium (RTSS), pp. 128-140. IEEE, 2020.

---

## Citation

Please use the following citation if you use this code for your work: 

```
Xiaotian Dai. (2022). dag-gen-rnd: A randomized multi-DAG task generator for scheduling and allocation research (v0.1). Zenodo. https://doi.org/10.5281/zenodo.6334205
```

BibTex:

```
@software{xiaotian_dai_2022_6334205,
  author       = {Xiaotian Dai},
  title        = {{dag-gen-rnd: A randomized multi-DAG task generator 
                   for scheduling and allocation research}},
  month        = mar,
  year         = 2022,
  publisher    = {Zenodo},
  version      = {v0.1},
  doi          = {10.5281/zenodo.6334205},
  url          = {https://doi.org/10.5281/zenodo.6334205}
}
```

---

## License

This software is licensed under MIT. See [LICENSE](LICENSE) for details.

[![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](http://badges.mit-license.org)
