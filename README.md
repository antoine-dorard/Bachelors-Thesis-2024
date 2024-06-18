# Enhancing Android Vulnerability Detection: Integrating LLMs with SAST tools

## Platform
This framework must be run on a Unix-based system, which is required by MobSF. The parameter --mobsf-output can be used to specify the output directory of MobSF. If this parameter is provided, the MobSF scan will be skipped, and the provided JSON file will be used instead.

## Requirements
- Python 3.11

## Installation
From the main directory, run the following command to install the required packages:
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py --dir <application_directory> --api-key <api_key>
```

## Implementation of Custom Clustering Algorithm

Custom clustering algorithms can be implemented by extending the `ClusteringInterface` class and implementing the `cluster` method. The `cluster` method should return a list of `Cluster` objects. Specific requirements and guidelines for implementing custom clustering algorithms are provided in the `ClusteringInterface` class.

After the algorithm is implemented, it can be registered to the pipeline by calling register_clustering_algorithm(clustering_algorithm_instance) before executing the pipeline.

