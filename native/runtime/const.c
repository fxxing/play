#include "const.h"
int _root_packages[] = {1};
int _root_classes[] = {0, 1};
int play_packages[] = {};
int play_classes[] = {5, 2, 8, 14, 15, 4, 11, 13, 10, 6, 7, 3, 9, 12};
NATIVE Package PACKAGES[] = {
    {"", 1, _root_packages, 2, _root_classes},
    {"play", 0, play_packages, 14, play_classes},
};
int play_Class_id = 4;
int play_IntList_id = 8;
int play_List_id = 9;
int play_Object_id = 11;
int play_String_id = 13;
int play_StringList_id = 14;
extern int HelloSub_test0_V_;
extern int play_String_String_V_;
extern int play_Byte_Byte_V_B;
extern int play_Long_new;
extern int Hello_new;
extern int play_Double_Double_V_D;
extern int play_List_List_V_;
extern int play_String_concat_V_TZ;
extern int play_Object_new;
extern int Hello_Hello_V_;
extern int play_String_concat_V_TB;
extern int play_String_new;
extern int play_Byte_getValue_B_;
extern int play_Short_new;
extern int play_StringList_get_T_I;
extern int play_Double_new;
extern int play_IntList_new;
extern int play_String_concat_V_TT;
extern int HelloSub_HelloSub_V_;
extern int play_String_concat_V_TS;
extern int play_StringList_new;
extern int play_String_concat_V_TI;
extern int play_Float_getValue_F_;
extern int play_System_new;
extern int play_Boolean_getValue_Z_;
extern int play_Object_equals_Z_O;
extern int play_Boolean_Boolean_V_Z;
extern int play_String_concat_V_TO;
extern int play_Byte_new;
extern int HelloSub_test1_V_;
extern int play_Int_getValue_I_;
extern int play_IntList_get_I_I;
extern int play_System_System_V_;
extern int play_Class_new;
extern int Hello___test1_V_;
extern int play_Float_Float_V_F;
extern int play_Float_new;
extern int play_Int_Int_V_I;
extern int HelloSub_new;
extern int play_List_get_O_I;
extern int play_StringList_StringList_V_;
extern int play_Boolean_new;
extern int play_Double_getValue_D_;
extern int Hello_test0_V_;
extern int play_Short_getValue_S_;
extern int play_List_new;
extern int play_Long_Long_V_L;
extern int play_Class_Class_V_;
extern int play_String_concat_V_TL;
extern int play_String_concat_V_TD;
extern int play_Long_getValue_L_;
extern int play_IntList_IntList_V_;
extern int play_String_concat_V_TF;
extern int play_Int_new;
extern int play_Object_Object_V_;
extern int play_Short_Short_V_S;
int Hello_superclasses[] = {11};
Method Hello_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"test0", 0, 0, "", NULL},
    {"<init>", 0, 0, "", NULL},
    {"__test1", 0, 0, "", NULL},
};
int HelloSub_superclasses[] = {0};
Method HelloSub_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"test0", 1, 0, "", NULL},
    {"test1", 1, 0, "", NULL},
    {"<init>", 1, 0, "", NULL},
};
int play_Boolean_superclasses[] = {11};
Method play_Boolean_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"<init>", 2, 0, "boolean", NULL},
    {"getValue", 2, 0, "", NULL},
};
int play_Byte_superclasses[] = {11};
Method play_Byte_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"<init>", 3, 0, "byte", NULL},
    {"getValue", 3, 0, "", NULL},
};
int play_Class_superclasses[] = {11};
Method play_Class_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"<init>", 4, 0, "", NULL},
};
int play_Double_superclasses[] = {11};
Method play_Double_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"<init>", 5, 0, "double", NULL},
    {"getValue", 5, 0, "", NULL},
};
int play_Float_superclasses[] = {11};
Method play_Float_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"<init>", 6, 0, "float", NULL},
    {"getValue", 6, 0, "", NULL},
};
int play_Int_superclasses[] = {11};
Method play_Int_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"<init>", 7, 0, "int", NULL},
    {"getValue", 7, 0, "", NULL},
};
int play_IntList_superclasses[] = {11};
Method play_IntList_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"get", 8, 0, "int", NULL},
    {"<init>", 8, 0, "", NULL},
};
int play_List_superclasses[] = {11};
Method play_List_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"get", 9, 0, "int", NULL},
    {"<init>", 9, 0, "", NULL},
};
int play_Long_superclasses[] = {11};
Method play_Long_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"<init>", 10, 0, "long", NULL},
    {"getValue", 10, 0, "", NULL},
};
int play_Object_superclasses[] = {};
Method play_Object_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"<init>", 11, 0, "", NULL},
};
int play_Short_superclasses[] = {11};
Method play_Short_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"<init>", 12, 0, "short", NULL},
    {"getValue", 12, 0, "", NULL},
};
int play_String_superclasses[] = {11};
Method play_String_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"concat", 13, 0, "play.String, boolean", NULL},
    {"concat", 13, 0, "play.String, byte", NULL},
    {"concat", 13, 0, "play.String, short", NULL},
    {"concat", 13, 0, "play.String, int", NULL},
    {"concat", 13, 0, "play.String, long", NULL},
    {"concat", 13, 0, "play.String, float", NULL},
    {"concat", 13, 0, "play.String, double", NULL},
    {"concat", 13, 0, "play.String, play.String", NULL},
    {"concat", 13, 0, "play.String, play.Object", NULL},
    {"<init>", 13, 0, "", NULL},
};
int play_StringList_superclasses[] = {11};
Method play_StringList_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"get", 14, 0, "int", NULL},
    {"<init>", 14, 0, "", NULL},
};
int play_System_superclasses[] = {11};
Method play_System_methods[] = {
    {"equals", 11, 0, "play.Object", NULL},
    {"<init>", 15, 0, "", NULL},
};
NATIVE Class CLASSES[] = {
    {"Hello", 0, NULL,  0, 1, Hello_superclasses, 4, Hello_methods},
    {"HelloSub", 1, NULL,  0, 1, HelloSub_superclasses, 4, HelloSub_methods},
    {"play.Boolean", 2, NULL,  0, 1, play_Boolean_superclasses, 3, play_Boolean_methods},
    {"play.Byte", 3, NULL,  0, 1, play_Byte_superclasses, 3, play_Byte_methods},
    {"play.Class", 4, NULL,  4, 1, play_Class_superclasses, 2, play_Class_methods},
    {"play.Double", 5, NULL,  0, 1, play_Double_superclasses, 3, play_Double_methods},
    {"play.Float", 6, NULL,  0, 1, play_Float_superclasses, 3, play_Float_methods},
    {"play.Int", 7, NULL,  0, 1, play_Int_superclasses, 3, play_Int_methods},
    {"play.IntList", 8, NULL,  4, 1, play_IntList_superclasses, 3, play_IntList_methods},
    {"play.List", 9, NULL,  4, 1, play_List_superclasses, 3, play_List_methods},
    {"play.Long", 10, NULL,  0, 1, play_Long_superclasses, 3, play_Long_methods},
    {"play.Object", 11, NULL,  4, 0, play_Object_superclasses, 2, play_Object_methods},
    {"play.Short", 12, NULL,  0, 1, play_Short_superclasses, 3, play_Short_methods},
    {"play.String", 13, NULL,  4, 1, play_String_superclasses, 11, play_String_methods},
    {"play.StringList", 14, NULL,  4, 1, play_StringList_superclasses, 3, play_StringList_methods},
    {"play.System", 15, NULL,  0, 1, play_System_superclasses, 2, play_System_methods},
};
NATIVE void initialize() {
    CLASSES[0].new = &Hello_new;
    CLASSES[1].new = &HelloSub_new;
    CLASSES[2].new = &play_Boolean_new;
    CLASSES[3].new = &play_Byte_new;
    CLASSES[4].new = &play_Class_new;
    CLASSES[5].new = &play_Double_new;
    CLASSES[6].new = &play_Float_new;
    CLASSES[7].new = &play_Int_new;
    CLASSES[8].new = &play_IntList_new;
    CLASSES[9].new = &play_List_new;
    CLASSES[10].new = &play_Long_new;
    CLASSES[11].new = &play_Object_new;
    CLASSES[12].new = &play_Short_new;
    CLASSES[13].new = &play_String_new;
    CLASSES[14].new = &play_StringList_new;
    CLASSES[15].new = &play_System_new;
    Hello_methods[0].func = &play_Object_equals_Z_O;
    Hello_methods[1].func = &Hello_test0_V_;
    Hello_methods[2].func = &Hello_Hello_V_;
    Hello_methods[3].func = &Hello___test1_V_;
    HelloSub_methods[0].func = &play_Object_equals_Z_O;
    HelloSub_methods[1].func = &HelloSub_test0_V_;
    HelloSub_methods[2].func = &HelloSub_test1_V_;
    HelloSub_methods[3].func = &HelloSub_HelloSub_V_;
    play_Boolean_methods[0].func = &play_Object_equals_Z_O;
    play_Boolean_methods[1].func = &play_Boolean_Boolean_V_Z;
    play_Boolean_methods[2].func = &play_Boolean_getValue_Z_;
    play_Byte_methods[0].func = &play_Object_equals_Z_O;
    play_Byte_methods[1].func = &play_Byte_Byte_V_B;
    play_Byte_methods[2].func = &play_Byte_getValue_B_;
    play_Class_methods[0].func = &play_Object_equals_Z_O;
    play_Class_methods[1].func = &play_Class_Class_V_;
    play_Double_methods[0].func = &play_Object_equals_Z_O;
    play_Double_methods[1].func = &play_Double_Double_V_D;
    play_Double_methods[2].func = &play_Double_getValue_D_;
    play_Float_methods[0].func = &play_Object_equals_Z_O;
    play_Float_methods[1].func = &play_Float_Float_V_F;
    play_Float_methods[2].func = &play_Float_getValue_F_;
    play_Int_methods[0].func = &play_Object_equals_Z_O;
    play_Int_methods[1].func = &play_Int_Int_V_I;
    play_Int_methods[2].func = &play_Int_getValue_I_;
    play_IntList_methods[0].func = &play_Object_equals_Z_O;
    play_IntList_methods[1].func = &play_IntList_get_I_I;
    play_IntList_methods[2].func = &play_IntList_IntList_V_;
    play_List_methods[0].func = &play_Object_equals_Z_O;
    play_List_methods[1].func = &play_List_get_O_I;
    play_List_methods[2].func = &play_List_List_V_;
    play_Long_methods[0].func = &play_Object_equals_Z_O;
    play_Long_methods[1].func = &play_Long_Long_V_L;
    play_Long_methods[2].func = &play_Long_getValue_L_;
    play_Object_methods[0].func = &play_Object_equals_Z_O;
    play_Object_methods[1].func = &play_Object_Object_V_;
    play_Short_methods[0].func = &play_Object_equals_Z_O;
    play_Short_methods[1].func = &play_Short_Short_V_S;
    play_Short_methods[2].func = &play_Short_getValue_S_;
    play_String_methods[0].func = &play_Object_equals_Z_O;
    play_String_methods[1].func = &play_String_concat_V_TZ;
    play_String_methods[2].func = &play_String_concat_V_TB;
    play_String_methods[3].func = &play_String_concat_V_TS;
    play_String_methods[4].func = &play_String_concat_V_TI;
    play_String_methods[5].func = &play_String_concat_V_TL;
    play_String_methods[6].func = &play_String_concat_V_TF;
    play_String_methods[7].func = &play_String_concat_V_TD;
    play_String_methods[8].func = &play_String_concat_V_TT;
    play_String_methods[9].func = &play_String_concat_V_TO;
    play_String_methods[10].func = &play_String_String_V_;
    play_StringList_methods[0].func = &play_Object_equals_Z_O;
    play_StringList_methods[1].func = &play_StringList_get_T_I;
    play_StringList_methods[2].func = &play_StringList_StringList_V_;
    play_System_methods[0].func = &play_Object_equals_Z_O;
    play_System_methods[1].func = &play_System_System_V_;
}