//
// Created by Fengxiang Xing on 2019-02-15.
//


#ifndef PLAY_H
#define PLAY_H

typedef unsigned char pboolean;
typedef unsigned char pbyte;
typedef short pshort;
typedef int pint;
typedef long plong;
typedef float pfloat;
typedef double pdouble;

#define TRUE 1
#define FALSE 0



#define Class(name, text) struct struct_##name text; \
typedef struct struct_##name* name;

#define NATIVE __attribute__((unused))

#endif //PLAY_H
