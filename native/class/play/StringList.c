
#include "StringList.h"

extern int play_StringList_id;

NATIVE play_StringList play_StringList_new() {
    play_StringList this = new(sizeof(struct struct_play_StringList));
    this->classId = play_StringList_id;
    return this;
}

NATIVE play_String play_StringList_get_T_I(play_StringList this, pint index) {
    return index < this->length ? this->items + index : NULL;
}

