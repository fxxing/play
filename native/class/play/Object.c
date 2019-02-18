
#include "Object.h"

extern int play_Object_id;

NATIVE void play_Object_init(play_Object this) {
    this->classId = play_Object_id;
}

NATIVE play_Object play_Object_new() {
    play_Object this =new(sizeof(struct struct_play_Object));
    play_Object_init(this);
    return this;
}

NATIVE pboolean play_Object_equals_Z_O(play_Object this, play_Object other) {
    return (pboolean) (this == other);
}
