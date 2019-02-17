
#include <stddef.h>
#include "List.h"

NATIVE play_Object play_List_get_O_I(play_List this, pint index) {
    return index < this->length ? this->items + index : NULL;
}