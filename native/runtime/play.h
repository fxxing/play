//
// Created by Fengxiang Xing on 2019-02-15.
//


#ifndef PLAY_H
#define PLAY_H

#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

typedef unsigned char pboolean;
typedef unsigned char pbyte;
typedef short pshort;
typedef int pint;
typedef long plong;
typedef float pfloat;
typedef double pdouble;

#define OBJECT_HEADER  int classId;

#define TRUE 1
#define FALSE 0


#define DefineClass(name, text) struct struct_##name text; \
typedef struct struct_##name* name;

#define NATIVE __attribute__((unused))

NATIVE void* new(int size);


#endif //PLAY_H
