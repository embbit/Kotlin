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
@brief  VSCP transport layer adapter
@file   vscp_tp_adapter.c
@author Andreas Merkle, http://www.blue-andi.de

@section desc Description
@see vscp_tp_adapter.h

*******************************************************************************/

/*******************************************************************************
    INCLUDES
*******************************************************************************/
#include "vscp_tp_adapter.h"
#include "can.h"

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
static CanTxMsgTypeDef TxMessage;
static CanRxMsgTypeDef RxMessage;
/*******************************************************************************
    GLOBAL VARIABLES
*******************************************************************************/

/*******************************************************************************
    GLOBAL FUNCTIONS
*******************************************************************************/

/**
 * This function initializes the transport layer.
 */
extern void vscp_tp_adapter_init(void)
{
    /* Implement your code here ... */

    return;
}

/**
 * This function reads a message from the transport layer.
 *
 * @param[out]  msg Message storage
 * @return  Message received or not
 * @retval  FALSE   No message received
 * @retval  TRUE    Message received
 */
extern BOOL vscp_tp_adapter_readMessage(vscp_RxMessage * const msg)
{
    BOOL    status  = FALSE;
    uint8_t DataCounter;    

    if (NULL != msg)
    {
        hcan1.pRxMsg = &RxMessage;
        if (HAL_OK == HAL_CAN_Receive_IT(&hcan1, CAN_FIFO0))
        {
           msg->priority = (VSCP_PRIORITY)((RxMessage.ExtId >> 26) & 0x07);
           msg->hardCoded = (BOOL)((RxMessage.ExtId >> 25) & 0x01);
           msg->vscpClass = (uint16_t)((RxMessage.ExtId >> 16) & 0x01FF);
           msg->vscpType = (uint8_t)((RxMessage.ExtId >> 8) & 0xFF);     
           msg->oAddr = (uint8_t)(RxMessage.ExtId & 0xFF);           
           msg->dataNum = RxMessage.DLC;
          
           for (DataCounter = 0; DataCounter < TxMessage.DLC; DataCounter++)
           {
               msg->data[DataCounter] = RxMessage.Data[DataCounter];        
           }           
           status  = TRUE;           
        }         

    }

    return status;
}

/**
 * This function writes a message to the transport layer.
 *
 * @param[in]   msg Message storage
 * @return  Message sent or not
 * @retval  FALSE   Couldn't send message
 * @retval  TRUE    Message successful sent
 */
extern BOOL vscp_tp_adapter_writeMessage(vscp_TxMessage const * const msg)
{
    BOOL    status  = FALSE;
    uint8_t DataCounter;

    if ((NULL != msg) &&                        /* Message shall exists */
        (VSCP_L1_DATA_SIZE >= msg->dataNum))    /* Number of data bytes is limited */
    {
        TxMessage.ExtId = (msg->priority << 26)\
                        + (msg->hardCoded << 25)\
                        + (msg->vscpClass << 16)\
                        + (msg->vscpType << 8)\
                        + (msg->oAddr);
        TxMessage.IDE = CAN_ID_EXT;
        TxMessage.RTR = CAN_RTR_DATA;
        TxMessage.DLC = msg->dataNum;
        
        for (DataCounter = 0; DataCounter < TxMessage.DLC; DataCounter++)
        {
           TxMessage.Data[DataCounter] = msg->data[DataCounter];        
        }
        
        hcan1.pTxMsg = &TxMessage;
        if (HAL_OK == HAL_CAN_Transmit_IT(&hcan1))
        {
           status = TRUE;
        }
    }
    return status;
}

/*******************************************************************************
    LOCAL FUNCTIONS
*******************************************************************************/

