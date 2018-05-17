variable "ami" {}
variable "eip_allocation_id" {}

resource "aws_instance" "image_proxy" {
  ami                    = "${var.ami}"
  instance_type          = "t2.xlarge"
  count                  = 1
  vpc_security_group_ids = ["${aws_security_group.image_proxy.id}"]
  key_name               = "image-proxy"
  connection {
    user = "ubuntu"
    private_key = "${file("keys/image-proxy.pem")}"
  }
  provisioner "remote-exec" {
    script = "scripts/init-image-proxy"
  }
}

resource "aws_default_vpc" "default" {}

resource "aws_security_group" "image_proxy" {
  name        = "image-proxy"
  description = "Image proxy security group"
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

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_eip_association" "image_proxy" {
  instance_id   = "${aws_instance.image_proxy.id}"
  allocation_id = "${var.eip_allocation_id}"
}

output "image_proxy_public_dns" {
  value = ["${aws_instance.image_proxy.public_dns}"]
}
