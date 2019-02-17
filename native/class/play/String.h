
#ifndef PLAY_STRING_H
#define PLAY_STRING_H

#include <play.h>
#include <play/Object.h>

DefineClass(play_String, {
    OBJECT_HEADER;
    pint length;
    char *value;
});

#endif //PLAY_STRING_H
