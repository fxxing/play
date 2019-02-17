
#ifndef PLAY_INTLIST_H
#define PLAY_INTLIST_H

#include <play.h>

Class(play_IntList, {
    pint length;
    pint *items;
});

NATIVE pint play_IntList_get_I_I(play_IntList this, pint index);

#endif //PLAY_INTLIST_H
