
#include "String.h"


NATIVE play_String play_String_new() {
    return malloc(sizeof(struct struct_play_String));
}

NATIVE void play_String_concat_V_TO(play_String this, play_String str, play_Object other) {
}

NATIVE void play_String_concat_V_TI(play_String this, play_String str, pint other) {
}

NATIVE void play_String_concat_V_TT(play_String this, play_String str, play_String other) {
}

NATIVE void play_String_concat_V_TS(play_String this, play_String str, pshort other) {
}

NATIVE void play_String_concat_V_TD(play_String this, play_String str, pdouble other) {
}

NATIVE void play_String_concat_V_TB(play_String this, play_String str, pbyte other) {
}

NATIVE void play_String_concat_V_TF(play_String this, play_String str, pfloat other) {
}

NATIVE void play_String_concat_V_TZ(play_String this, play_String str, pboolean other) {
}

NATIVE void play_String_concat_V_TL(play_String this, play_String str, plong other) {
}

