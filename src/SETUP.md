# Workshop setup

## EC2 resources

- Start student GPUs
- Start large GPU
- Start image proxy

    $ cd terraform2
    $ terraform apply

Get the list of hostnames by running:

    $ ./hostnames

After pairing students up, ask a rep from each pair to IM me on Slack
and I'll assign the hostname.

## Cameras

Setup cameras on Guild Workshop network.

- Install on tripods around the room
- Use mobile app connected to Guild Workshop to position and zoom

## Control workstation

- Hard-wired connection to Guild Workshop router
- Wireless connection to Internet accessible network

## Start image pump

Pump camera images to image proxy:

    $ python pump.py

## Run tests on large GPU

- Collect sample images
- Run detect
- Finetune pets
- Label images
- Finetune cats
- Evaluate
- Push runs to shared

## pawnee as backup

If the large GPU doesn't work for whatever reason (e.g. network
issues) we can fall back on pawnee.

Use `nmtui` to configure wired (192.168.2.xxx) and wireless (guest LAN
to Internet):

    sudo nmtui
