
#ifndef PLAY_STRINGLIST_H
#define PLAY_STRINGLIST_H

#include <play.h>
#include <play/String.h>

DefineClass(play_StringList, {
    OBJECT_HEADER;
    pint length;
    play_String items;
});

#endif //PLAY_STRINGLIST_H
