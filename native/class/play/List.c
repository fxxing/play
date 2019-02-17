
#include "List.h"


NATIVE play_List play_List_new() {
    return malloc(sizeof(struct struct_play_List));
}

NATIVE play_Object play_List_get_O_I(play_List this, pint index) {
    return index < this->length ? this->items + index : NULL;
}