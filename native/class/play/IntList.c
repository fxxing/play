
#include "IntList.h"


NATIVE play_IntList play_IntList_new() {
    return malloc(sizeof(struct struct_play_IntList));
}

NATIVE pint play_IntList_get_I_I(play_IntList this, pint index) {
    return index < this->length ? *(this->items + index) : 0;
}

