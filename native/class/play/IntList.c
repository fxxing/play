
#include "IntList.h"


NATIVE play_IntList play_IntList_new() {
    return new(sizeof(struct struct_play_IntList));
}

extern int play_IntList_id;

NATIVE void play_IntList_init(play_IntList this) {
    this->classId = play_IntList_id;
}

NATIVE pint play_IntList_get_I_I(play_IntList this, pint index) {
    return index < this->length ? *(this->items + index) : 0;
}

