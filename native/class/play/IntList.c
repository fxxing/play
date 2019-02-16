
#include "IntList.h"

NATIVE pint play_IntList_get_I_I(play_IntList this, pint index) {
    return index < this->length ? *(this->items + index) : 0;
}

