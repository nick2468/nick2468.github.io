---
title: jcc
summary: A small C compiler written in Java. It turns a subset of C into programs that run on Windows and Linux.
platforms: Windows, Linux
source: https://github.com/nick2468/jcc
media:
  - file: 01-hello-world.png
    alt: The HelloWorld.c example beside the assembly jcc wrote for it. Below, jcc compiles the file step by step, and the program prints "Hello, World!".
---
jcc is a minimal compiler for the C language, written in Java. It reads C source code and
writes x86-64 assembly, which standard tools then turn into a program you can run.

It finds out whether it is on Windows or Linux and follows that system's rules for calling
functions, so one compiler serves both.
