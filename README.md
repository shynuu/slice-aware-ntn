# Slice Aware Non Terrestrial Networks

This repository contains all the tools to launch a testbed and experiment our integration method of NTN as slice-aware backhaul links in 5G networks.

![satellite_transport_network](https://user-images.githubusercontent.com/41422704/121254098-2b37ba00-c8aa-11eb-91ba-537959db5d3b.png)

**Abstract** 
<div style="text-align: justify">
With the recent integration of Non Terrestrial Networks into 3GPP Release 17, 5G networks are expected to benefit from the NTN large coverage area.
This integration will help mobile terrestrial networks reach a worldwide coverage.
However, this ultimate ubiquity also comes with its set of challenges to overcome. 
One of the main issues is the seamless integration of NTN into the existing mobile network standard.
In this paper, we propose a comprehensive architecture integrating NTNs as slice-aware backhaul links.
This architecture remains fully compliant with the 3GPP standard.
For this purpose, we propose an end-to-end slice model integrating NTNs and 5G networks.
Then, we implement this model on a 5G-satellite testbed, adding new functional components to interconnect both networks at the control and data plane levels.
Lastly, we evaluate the performances of our method using the aforementioned testbed by monitoring each slice and their related Quality of Service (QoS) requirements.
</div>

# Table of contents

- [Requirements](#requirements)
  - [Hardware](#hardware)
  - [Software](#software)
- [Run the Testbed](#run-the-testbed)
  - [Objective](#objective)
  - [Install dependencies](#install-dependencies)
  - [Configure scenarios](#configure-scenarios)
  - [Run scenarios](#run-scenarios)
  - [Evaluate scenarios](#evaluate-scenarios)
  - [Samples](#samples)
- [Custom scenarios](#custom-scenarios)
- [Helpers](#helpers)
  - [Vagrant](#vagrant)
  - [Bare-metal scripts](#bare-metal-scripts)
- [Components used](#components-used)
- [Authors](#authors)
- [Acknownledgments](#acknownledgments)
- [License](#license)

## Requirements

### Hardware

Hardware resources depends on the scenario you want to evaluate. We recommand at least 8 CPU, 8 GB RAM and 50 GB of disk.

### Software

- Docker
- Docker Compose
- Python 3.8
- A Linux Kernel compatible with free5GC (Ubuntu 18.04 with kernel 5.0.0-23-generic or 20.04 with Kernel 5.4)

## Run the Testbed

### Objective

This testbed has been developed in order to easily define scenarios, deploy them and evaluate their performances using docker containers.

Scenarios are defined in a configuration file which is parsed by the testbed generator. For each scenario, the parser generates a `docker-compose.yaml` file, a set of scripts and configuration files which correspond to the testbed. Under the hood, docker-compose is called when you run the testbed.

It has been specifically designed to demonstrate our method of NTNs integrated in 5G networks as slice-aware backhaul links.

### Install dependencies

First clone the repository

```bash
git clone https://github.com/shynuu/slice-aware-ntn
cd slice-aware-ntn
```

Install all the python dependencies :

```bash
cd code
pip3/pip3.8 install -r requirements.txt
```

### Configure scenarios

Two scenarios are preconfigured in the [scenario file](code/template/scenario.yaml): the **Slice Aware** and **Slice Unaware** scenarios as described in our paper.

These scenarios launches 64 containers (**/!\ Be sure to have enough resources available**):

- 1 gNB
- 9 UEs
- 1 Non Terrestrial Networks Quality of Service Function (NTNQOF)
- 2 Slice Classifiers (Interconnect RAN-NTN and NTN-CN)
- 2 Trunks (GEO system and LEO system)
- 9 VoIP servers in slice 0 (one server per UE to avoid iperf server to struggle when multiple clients are connected)
- 9 Web servers in slice 0
- 9 Streaming servers in slice 1
- 9 Streaming servers in slice 2
- 5G Control Plane components (10 containers): 1 AMF, 1 SMF (supporting NTN), 1 PCF, 1 NRF, 1 NSSF, 1 UDM, 1 UDR, 1 QOF (for NTN support), 1 AUSF, 1 Mongo (free5gc implementation dependent)
- 3 UPFs (one for each slice)

Each component corresponds to a docker container. Dockerfiles are located in the [containers](code/config/containers/main) folder.

We have already pre-built images pushed on the Docker HUB: https://hub.docker.com/r/shynuu/sa-ntn. At the run step, docker will pull all the images from the HUB and run containers.

Still, you can build all the images manually with:

```bash
python3.8 nt.py images --build all
```

On a 8 vCPU, 8 GB of RAM, Ubuntu 20.04 VM, image build took around 1 Hour.

### Run scenarios

Run both scenarios with:

```bash
python3.8 nt.py run --scenario saw-ntn suaw-ntn
```

Options can be specified and help can be display with `python3.8 nt.py run -h`

- `--iterations <number of iterations>`: By default, each scenario is only executed once. You can run each scenario multiple times with this option
- `--pcap`: Capture all the traffic with the `--pcap` option (Be sure to have sufficient storage as a single iteration generates a ~ 13 GB pcap file for our scenario)

Both scenarios will run for 240s and generate probe files located in the `code/testbeds` folder. 

For unknown reasons (we are still investigating), sometimes UEs start and stay in IDLE state and do not establishe PDU Sessions which prevent the correct execution of the testbed. Thus, We implement a try-retry policy and if for a given iteration, some UE do not establish proper PDU sessions, we stop the iteration and retry until all UEs are in the CONNECTED state.

At the end of the execution, results would be placed in `code/receipes` folder.

### Evaluate scenarios

Before evaluating 2 scenarios, you need to run them before to generate probe files.

To evaluate scenarios, run:

```bash
python3.8 nt.py evaluate -s1 saw-ntn -s2 suaw-ntn
```

You can display help and additionnal options with `python3.8 nt.py evaluate -h`

- `--plot`: Plot the results with matplotlib
- `--contribution`: Generate tikz code for latex integration

PDF figures will be generated in folder `code/receipes/eval_saw-ntn_suaw-ntn`

### Samples

We have already executed testbeds and generated results in folder `code/receipes/eval_saw-ntn_suaw-ntn`

## Custom scenarios

*In progress...*

## Helpers

### Vagrant

We provide a Vagrant Box which automatically install all the required dependencies in `vagrant` folder. You will need the following requirements :

- VirtualBox installed
- Vagrant plugins disksize and reload (install with `vagrant plugin install vagrant-reload` and `vagrant plugin install vagrant-disksize`)

### Bare-metal scripts

We provide two scripts for easy installation and configuration :

- [Kernel update (for Ubuntu 18.04)](scripts/kernel.sh): update kernel to version **5.0.0-23-generic** and reboot
- [Install dependencies](scripts/install.sh): install dependencies

## Components used

- UERANSIM for software gNB and UE https://github.com/aligungr/UERANSIM
- iperf for traffic generation in applications https://sourceforge.net/projects/iperf2/
- Slice Classifier for classifiers https://github.com/shynuu/slice-classifier
- Free5GC for 5G CN https://github.com/free5gc/free5gc
- Fork of Free5GC for SMF, QOF and NTNQOF https://github.com/shynuu/5g-core-ntn
- Trunks for satellite system simulation https://github.com/shynuu/trunks

## Authors

This specific work has been achieved in the SUPER-G project within [IRT Saint Exupéry](https://www.irt-saintexupery.com/).

## Acknownledgments

We would like to thank the free5gc team for their open-source 5G Core Network as well as UERANSIM team for their open-source software gNB and UE.

## License

The code of the testbed is released under the [MIT](LICENSE), you are free to fork, alter and contribute to the testbed. All python code is documented and any contribution are welcomed !

Each standalone component used within the testbed has a dedicated license.