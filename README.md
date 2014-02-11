balanced-infra
==============

Balanced infrastructure definitions and scripts

Installation
------------

pip install -r requirements.txt

Usage
-----

The `balanced-stacks` is the way to interact with things. It has four subcommands:
`validate`, `show`, `sync`, and `update`.

`balanced-stacks validate` will load all templates and ensure they can be
converted to JSON.

`balanced-stacks show <name>` will display the rendered CloudFormation template
for a given name.

`balanced-stacks sync` will upload all templates to S3.

`balanced-stacks update [<region>]` will create or update all stacks for a region.
The default region can be set via `$BALANCED_AWS_REGION` and defaults to `us-west-2`.

Adding A Template
-----------------

To add a new template you need to:
1. Add a new Python file containing a subclass of Template (see `balanced_docs.py` for an example).
2. Update `balanced_region.py` to deploy the required stacks based on #1.
3. Update `__init__.py` to include your new file in the `TEMPLATES` list.
