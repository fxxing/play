
#ifndef PLAY_LIST_H
#define PLAY_LIST_H

#include <play.h>
#include <play/Object.h>

Class(play_List, {
    pint length;
    play_Object items;
});

NATIVE play_Object play_List_get_O_I(play_List this, pint index);

#endif //PLAY_LIST_H
