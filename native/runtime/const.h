//
// Created by Fengxiang Xing on 2019-02-15.
//


#ifndef CONST_H
#define CONST_H

#import "play.h"


#define CLASS_FLAG_INTERFACE   (1 << 0)
#define CLASS_FLAG_ABSTRACT    (1 << 1)
#define CLASS_FLAG_NATIVE      (1 << 2)

typedef struct struct_Package {
    const char *name;
    int packageCont;
    int *packages;
    int classCount;
    int *classes;
} Package;

typedef struct struct_Method {
    const char* name;
    int classId;
    int flag;
    char* signature;
    int* func;
} Method;

typedef struct struct_Class {
    const char* name;
    int classId;
    int* new;
    int flag;
    int superCount;
    int* superclasses;
    int methodCount;
    Method* methods;
} Class;


#endif //CONST_H
