#include <play/Object.h>
#include <play/String.h>
#include <string.h>
#include "const.h"
#include "tgc.h"

extern Class CLASSES[];

static tgc_t gc;


NATIVE void *new(int size) {
    return tgc_alloc(&gc, size);
}

NATIVE play_String newString(char *str) {
    play_String string = new(sizeof(struct struct_play_String));
    string->length = (pint) strlen(str);
    string->value = str;
    return string;
}

pboolean isSubClassOf(int thisId, int targetId) {
    Class *class = &CLASSES[thisId];
    if (class->classId == targetId) return TRUE;
    for (int i = 0; i < class->superCount; i++) {
        int superId = class->superclasses[i];
        if (superId == targetId || isSubClassOf(superId, targetId)) {
            return TRUE;
        }
    }
    return FALSE;
}

pboolean isInstanceOf(play_Object object, int classId) {
    return isSubClassOf(object->classId, classId);
}


NATIVE play_Object cast(play_Object object, int classId) {
    Class *class = &CLASSES[object->classId];
    if (isInstanceOf(object, classId)) {
        return object;
    }
    printf("Cannot cast from %s to %s", class->name, CLASSES[classId].name);
    exit(1);
}

NATIVE int *loadMethod(play_Object object, int methodId) {
    return CLASSES[object->classId].methods[methodId].func;
}

extern void initConst();

extern void playMain();

NATIVE void initialize() {
    initConst();
}

NATIVE void runGC() {
    tgc_run(&gc);
}


int main(int argc, char **argv) {
    tgc_start(&gc, &argc);
    initialize();
    playMain();
    tgc_stop(&gc);
}