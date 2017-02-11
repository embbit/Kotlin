#ifndef _DEBUG_H
#define _DEBUG_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define  DbgLog(...)        printf("DEBUG : ") ;\
                            printf(__VA_ARGS__);\
                            printf("\n");

#endif
