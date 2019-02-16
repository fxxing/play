
#ifndef PLAY_STRINGLIST_H
#define PLAY_STRINGLIST_H

#include <play.h>
#include <play/String.h>

Class(play_StringList, {
    int length;
    play_String items;
});

NATIVE play_String play_StringList_get_T_I(play_StringList this, pint index);

#endif //PLAY_STRINGLIST_H
