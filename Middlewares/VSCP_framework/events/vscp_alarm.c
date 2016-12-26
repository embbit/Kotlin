/* The MIT License (MIT)
 *
 * Copyright (c) 2014 - 2016, Andreas Merkle
 * http://www.blue-andi.de
 * vscp@blue-andi.de
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */

/*******************************************************************************
    DESCRIPTION
*******************************************************************************/
/**
@brief  VSCP class 1 type Alarm events
@file   vscp_alarm.c
@author Andreas Merkle, http://www.blue-andi.de

@section desc Description
@see vscp_alarm.h

This file is automatically generated. Don't change it manually.

*******************************************************************************/

/*******************************************************************************
    INCLUDES
*******************************************************************************/
#include "vscp_alarm.h"
#include "vscp_core.h"
#include "vscp_class_l1.h"
#include "vscp_type_alarm.h"

/*******************************************************************************
    COMPILER SWITCHES
*******************************************************************************/

/*******************************************************************************
    CONSTANTS
*******************************************************************************/

/*******************************************************************************
    MACROS
*******************************************************************************/

/*******************************************************************************
    TYPES AND STRUCTURES
*******************************************************************************/

/*******************************************************************************
    PROTOTYPES
*******************************************************************************/

/*******************************************************************************
    LOCAL VARIABLES
*******************************************************************************/

/*******************************************************************************
    GLOBAL VARIABLES
*******************************************************************************/

/*******************************************************************************
    GLOBAL FUNCTIONS
*******************************************************************************/

/**
 * Undefined alarm.
 *
 * @return Status
 * @retval FALSE Failed to send the event
 * @retval TRUE  Event successul sent
 *
 */
extern BOOL vscp_alarm_sendUndefinedEvent(void)
{
    vscp_TxMessage txMsg;

    vscp_core_prepareTxMessage(&txMsg, VSCP_CLASS_L1_ALARM, VSCP_TYPE_ALARM_UNDEFINED, VSCP_PRIORITY_3_NORMAL);

    txMsg.dataNum = 0;

    return vscp_core_sendEvent(&txMsg);
}

/**
 * Indicates a warning condition.
 *
 * @param[in] userData User defined data.
 * @param[in] zone Zone for which event applies to (0-255). 255 is all zones.
 * @param[in] subZone Sub-zone for which event applies to (0-255). 255 is all sub-zones.
 * @return Status
 * @retval FALSE Failed to send the event
 * @retval TRUE  Event successul sent
 *
 */
extern BOOL vscp_alarm_sendWarningEvent(uint8_t userData, uint8_t zone, uint8_t subZone)
{
    vscp_TxMessage txMsg;

    vscp_core_prepareTxMessage(&txMsg, VSCP_CLASS_L1_ALARM, VSCP_TYPE_ALARM_WARNING, VSCP_PRIORITY_3_NORMAL);

    txMsg.dataNum = 3;
    txMsg.data[0] = userData;
    txMsg.data[1] = zone;
    txMsg.data[2] = subZone;

    return vscp_core_sendEvent(&txMsg);
}

/**
 * Indicates an alarm condition.
 *
 * @param[in] userData User defined data.
 * @param[in] zone Zone for which event applies to (0-255). 255 is all zones.
 * @param[in] subZone Sub-zone for which event applies to (0-255). 255 is all sub-zones.
 * @return Status
 * @retval FALSE Failed to send the event
 * @retval TRUE  Event successul sent
 *
 */
extern BOOL vscp_alarm_sendAlarmOccurredEvent(uint8_t userData, uint8_t zone, uint8_t subZone)
{
    vscp_TxMessage txMsg;

    vscp_core_prepareTxMessage(&txMsg, VSCP_CLASS_L1_ALARM, VSCP_TYPE_ALARM_ALARM_OCCURRED, VSCP_PRIORITY_3_NORMAL);

    txMsg.dataNum = 3;
    txMsg.data[0] = userData;
    txMsg.data[1] = zone;
    txMsg.data[2] = subZone;

    return vscp_core_sendEvent(&txMsg);
}

/**
 * Alarm sound should be turned on or off.
 *
 * @param[in] state 0=off. 1=on.
 * @param[in] zone Zone for which event applies to (0-255). 255 is all zones.
 * @param[in] subZone Sub-zone for which event applies to (0-255). 255 is all sub-zones.
 * @return Status
 * @retval FALSE Failed to send the event
 * @retval TRUE  Event successul sent
 *
 */
extern BOOL vscp_alarm_sendAlarmSoundOnOffEvent(uint8_t state, uint8_t zone, uint8_t subZone)
{
    vscp_TxMessage txMsg;

    vscp_core_prepareTxMessage(&txMsg, VSCP_CLASS_L1_ALARM, VSCP_TYPE_ALARM_ALARM_SOUND_ON_OFF, VSCP_PRIORITY_3_NORMAL);

    txMsg.dataNum = 3;
    txMsg.data[0] = state;
    txMsg.data[1] = zone;
    txMsg.data[2] = subZone;

    return vscp_core_sendEvent(&txMsg);
}

/**
 * Alarm light should be turned on or off.
 *
 * @param[in] userData User defined data.
 * @param[in] zone Zone for which event applies to (0-255). 255 is all zones.
 * @param[in] subZone Sub-zone for which event applies to (0-255). 255 is all sub-zones.
 * @return Status
 * @retval FALSE Failed to send the event
 * @retval TRUE  Event successul sent
 *
 */
extern BOOL vscp_alarm_sendAlarmLightOnOffEvent(uint8_t userData, uint8_t zone, uint8_t subZone)
{
    vscp_TxMessage txMsg;

    vscp_core_prepareTxMessage(&txMsg, VSCP_CLASS_L1_ALARM, VSCP_TYPE_ALARM_ALARM_LIGHT_ON_OFF, VSCP_PRIORITY_3_NORMAL);

    txMsg.dataNum = 3;
    txMsg.data[0] = userData;
    txMsg.data[1] = zone;
    txMsg.data[2] = subZone;

    return vscp_core_sendEvent(&txMsg);
}

/**
 * Power has been lost or is available again.
 *
 * @param[in] userData User defined data.
 * @param[in] zone Zone for which event applies to (0-255). 255 is all zones.
 * @param[in] subZone Sub-zone for which event applies to (0-255). 255 is all sub-zones.
 * @return Status
 * @retval FALSE Failed to send the event
 * @retval TRUE  Event successul sent
 *
 */
extern BOOL vscp_alarm_sendPowerOnOffEvent(uint8_t userData, uint8_t zone, uint8_t subZone)
{
    vscp_TxMessage txMsg;

    vscp_core_prepareTxMessage(&txMsg, VSCP_CLASS_L1_ALARM, VSCP_TYPE_ALARM_POWER_ON_OFF, VSCP_PRIORITY_3_NORMAL);

    txMsg.dataNum = 3;
    txMsg.data[0] = userData;
    txMsg.data[1] = zone;
    txMsg.data[2] = subZone;

    return vscp_core_sendEvent(&txMsg);
}

/**
 * Emergency stop has been hit/activated. All systems on the zone/sub-zone should go to their
 * inactive/safe state.
 *
 * @param[in] userData User defined data.
 * @param[in] zone Zone for which event applies to (0-255). 255 is all zones.
 * @param[in] subZone Sub-zone for which event applies to (0-255). 255 is all sub-zones.
 * @return Status
 * @retval FALSE Failed to send the event
 * @retval TRUE  Event successul sent
 *
 */
extern BOOL vscp_alarm_sendEmergencyStopEvent(uint8_t userData, uint8_t zone, uint8_t subZone)
{
    vscp_TxMessage txMsg;

    vscp_core_prepareTxMessage(&txMsg, VSCP_CLASS_L1_ALARM, VSCP_TYPE_ALARM_EMERGENCY_STOP, VSCP_PRIORITY_3_NORMAL);

    txMsg.dataNum = 3;
    txMsg.data[0] = userData;
    txMsg.data[1] = zone;
    txMsg.data[2] = subZone;

    return vscp_core_sendEvent(&txMsg);
}

/**
 * Emergency pause has been hit/activated. All systems on the zone/sub-zone should go to their
 * inactive/safe state but preserve there settings.
 *
 * @param[in] userData User defined data.
 * @param[in] zone Zone for which event applies to (0-255). 255 is all zones.
 * @param[in] subZone Sub-zone for which event applies to (0-255). 255 is all subzones.
 * @return Status
 * @retval FALSE Failed to send the event
 * @retval TRUE  Event successul sent
 *
 */
extern BOOL vscp_alarm_sendEmergencyPauseEvent(uint8_t userData, uint8_t zone, uint8_t subZone)
{
    vscp_TxMessage txMsg;

    vscp_core_prepareTxMessage(&txMsg, VSCP_CLASS_L1_ALARM, VSCP_TYPE_ALARM_EMERGENCY_PAUSE, VSCP_PRIORITY_3_NORMAL);

    txMsg.dataNum = 3;
    txMsg.data[0] = userData;
    txMsg.data[1] = zone;
    txMsg.data[2] = subZone;

    return vscp_core_sendEvent(&txMsg);
}

/**
 * Issued after an emergency stop or pause in order for nodes to reset and start operating .
 *
 * @param[in] userData User defined data.
 * @param[in] zone Zone for which event applies to (0-255). 255 is all zones.
 * @param[in] subZone Sub-zone for which event applies to (0-255). 255 is all sub-zones.
 * @return Status
 * @retval FALSE Failed to send the event
 * @retval TRUE  Event successul sent
 *
 */
extern BOOL vscp_alarm_sendEmergencyResetEvent(uint8_t userData, uint8_t zone, uint8_t subZone)
{
    vscp_TxMessage txMsg;

    vscp_core_prepareTxMessage(&txMsg, VSCP_CLASS_L1_ALARM, VSCP_TYPE_ALARM_EMERGENCY_RESET, VSCP_PRIORITY_3_NORMAL);

    txMsg.dataNum = 3;
    txMsg.data[0] = userData;
    txMsg.data[1] = zone;
    txMsg.data[2] = subZone;

    return vscp_core_sendEvent(&txMsg);
}

/**
 * Issued after an emergency pause in order for nodes to start operating from where they left of
 * without resetting their registers .
 *
 * @param[in] userData User defined data.
 * @param[in] zone Zone for which event applies to (0-255). 255 is all zones.
 * @param[in] subZone Sub-zone for which event applies to (0-255). 255 is all sub-zones.
 * @return Status
 * @retval FALSE Failed to send the event
 * @retval TRUE  Event successul sent
 *
 */
extern BOOL vscp_alarm_sendEmergencyResumeEvent(uint8_t userData, uint8_t zone, uint8_t subZone)
{
    vscp_TxMessage txMsg;

    vscp_core_prepareTxMessage(&txMsg, VSCP_CLASS_L1_ALARM, VSCP_TYPE_ALARM_EMERGENCY_RESUME, VSCP_PRIORITY_3_NORMAL);

    txMsg.dataNum = 3;
    txMsg.data[0] = userData;
    txMsg.data[1] = zone;
    txMsg.data[2] = subZone;

    return vscp_core_sendEvent(&txMsg);
}

/*******************************************************************************
    LOCAL FUNCTIONS
*******************************************************************************/

