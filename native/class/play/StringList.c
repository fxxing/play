
#include "StringList.h"

NATIVE play_String play_StringList_new() {
    return malloc(sizeof(struct struct_play_StringList));
}

NATIVE play_String play_StringList_get_T_I(play_StringList this, pint index) {
    return index < this->length ? this->items + index : NULL;
}

