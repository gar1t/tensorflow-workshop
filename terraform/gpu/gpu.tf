variable "ami" {}
variable "standard_count" {}
variable "large_count" {}

resource "aws_instance" "standard_gpu" {
  ami                    = "${var.ami}"
  instance_type          = "p2.xlarge"
  count                  = "${var.standard_count}"
  vpc_security_group_ids = ["${aws_security_group.gpu.id}"]
  key_name               = "workshop-admin"
  connection {
    user = "ubuntu"
    private_key = "${file("keys/workshop-admin.pem")}"
  }
  provisioner "remote-exec" {
    scripts = [
      "scripts/init-gpu",
      "scripts/init-gpu-secrets"
    ]
  }
}

output "standard_gpu_public_dns" {
  value = ["${aws_instance.standard_gpu.*.public_dns}"]
}

resource "aws_instance" "large_gpu" {
  ami                    = "${var.ami}"
  instance_type          = "p3.2xlarge"
  count                  = "${var.large_count}"
  vpc_security_group_ids = ["${aws_security_group.gpu.id}"]
  key_name               = "workshop-admin"
  connection {
    user = "ubuntu"
    private_key = "${file("keys/workshop-admin.pem")}"
  }
  provisioner "remote-exec" {
    scripts = [
      "scripts/init-gpu",
      "scripts/init-gpu-secrets"
    ]
  }
}

output "large_gpu_public_dns" {
  value = ["${aws_instance.large_gpu.*.public_dns}"]
}

resource "aws_default_vpc" "default" {}

resource "aws_security_group" "gpu" {
  name        = "workshop-gpu"
  description = "Workshop GPU security group"
  vpc_id      = "${aws_default_vpc.default.id}"

  ingress {
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8999
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
