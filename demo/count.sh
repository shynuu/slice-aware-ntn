#!/bin/bash


docker container ls
N=$(docker ps -q | wc -l)
echo ==========================
echo $N Containers Running