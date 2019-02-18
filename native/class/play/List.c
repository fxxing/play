
#include "List.h"

extern int play_List_id;

NATIVE play_List play_List_new() {
    play_List this = new(sizeof(struct struct_play_List));
    this->classId = play_List_id;
    return this;
}

NATIVE play_Object play_List_get_O_I(play_List this, pint index) {
    return index < this->length ? this->items + index : NULL;
}