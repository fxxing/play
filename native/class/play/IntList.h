
#ifndef PLAY_INTLIST_H
#define PLAY_INTLIST_H

#include <play.h>

DefineClass(play_IntList, {
    OBJECT_HEADER;
    pint length;
    pint *items;
});

#endif //PLAY_INTLIST_H
