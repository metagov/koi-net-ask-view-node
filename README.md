# koi-net-node-template

# Quick Start

## 1. Create repo from template
Click `Use this template` -> `Create a new repository` and finish the set up process.

## 2. Clone repo
Clone the resulting repository
```
git clone <your-github-url-here>
```

## 3. Set up virtual environment

```
python -m venv .venv
```
For Windows:
```
.venv\Scripts\activate
```
For Mac/Linux:
```
source .venv\bin\activate
```

## 4. Set node name

Pick a name for your node, and update the package directory name in `src/`, `node_name` in `config.py`, and `name` in `pyproject.toml`.

## 5. Install your node package
This will install your node in editable mode, reflecting changes as you edit the source code.
```
pip install -e .
```

## 6. Set up .env file
Create a file called `.env` and inside set `PRIV_KEY_PASSWORD=<password_of_your choice>`. This will be used to encrypt your node's private key.

## 7. Run node
```
python -m koi_net_YOUR_NODE_NAME_node
```

# Modifying this Node
Take a look at the [koi-net repo](https://github.com/BlockScience/koi-net) for documentation about the koi-net package and developing nodes. This template provides the basic structure for a full node setup. You'll likely want to start by modifying `config.py` with the RID types your node deals with, and adding some new knowledge handlers in `handlers.py`.

# Adding a License
This template doesn't contain any license by default. If you add a `LICENSE` file, make sure to update your `pyproject.toml` with the following line:
```
license = {file = "LICENSE"}
```