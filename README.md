# balanced-infra

Balanced infrastructure definitions and tools.

## Installation

pip install -r requirements.txt

## Usage

The `brix` command interacts with templates and stacks.

### brix validate

`brix [options] validate [--full]`

The validate subcommand checks all templates for errors. An optional `--full`
flag can be passed to do deeper (and slower) validations. If errors are found,
the exit code will be set to 1. To see the full traceback of an error, use
`brix show`.

Example:

```bash
$ brix validate
balanced_region ok
legacy_region ok
balanced_az ok
balanced_gateway ok
balanced_docs ok
balanced_api ok
```

### brix show

`brix [options] show <name>`

The show subcommand displays the rendered JSON for a template.

Example:

```bash
$ brix show balanced_docs
{
    "Description": "Balanced docs",
    ...,
}
```

### brix sync

`brix [options] sync`

The sync subcommand uploads all templates to S3 for use with CloudFormation.

Example:

```bash
$ brix sync
Uploading balanced_region us-east-1 us-west-1 us-west-2
Uploading legacy_region us-east-1 us-west-1 us-west-2
Uploading balanced_az us-east-1 us-west-1 us-west-2
Uploading balanced_gateway us-east-1 us-west-1 us-west-2
Uploading balanced_docs us-east-1 us-west-1 us-west-2
Uploading balanced_api us-east-1 us-west-1 us-west-2
```

### brix update

`brix [options] update [--no-sync --param=KEY:VALUE...] <stack> [<template>]`

The update subcommand with create or update a stack using a given template. The
`--no-sync` argument will suppress the initial sync to S3. Be warned this can
result in errors if you reference an un-synced template from your stack. The
`--param` argument can be used to pass parameters to the stack. When updating an
existing stack, all existing parameters will be copied over.

## Adding A Template

To add a new template you need to:

1. Add a new Python file containing a subclass of Template (see `balanced_docs.py` for an example).
2. Update `balanced_region.py` and/or `legacy_region.py` to deploy the required static stacks based on #1.
3. Update `brix/__init__.py` to include your new file in the `TEMPLATES` list.

## Building a new AMI

The `packer/` folder contains templates and scripts to build an AMI to use as
our base image. To build the image you need the validation key (`validation.pem`)
as well as the AWS certificate and key (`balanced-aws.crt` and `balanced-aws.key`,
as Noah for these). Put all three of those in `packer/` folder and ensure your
`$AWS_ACCESS_KEY_ID` and `$AWS_SECRET_ACCESS_KEY` environment variables are set.

To verify everything is all set:

```bash
$ packer validate balanced-client.json
```

To start the build:

```bash
$ packer build balanced-client.json
```

After the build completes it will display the three (one for each region) AMI IDs.
Copy these into `templates/balanaced_region.py`.
