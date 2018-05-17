# TensorFlow Workshop

This is the project repository for a TensorFlow workshop in Chicago in
May, 2018.

- [Schedule](#schedule)
- [Sessions](#sessions)
- [Slack](#slack)
- [Servers](#servers)

## Schedule

- 10:00 - 10:30 (30 min) : Registration + setup
- 10:30 - 11:10 (40 min) : Session 1
- 11:10 - 11:25 (15 min) : Break
- 11:25 - 12:05 (40 min) : Session 2
- 12:05 - 12:20 (15 min) : Break
- 12:20 - 13:00 (40 min) : Session 3
- 13:00 - 14:00 (60 min) : Lunch
- 14:00 - 14:40 (40 min) : Session 4
- 14:40 - 14:55 (15 min) : Break
- 14:55 - 15:35 (40 min) : Session 5
- 15:35 - 15:50 (15 min) : Break
- 15:50 - 16:30 (40 min) : Session 6
- 16:30 - 17:00 (30 min) : Wrap up + spill over

## Sessions

Below is a working list of workshop session topics.

### Session 1. Introduction to deep learning workflow

Objective: *Walk students through the process we'll be going through
during the workshop*

This will include an introduction to Guild and the workshop
project. We can pair off and access an EC2 instance to run various
operations:

- Acquire images
- Detect classes
- Run model as application

### Session 2. Basics of Deep Learning

Objective: Understanding the main concepts around image classification
(convolutional neural networks, transfer learning)

Will share a simple notebook around cats/dogs just for learning
purposes

### Session 3. Object Detection

Objective: A quick tour of the main concepts developed in the last few
years in object detection, ending with Mask-RCNN in Keras

Architectures include:
R-CNN
Fast R-CNN
Faster R-CNN
Mask R-CNN
One shot (YOLO, SSD)

Will share other repos of other approaches and walk through code
examples of the main concepts.

### Session 4. Model fine-tuning, part 1

Objective: *Fine-tune a pretrained model on a narrower set of images*

E.g. use pets database to fine-tune a model trained on COCO.

Students should see some difference between the application
demonstrated in Session 2 - ideally it would be an improvement.

### Session 5. Dataset creation

Objective: *Generate a dataset unique to the room and object being
detected*

### Session 6. Model fine-tuning, part 2

Objective: *Fine-tune a pretrained model on the dataset generated in
Session 5*

Students should see a marked improvement in the detector.

## Slack

We will use Slack to share information during the workshop and for any
followup work.

Students will receive an invitation to Slack before the workshop
begins.

## Servers

Server hostnames and user passwords will be assigned via the Slack
channel during the workshop.

### Logging on to a server

Once you have your server hostname, follow these steps to log on.

- In your browser, open https://&lt;server hostname&gt;
- Log on with user name `ubuntu`
- Specify the password provided

**NOTE:** You must use `https` in the browser URL above. If you use
`http` the browser will not connect to the server.

This will open a terminal session on the server. You can repeat these
steps in a new tab or window to open multiple terminal sessions to a
server.

### Start or attach to a tmux session

If you are logging in for the first time, start a tmux session by
running:

    tmux

tmux is a terminal multiplexer that lets you open multiple terminals
in a single session. It also lets you reconnect to your terminals if
you get disconnected.

If you already have a tmux session, attach to it by running:

    tmux attach

### Activate the workshop environment

Each time you open a terminal session to a server, including a new
tmux window, you must activate the environment used for training and
other operation.

To activate the workshop environment, in a terminal session, run:

    source activate workshop

## tmux quick reference

All tmux commands are run by typing `Ctrl-b` followed by a command
character.

### Open a new window

    Ctrl-b c

### List windows

    Ctrl-b w

### Navigate to window NUM

    Ctrl-b NUM

### Navidate to preview and next windows

Previous:

    Ctrl-b p

Next:

    Ctrl-b n

### Navigate to last window

    Ctrl-b l

### Scroll up history

Start scrolling:

    Ctrl-b PGUP

Exit scrolling:

    q
    Ctrl-C

### Detach from the current session

    Ctrl-b d

## Guild command quick reference

### Listing runs

    guild runs
