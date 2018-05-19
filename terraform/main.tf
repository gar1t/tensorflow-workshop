variable "profile" {
  description = "one of:\n- proxy-only (no gpus)\n- one (only one gpu)\n- dev (large gpu and image-proxy)\n- test (one of every each)\n- full (everything)"
}

variable "us_east_1_standard_gpu_counts" {
  default = {
    "proxy-only" = "0"
    "one" = "1"
    "dev" = "0"
    "test" = "1"
    "full" = "2"
  }
}

variable "us_east_1_large_gpu_counts" {
  default = {
    "proxy-only" = "0"
    "one" = "0"
    "dev" = "1"
    "test" = "0"
    "full" = "1"
  }
}

variable "us_east_2_standard_gpu_counts" {
  default = {
    "proxy-only" = "0"
    "one" = "0"
    "dev" = "0"
    "test" = "1"
    "full" = "20"
  }
}

variable "us_west_2_standard_gpu_counts" {
  default = {
    "proxy-only" = "0"
    "one" = "0"
    "dev" = "0"
    "test" = "1"
    "full" = "5"
  }
}

module "image-proxy" {
  source = "./image-proxy"
  region = "us-east-1"
  ami = "ami-43a15f3e"
  eip_allocation_id = "eipalloc-44769f4c"
}

module "gpu-us-east-1" {
  source = "./gpu"
  region = "us-east-1"
  ami = "ami-8024aaff"
  # ami = "ami-870a99f8"
  standard_count = "${lookup(var.us_east_1_standard_gpu_counts, var.profile)}"
  large_count = "${lookup(var.us_east_1_large_gpu_counts, var.profile)}"
}

module "gpu-us-east-2" {
  source = "./gpu"
  region = "us-east-2"
  ami = "ami-e4f4c981"
  standard_count = "${lookup(var.us_east_2_standard_gpu_counts, var.profile)}"
  large_count = 0
}

module "gpu-us-west-2" {
  source = "./gpu"
  region = "us-west-2"
  ami = "ami-0faada77"
  standard_count = "${lookup(var.us_west_2_standard_gpu_counts, var.profile)}"
  large_count = 0
}
