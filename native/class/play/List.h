
#ifndef PLAY_LIST_H
#define PLAY_LIST_H

#include <play.h>
#include <play/Object.h>

DefineClass(play_List, {
    OBJECT_HEADER;
    pint length;
    play_Object items;
});

#endif //PLAY_LIST_H
