
#include "Class.h"


extern int play_Class_id;

NATIVE play_Class play_Class_new() {
    play_Class this = new(sizeof(struct struct_play_Class));
    this->classId = play_Class_id;
    return this;
}

