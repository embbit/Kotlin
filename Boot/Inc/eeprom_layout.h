#ifndef EEPROM_LAYOUT_H
#define EEPROM_LAYOUT_H

#include "stm32f1xx_hal.h"

/* Variables' number */
#define NB_OF_VAR             ((uint16_t)18)
#define APPL_EEPROM_START   VSCP_PS_ADDR_NEXT

extern uint16_t VirtAddVarTab[];
    

#endif
