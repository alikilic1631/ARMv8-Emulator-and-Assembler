#!/bin/bash
if [ ! -d arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf ]; then
    wget https://developer.arm.com/-/media/Files/downloads/gnu/13.2.rel1/binrel/arm-gnu-toolchain-13.2.rel1-x86_64-aarch64-none-elf.tar.xz
    tar -xvf arm-gnu-toolchain-13.2.rel1-x86_64-aarch64-none-elf.tar.xz
fi