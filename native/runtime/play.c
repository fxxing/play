#include <play/Object.h>
#include <play/String.h>
#include <stdlib.h>
#include <string.h>


play_Object new_class() {
    return NULL;
}

play_String new_string(char *str) {
    play_String string = malloc(sizeof(struct struct_play_String));
    string->length = (pint) strlen(str);
    string->value = str;
    return string;
}

play_Object cast(play_Object object) {
    return object;
}