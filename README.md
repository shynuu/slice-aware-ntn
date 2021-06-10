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
    - [Scenario configuration](#scenario-configuration)
    - [Run the scenarios](#run-the-scenarios)
    - [Evaluate performances and plot results](#evaluate-performances-and-plot-results)
- [Advanced testbed configuration](#advanced-testbed-configuration)
  - [Testbed configuration file](#testbed-configuration-file)
  - [Add docker containers](#add-docker-containers)
  - [Define services](#define-services)
  - [Create scenario files](#create-scenario-files)
  - [Add the scenario to the testbed](#add-the-scenario-to-the-testbed)
  - [Add the evaluator for the scenario](#add-the-evaluator-for-the-scenario)
  - [Configure and run the scenario](#configure-and-run-the-scenario)
- [Helpers](#helpers)
  - [Vagrant](#vagrant)
  - [Bare-metal scripts](#bare-metal-scripts)
- [Components used](#components-used)
- [Authors](#authors)
- [Acknownledgments](#acknownledgments)
- [License](#license)

## Requirements

### Hardware

Hardware resources depend on the scenario you want to evaluate. We recommand at least 8 CPU cores, 8 GB RAM and 50 GB of disk.

### Software

- Docker
- Docker Compose
- Python 3.8
- A Linux Kernel compatible with free5GC (Ubuntu 18.04 with kernel 5.0.0-23-generic or 20.04 with Kernel 5.4)

## Run the Testbed

### Objective

This testbed has been developed in order to easily define scenarios, deploy them and evaluate their performances using docker containers.

Scenarios are defined in a configuration file which is parsed by the testbed generator. For each scenario, the parser generates a `docker-compose.yaml` file, a set of scripts and configuration files used to run the testbed. Under the hood, docker-compose is called when you run the testbed.

This project has been specifically designed to demonstrate that our method can integrate NTNs in 5G networks as slice-aware backhaul links.

### Install dependencies

First clone the repository:

```bash
git clone https://github.com/shynuu/slice-aware-ntn
cd slice-aware-ntn
```

Install all the python dependencies:

```bash
cd code
pip3/pip3.8 install -r requirements.txt
```

### Configure scenarios

Two scenarios are preconfigured in the [scenario file](code/template/scenario.yaml): the **Slice Aware** and **Slice Unaware** scenarios as described in our paper.

These scenarios launch 64 containers (**/!\ Be sure to have enough resources available**):

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

For unknown reasons (we are still investigating), sometimes UEs start and stay in IDLE state and do not establish PDU Sessions, this prevents the correct execution of the testbed. We thus implemented a try-retry policy and, if for a given iteration, some UEs do not establish proper PDU sessions, we stop the iteration and retry until all UEs are in the CONNECTED state.

At the end of the execution, results should be placed in the `code/receipes` folder.

You can list all the running containers with `docker container ls` and display a container log with `docker logs <container-name>`.

### Evaluate scenarios

Once you have run the scenarios, probe files are generated. Then, to evaluate the scenarios, simply execute:

```bash
python3.8 nt.py evaluate -s1 saw-ntn -s2 suaw-ntn
```

You can display help and additionnal options with `python3.8 nt.py evaluate -h`

- `--plot`: Plot the results with matplotlib
- `--contribution`: Generate tikz code for latex integration

PDF figures will be generated in the `code/receipes/eval_saw-ntn_suaw-ntn` folder.

### Samples

We have already executed testbeds and generated results in the `code/receipes/eval_saw-ntn_suaw-ntn` folder.


### Custom scenarios

You can easily define new scenario configurations and evaluate them by changing the [scenario](code/template/scenario.yaml) file.

As an example, two custom scenarios are given: `custom-scenario-aware` and `custom-scenario-non-aware`. We detail step by step how to define yours.

#### Scenario configuration

Scenarios need to be evaluated by pair, first in the slice-aware mode and then in the non-slice-aware mode. They should have the exact same topology.

To configure a scenario in the `scenario.yaml` file you need to:

- Define the number of NTN links provided by the satellite operator. In our example, 2 links are provided: 1 LEO (100 Mbps forward, 25 Mbps return, 45 ms += 5 ms delay and no ACM simulation) and 1 GEO (150 Mbps forward, 15 Mbps return, 550 ms += 50 ms delay and no ACM simulation)
- Define the slices running on each link. In our example, 1 slice runs on each link: S0 for 60s on LEO link and S1 for 60s on GEO link
- Define the applications instanciated on each slice Data Network. In our example, on S0 we have VoIP and Web applications and on S1 we have Streaming and VoIP applications
- Define the number of UE in the RAN
- Set the total duration of scenario
- Give a name to the slice-aware and non-slice-aware scenarios. `custom-scenario-aware` and `custom-scenario-non-aware` in our example

#### Run the scenarios

Once you have defined your own scenarios, you can run them with:

```bash
python3.8 nt.py run --scenario custom-scenario-aware custom-scenario-non-aware --iterations 10
```

This will run the testbed associated with the scenario and generate probe files in `receipes/custom-scenario-aware` and `receipes/custom-scenario-non-aware` folders.

You can also only generate the testbed configuration file with:

```bash
python3.8 nt.py generate --scenario custom-scenario-aware custom-scenario-non-aware --iterations 10
```

This will output all the configuration files in the `code/testbeds` folder.

#### Evaluate performances and plot results

To evaluate scenarios, run:

```bash
python3.8 nt.py evaluate -s1 custom-scenario-aware -s2 custom-scenario-non-aware --plot --contribution
```

This will generate PDF figures, Tikz latex code in `code/receipes/eval_custom-scenario-aware_custom-scenario-non-aware` folder and plot figures with matplotlib.

## Advanced testbed configuration

*slice-aware* and *non-slice-aware* scenarios are configured in python scripts. The testbed is not limited to these scenarios and you can add your own scenario definition to generate your custom testbed.

We highly recommend you to take a look at these scenario files when following the instructions below. They are well documented and helpful to understand the definition logic.

### Testbed configuration file

The testbed global configuration file is located in the [code/configuration.conf](code/configuration.conf) file. You can manage images folder, service configuration folder and output folders.

In case you alter this file, please adapt the following instructions.

### Add docker containers

The first step is to add your image Dockerfile to the [containers](code/config/containers/) folder.

The workflow is the following:

- Create the Dockerfile dedicated to your service in a dedicated folder within the [main](code/config/containers/main) folder. This Dockerfile can use the multistage technique and call for images in the [required](code/config/containers/required) folder. An example of such Dockerfile is the [gnb](code/config/containers/main/gnb/Dockerfile) which calls the [ueransim](code/config/containers/required/ueransim/Dockerfile) image.
- Create the required Dockerfile used by your multistage build if needed under a dedicated folder within the [required](code/config/containers/required) folder.
- Add configuration files of the service under the [services](code/config/services/) folder.
- Add your Dockerfiles to the [images](code/config/containers/images.yaml) configuration file with the same name as your folder.

```yaml
images:
  - name: "new_service"
    fulltag: "account/myrepo:new_service"
    required:
      - "new_service_requirement"
required:
  - name: "new_service_requirement"
    fulltag: "account/myrepo:new_service_requirement"
```

You can now build the image alongside all the required images and add them to your local repository with:

```bash
python3.8 nt.py images --build new_service --main-cache --pre-cache
```

The *new_service* image will be built with the tag *account/myrepo:new_service*. `--main-cache` and `--pre-cache` pass the `--no-cache` option to the `docker build` command.

Now that you have the docker image ready, you can define the python code of your service.

### Define services

Before defining the scenario logic and topology, you need to define the services.

Create a new python file within the [model](code/source/model/) folder with the name of your scenario implementing all your services.

Each service needs to implement the [Service](code/source/model/__init__.py#L60) class:

```python
class Service(object):
    """Service class"""

    configuration_file = None
    docker_image = None

    def __init__(self, name: str, repository: Repository) -> None:
        self.name = name
        self.networks: Dict[str, ipaddress.IPv4Address] = {}
        self.compose = None
        self.entrypoint = None

        if self.configuration_file != None:
            path = f"{repository.configurations_folder}/{self.configuration_file}"
            with codecs.open(path, mode="r", encoding="utf8") as f:
                self.configuration = yaml.load(
                    f.read(), Loader=yaml.RoundTripLoader)

    def attach_network(self, name: str, address: ipaddress.IPv4Address):
        """Add a network address to the service"""
        self.networks[name] = address

    def write_configuration(self, folder_path: str) -> None:
        """
        Write the configuration file of the service
        """

        if self.configuration_file != None:
            path = f"{folder_path}/{self.name}.yaml"
            yam = yaml.YAML()
            yam.indent(sequence=4, offset=2)
            with codecs.open(path, "w", encoding="utf-8") as configuration:
                yam.representer.add_representer(HexInt, representer)
                yam.dump(self.configuration, configuration)

    def configure(self, repository: Repository) -> None:
        """Configure the service"""
        logging.error(
            f"{self.name} service function configure not implemented, I QUIT !")
        sys.exit(1)

    def configure_compose(self, repository: Repository) -> None:
        """Configure the service docker compose"""
        logging.error(
            f"{self.name} service function configure_compose not implemented, I QUIT !")
        sys.exit(1)

    def configure_entrypoint(self, repository: Repository) -> None:
        """Configure the entrypoint if necessarily"""
        if self.compose.entrypoint != None:
            logging.error(
                f"{self.name} service function configure_entrypoint not implemented, I QUIT !")
            sys.exit(1)

    def write_entrypoint(self, repository: Repository) -> None:
        """Write the entrypoint if necessarily"""
        if self.entrypoint != None:
            self.entrypoint.write(repository.containers_folder, self.name)
```

When you're done, you can define the scenario and scenario topology.

### Create scenario files

Create a new python file within the [model](code/source/model/) folder with the name of your scenario implementing all your services.

Each service needs to implement the [Scenario](code/source/scenario/__init__.py#L28) class.

For each scenario, you need to specify the `scenario_type` which acts as the identifier of the scenario type in the [scenario.yaml](code/template/scenario.yaml) file.

You can optionally define a `validation_scheme` using [cerberus](https://docs.python-cerberus.org/en/stable/schemas.html) to validate the user input in [scenario.yaml](code/template/scenario.yaml)

```python
class Scenario(object):
    """Generic Scenario Interface"""

    validation_schema = None
    scenario_type = "generic"

    def __init__(self, definition: Dict) -> None:
        self.name = definition['name']
        self.definition = definition
        self.networker = Networker()
        self.repository = Repository()

    def set_path(self, results_folder: str, containers_folder: str, configurations_folder: str, output_configuration_folder: str, scenario_folder: str):
        """
        Set the path for the output folders
        """

        self.repository.results_folder = results_folder
        self.repository.containers_folder = containers_folder
        self.repository.configurations_folder = configurations_folder
        self.repository.output_configuration_folder = output_configuration_folder
        self.repository.scenario_folder = scenario_folder

    def prepare_scenario(self) -> None:
        """
        Prepare all the requirements prior to the generation of the scenario topology
        """

        logging.info(
            f"[{self.name}] prepare_scenario function undefined, I QUIT !")
        sys.exit(1)

    def generate_networks(self) -> None:
        """
        Generate the networks of the testbed
        """

        logging.info(
            f"[{self.name}] generate_networks function undefined, I QUIT !")
        sys.exit(1)

    def generate_topology(self) -> None:
        """
        Create all the services and generate the network topology of the scenario
        """

        logging.info(
            f"[{self.name}] generate_topology function undefined, I QUIT !")
        sys.exit(1)

    def configure_services(self) -> None:
        """
        Configure all the services
        """

        for service in sorted(self.repository.services):
            self.repository.services.get(service).configure(self.repository)

    def configure_compose(self) -> None:
        """
        Configure the services docker compose part
        """

        for service in sorted(self.repository.services):
            self.repository.services.get(
                service).configure_compose(self.repository)

    def configure_entrypoint(self) -> None:
        """
        Configure the services entrypoint
        """

        for service in sorted(self.repository.services):
            self.repository.services.get(
                service).configure_entrypoint(self.repository)

    def write_configuration(self) -> None:
        """
        Write the configuration files of each service
        """

        for service in sorted(self.repository.services):
            s = self.repository.services.get(service)
            s.write_configuration(self.repository.output_configuration_folder)

    def write_entrypoint(self) -> None:
        """
        Write entrypoints for each service
        """

        for service in sorted(self.repository.services):
            s: Service = self.repository.services.get(service)
            s.write_entrypoint(self.repository)

    def write_compose(self) -> None:
        """
        Write docker-compose.yaml file
        """

        output = {
            "version": "3.9",
            "services": {},
            "networks": {},
            "volumes": {"dbdata": None}
        }

        for service in sorted(self.repository.services):
            if self.repository.services[service].compose != None:
                output["services"][service] = self.repository.services[service].compose.generate()

        network_index: int = 0
        for network in sorted(self.networker.networks_name):
            output["networks"][network] = {
                "name": network,
                "driver": "bridge",
                "ipam": {
                    "driver": "default",
                    "config": [
                        {
                            "subnet": str(
                                self.networker.networks_name.get(network))
                        }
                    ]
                },
                "driver_opts":
                {
                    "com.docker.network.bridge.name": f"network-{network_index}"
                }
            }
            network_index += 1

        path: str = f"{self.repository.scenario_folder}/{self.name}/docker-compose.yaml"
        yam = yaml.YAML()
        yam.indent(sequence=4, offset=2)
        with codecs.open(path, "w", encoding="utf-8") as compose_file:
            yam.dump(output,  compose_file)

    def run(self) -> None:
        logging.info(f"[{self.name}] run function undefined, I QUIT !")
        sys.exit(1)
```

When you run a scenario, the functions are called following this order:

```python
scenario.prepare_scenario()
scenario.generate_networks()
scenario.generate_topology()
scenario.configure_services()
scenario.write_configuration()
scenario.configure_compose()
scenario.configure_entrypoint()
scenario.write_entrypoint()
scenario.write_compose()
```

### Add the scenario to the testbed

Add the scenario to the supported testbed scenario in [testbed](code/source/testbed/testbed.py#L27) as follows:

```python
class Selector(object):
    """Scenario selector class"""

    scenarios = [SliceAwareNTN, NonSliceAwareNTN, MyNewScenario]
```

### Add the evaluator for the scenario

You need to define a specific evaluator to your scenario based on the probes it generates.

This evaluator needs to implement the [Evaluator](code/source/evaluator/__init__.py#L21) class.

```python
class Evaluator(object):
    """Generic Evaluator Class"""

    def __init__(self, t1: Testbed, t2: Testbed) -> None:
        self.t1 = t1
        self.t2 = t2
        self.output_path = None

    def evaluate(self, contribution: bool, plot: bool) -> None:
        """generic evaluate function"""
        pass
```

### Configure and run the scenario

You're now all set to add your scenario configuration in the [scenario file](code/template/scenario.yaml) and execute it using the [`run`](#run-scenarios) command!

## Helpers

### Vagrant

In the `vagrant` folder we provide a Vagrant Box which automatically installs all the required dependencies. You will need the following requirements:

- VirtualBox installed
- Vagrant plugins disksize and reload (install with `vagrant plugin install vagrant-reload` and `vagrant plugin install vagrant-disksize`)

### Bare-metal scripts

We provide two scripts for easy installation and configuration:

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

You can reach us at youssouf.drif@irt-saintexupery.com

## Acknownledgments

We would like to thank the free5gc team for their open-source 5G Core Network as well as UERANSIM team for their open-source software gNB and UE.

## License

The code of this testbed is released under the [MIT license](LICENSE), you are free to fork, alter and contribute to the testbed. All python code is documented and any contribution is welcomed!

Each standalone component used within the testbed has a dedicated license.
