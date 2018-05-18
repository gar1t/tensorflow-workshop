# Workshop script

**TODO:** Number sections when finished.

## Setup

### GPU hosts

Students should all log into their assigned GPU servers. We will be
starting 20 servers, so there will be 2-3 students per server.

Hostname assignments will be made over Slack.

### Terminal sessions and environments

The workshop makes of Guild AI to run commands and manage
workflow. Each command must be executed in a terminal on a GPU
server. Commands should always be run in an activated 'workshop'
environment and in the workshop `src` directory.

To summarize, commands must be run:

- On a GPU server in a terminal
- Within an activated environment
- Within the workshop `src` directory

Once logged in, always run the following:

    $ source activate workshop
    $ cd workshop/src
    $ guild check

This will activate the environment, change to the workshop `src`
directory, and run a check to verify your setup is correct.

 ## Introduction and initial demo

Provide a high level overview of what it is we'll be doing for the
day.

### Introduce workshop problem

We want to create an application that detects a particular object in
the room.

**BACKGROUND:** Overview of CNN and deep learning

### Collect initial sample images

We'll start our exercise by testing a pretrained model to see if it
detects our object.

We need a handful of images to test. We can collect these with the
workshop cameras by running:

    $ guild run images:collect use-proxy=yes

This will start a server on port 8002, which we can use to save images
from the workshop cameras in the room.

We'll want to make sure we have images that contain:

- target object
- similar objects
- people

Stop the `collect` operation by typing `Ctrl-C`. The run can be listed
by running:

    $ guild runs

To view the collected images, use Guild View:

    $ guild view --port 8080

(Optional) Stop View by typing `Ctrl-C`.

**NOTE:** At this time it might be a good idea to start View in a
separate session.

### Run detect using Faster RCNN pretrained on MS COCO

The MS COCO trained model should pick up various objects in the
room. It should even find our target object, though not consistently
or accurately (it will frequently misclassify).

    $ guild run coco-faster-rcnn-resnet101:detect

This operation will apply the trained model to detect objects in our
collected images.

This will download the TensorFlow object detection library (500MB) and
the MS COCO pretrained network (600MB), which will take a while. We'll
use that time to introduce the the project and tools we'll be working
with.

### Introduction to Guild and the workshop project

#### Overview of project

The project is made up of the files in this directory
([`src`](.)). The main file of interest is [`guild.yml`](guild.yml),
which defines the models and operations that will be run throughout
the workshop.

#### Project models

There are three categories of models in the project:

- Support for detection using models pretrained on MS COCO (coco)
- Support for detection using models finetuned with Oxford-IIIT pets
  database (pets)
- Support for detection using models finetuned on images we'll collect
  in the workshop (cats)

To list the models:

    $ guild models

#### Project operations

Each model provides one or more operations.

To list operations:

    $ guild ops

Operation names are displayed with their associated models. For
example the `finetune` operation for the `pets-faster-rcnn-resnet101`
model is listed as `pets-faster-rcnn-resnet101:finetune`.

Each operation is described below in (roughly) the order in which it
would typically be run:

- **collect** - Collect images from the workshop cameras for either
  generating a dataset or for detection using a trained model. This
  operation is supported by [`collect.py`](collect.py) and a VueJS
  application in [`collect`](collect).

- **label** - Label collected images by drawing boxes around and
  tagging known objects. This operation is supported by a labeling
  application from
  https://github.com/frederictost/images_annotation_programme.

- **prepare** - Prepare labeled images for use in fine tuning and
  validation by converting them to TF record format. This operation is
  supported by scripts that are specific to the dataset being
  converted. The prepare script for our cats dataset is
  [`cats/prepare_dataset.py`](cats/prepare_dataset.py).

- **finetune** - Fine tune (train) a model using a prepared dataset
  and a pretrained model. This operation is supported by the
  TensorFlow object detection library in
  [`object_detection/train.py`](https://github.com/tensorflow/models/blob/master/research/object_detection/train.py).

- **evaluate** - Evaluate a trained model using a validation
  dataset. This operation is supported by the TensorFlow object
  detection library in
  [`object_detection/eval.py`](https://github.com/tensorflow/models/blob/master/research/object_detection/eval.py).

- **export** - Export a model for use in detection. This operation is
  supported by the TensorFlow object detection library in
  [`object_detection/export_inference_graph.py`](https://github.com/tensorflow/models/blob/master/research/object_detection/export_inference_graph.py).

- **catscan** - Run the cat detection application. This applies only
  to the `cats` models. This operation is supported by
  [`scan.py`](scan.py) and a VueJS application in [`scan`](scan).

#### Other project files

The project contains various other files, used to support operations.

- **[`cats`](cats)** - configuration and application files associated
  with cats model operations.

- **[`config.json`](config.json)** - workshop camera and related configuration.

- **[`object_detection`](object_detection)** - contains patch to
  TensorFlow's object detection library.

- **[`pipelines`](pipelines)** - object detection pipeline
  configurations used for workshop models.

- **[`pump.py`](pump.py)** - tool used to copy workshop camera images to
  an image proxy.

#### Running operations in Guild

Operations in Guild are run with the `run` command:

    $ guild run MODEL:OPERATION

Each time an operation is run, a *run* is generated. We can list runs
by running:

    $ guild runs

Guild supports a variety of run management commands, which we'll use
throughout the workshop. Help for any Guild command is available by
running `guild CMD --help`.

#### Guild View and TensorBoard

We'll use Guild View and TensorBoard throughout the workshop to view
run results. Guild View can be started by running:

    $ guild view --port PORT

TensorBoard can be opened by clicking the **View in TensorBoard** link
in Guild View.

### Review results of MS COCO trained model

At this point the `detect` operation should be completed. It generates
a detection image for every input image. The detection image contains
bounding boxes and associated labels for each detected object in the
input image.

Use Guild View to view the detection images.

**BACKGROUND:** Pretrained network

**BACKGROUND:** How RCNN works - region search

## Improve our detector using a different dataset

At this point we've seen an off-the-shelf detector, which is good at
detecting a set of general images but not very good at detecting our
target object.

We can try to improve our detection capabilities by fine tuning a
model with a new dataset. We'll use the Oxford-IIIT pets database,
which contains a large number of labeled cats (as well as dogs), to
fine tune a model in the hope of improving our model.

### Prepare the pets dataset for training

The Oxford-IIIT pets dataset provides PASCAL VOC formatted images of
dog and cat breeds. To train with the TF object detection library, we
need to convert these images into TF record datasets - one for
training and another for validation.

    $ guild run pets-dataset:prepare

**BACKGROUND:** Discuss train vs validation splits

### Fine tune our model using pets data

With the prepared dataset, we can run the `finetune` operation on our
pets detector:

    $ guild run pets-faster-rcnn-resnet101:finetune

This start off a finetune operation, which is configured to run for
200K steps. This will take far longer than we have time for (on the
p2.xlarge GPU instances) but students can let their runs continue if
they want.

The instructor will also have a large GPU instance (V100) that trains
much faster and can highlight the performance differences across GPUs.

We'll also have a completed run on hand that we can use for detection
and be able to stop training early.

**BACKGROUND:** Lets talk about what fine tuning is

As the model is training, we can use TensorBoard to view loss and
performance metrics.

In a separete terminal, run:

    $ guild view --port

Note the files generated by the fine tune operation.

Click View in TensorBoard to view the stats for the finetune run.

Spend some time going over the scalars.

**BACKGROUND:** Talk about loss, learning rate, and convergence

Back in View, show the finetune config and walk through some of the
inputs:

- Optimizer (momentum)
- Learning rate
- Steps
- Augmentation

**BACKGROUND:** Talk about the role of hyperparameters and augmentation

As this is discussed, get the complete finetune run.

Steps to import:

    $ curl -L https://s3.amazonaws.com/guild-pub/tensorflow-workshop/archive/859c96044c8f11e8810e107b44920855.tar.gz \
      > /tmp/859c96044c8f11e8810e107b44920855.tar.gz
    $ tar -C ~/anaconda3/envs/workshop/.guild/runs -xf /tmp/859c96044c8f11e8810e107b44920855.tar.gz
    $ echo 'guildfile:/home/ubuntu/workshop/src - pets-faster-rcnn-resnet101 finetune' \
      > ~/anaconda3/envs/workshop/.guild/runs/859c96044c8f11e8810e107b44920855/.guild/attrs/opref

When the discussions are wrapping up, we should have a full finetuned
model (all 200K steps) on hand and ready for evaluation.

### Evaluate trained model

With our trained model(s) (i.e. what was completed in the previous
section as well as the full finetuned model) we can evaluate how it
does on data it hasn't seen.

This command will evalute the latest finetune operation:

    $ guild run pets-faster-rcnn-resnet101:evaluate

This command will evaluate the completed run (200K steps), provided it
was imported (see above):

    $ guild run pets-faster-rcnn-resnet101:evaluate trained-model=859c9604

This will generate images with highlighted predicted objects and
output an overal average precision for the model.

**BACKGROUND:** Talk about overfitting, evaluating models, and test
data

Once the evaluation is done, we can use TensorBoard to view the
labeled images and precision across classes.

Note that we're evaluating using the pets validation dataset. This
tests how well the model generalizes, at least within the pets
dataset.

We can remove any finetune and evaluate runs that we don't want at
this point.

### Test model on collected images

Having evaluated the trained model using the pets validation data, we
want to see how the detector works on our collected images.

First export our model:

    $ guild run pets-faster-rcnn-resnet101:export checkpoint-step=STEP

NOTE: We need to explicitly specify a checkpoint step for export,
which we can get by running `guild runs info -F` on the finetune run,
or use Guild View to view run files.

And then detect:

    $ guild run pets-faster-rcnn-resnet101:detect

This will likely have become worse, since our object is not really a
cat and our model has become a specialist in real pets!

**BACKGROUND:** Semi supervised, process of error checking models

## Improve our detector using a custom dataset

Having tried both an off-the-shelf model trained on a general dataset
and a fine tuned model trained on a pet-specific dataset, we'll
attempt to improve our model by training on a custom dataset. This
will let us train on the object itself in context.

### Collect cat images

Our first step is to collect images. We'll use the `collect` operation
for `cats-dataset`:

    $ guild run images:collect use-proxy=yes

Students can take turns moving the object around the room and taking
snapshots.

We can start with 10 images just to see how far we can get. We can add
more as needed later.

### Label cat images

Once we have some images, we need to label them using the `label`
operation:

    $ guild run cats-dataset:label

Show the `annotations/` files, which contain the label information.

### Prepare cats dataset

Once we have labeled our cat images, we can prepare the dataset for
training and validation.

    $ guild run cats-dataset:prepare

This is similar to the prepare operation on pets, but applied to our
custom images rather than a downloaded imageset.

### Train cats model

With our prepared cats dataset, we can fine tune:

    $ guild run cats-faster-rcnn-resnet101:finetune

This operation should be run on the large GPU as the student servers
will take too long. Our initial run should be time-boxed for 10-15
minutes, just to see how things go.

NOTE: We're using Faster RCNN here as we don't need masks for our
application. We can explain this, refering to the background on Faster
and Mask pipelines to point out that they're the same model when masks
aren't used.

### Validate trained cats model

Once we've trained our cats model on our novel dataset, we can
evaluate it:

    $ guild run cats-faster-rcnn-resnet101:evaluate

This won't be much of a test since our validation set is very small,
but it will give us some idea of how we're doing.

### Test model on collected images

We can see how our model works on our initial images.

First export our model:

    $ guild run cats-faster-rcnn-resnet101:export checkpoint-step=STEP

And then detect:

    $ guild run cats-faster-rcnn-resnet101:detect

## Improve our detector with more data

We should now have a pretty good detector, even with 10 images! But we
should also have seen some problems:

- False negatives where the object is in unseen positions or locations

- False positives, e.g. similar objects and even people can be
  detected

We can note the type of error and contrive images that will steer the
model in the right direction.

This will repeat the steps from the previous section to train a new
model.

Note that images and annotations can be reused from the previous
labeling exercise.

We can also create a separate dataset for validating our trained
model. These would be all new images, which the model hasn't seen, and
represent an excellent test of our model. Once tested, we can roll
these images into our training set.

NOTE: This process of data collection, validation, and re-training can
be repeated indefinitely, and reflects a real world application
development scenario. It highlights the importance of data and the
ability to collect new data for both testing and improving models.

## Run the application

With our final model in hand, we can run our catscan application:

    $ guild run cats-faster-rcnn-resnet101:scan

This will present a live view of the workshop environment (per the
workshop cameras) with object detection and logging!

At this point, we've seen the evolution of our model and the process
for improving it. Once deployed, we can go back to improve either the
model or the host application using a similar iterative process.

## Review

What was covered:

- Naive use of off-the-shelf model
- Naive fine tuning using an available dataset
- Creation of a custom dataset
- Fine tuning using the custom dataset
- Iteration with more custom data
- App deployment
