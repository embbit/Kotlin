/**
  ******************************************************************************
  * File Name          : main.h
  * Description        : This file contains the common defines of the application
  ******************************************************************************
  *
  * Copyright (c) 2017 STMicroelectronics International N.V. 
  * All rights reserved.
  *
  * Redistribution and use in source and binary forms, with or without 
  * modification, are permitted, provided that the following conditions are met:
  *
  * 1. Redistribution of source code must retain the above copyright notice, 
  *    this list of conditions and the following disclaimer.
  * 2. Redistributions in binary form must reproduce the above copyright notice,
  *    this list of conditions and the following disclaimer in the documentation
  *    and/or other materials provided with the distribution.
  * 3. Neither the name of STMicroelectronics nor the names of other 
  *    contributors to this software may be used to endorse or promote products 
  *    derived from this software without specific written permission.
  * 4. This software, including modifications and/or derivative works of this 
  *    software, must execute solely and exclusively on microcontroller or
  *    microprocessor devices manufactured by or for STMicroelectronics.
  * 5. Redistribution and use of this software other than as permitted under 
  *    this license is void and will automatically terminate your rights under 
  *    this license. 
  *
  * THIS SOFTWARE IS PROVIDED BY STMICROELECTRONICS AND CONTRIBUTORS "AS IS" 
  * AND ANY EXPRESS, IMPLIED OR STATUTORY WARRANTIES, INCLUDING, BUT NOT 
  * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
  * PARTICULAR PURPOSE AND NON-INFRINGEMENT OF THIRD PARTY INTELLECTUAL PROPERTY
  * RIGHTS ARE DISCLAIMED TO THE FULLEST EXTENT PERMITTED BY LAW. IN NO EVENT 
  * SHALL STMICROELECTRONICS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
  * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
  * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, 
  * OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF 
  * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING 
  * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
  * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
  *
  ******************************************************************************
  */
/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H
  /* Includes ------------------------------------------------------------------*/

/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private define ------------------------------------------------------------*/
#define VSCP_CORE_PERIOD 100
#define VSCP_TIMER_PERIOD 1000
#define VSCP_LED_PERIOD_FAST 100
#define VSCP_LED_PERIOD_SLOW 800

#define EXT_GPIO_1_Pin GPIO_PIN_13
#define EXT_GPIO_1_GPIO_Port GPIOC
#define EXT_GPIO_2_Pin GPIO_PIN_14
#define EXT_GPIO_2_GPIO_Port GPIOC
#define EXT_GPIO_3_Pin GPIO_PIN_15
#define EXT_GPIO_3_GPIO_Port GPIOC
#define VSCP_BTN_Pin GPIO_PIN_0
#define VSCP_BTN_GPIO_Port GPIOC
#define VSCP_LED_Pin GPIO_PIN_1
#define VSCP_LED_GPIO_Port GPIOC
#define CH6_REL2_CNTRL_Pin GPIO_PIN_2
#define CH6_REL2_CNTRL_GPIO_Port GPIOC
#define CH6_REL1_CNTRL_Pin GPIO_PIN_3
#define CH6_REL1_CNTRL_GPIO_Port GPIOC
#define CH5_REL2_CNTRL_Pin GPIO_PIN_0
#define CH5_REL2_CNTRL_GPIO_Port GPIOA
#define CH5_REL1_CNTRL_Pin GPIO_PIN_1
#define CH5_REL1_CNTRL_GPIO_Port GPIOA
#define CH4_REL2_CNTRL_Pin GPIO_PIN_2
#define CH4_REL2_CNTRL_GPIO_Port GPIOA
#define CH4_REL1_CNTRL_Pin GPIO_PIN_3
#define CH4_REL1_CNTRL_GPIO_Port GPIOA
#define F_CS_Pin GPIO_PIN_4
#define F_CS_GPIO_Port GPIOA
#define OW_PWR_FAULT_Pin GPIO_PIN_5
#define OW_PWR_FAULT_GPIO_Port GPIOA
#define OW_PWR_EN_Pin GPIO_PIN_6
#define OW_PWR_EN_GPIO_Port GPIOA
#define EXT_GPIO_4_Pin GPIO_PIN_0
#define EXT_GPIO_4_GPIO_Port GPIOB
#define EXT_GPIO_5_Pin GPIO_PIN_1
#define EXT_GPIO_5_GPIO_Port GPIOB
#define EXT_GPIO_6_Pin GPIO_PIN_2
#define EXT_GPIO_6_GPIO_Port GPIOB
#define RS485_RX_Pin GPIO_PIN_10
#define RS485_RX_GPIO_Port GPIOB
#define RS485_RXB11_Pin GPIO_PIN_11
#define RS485_RXB11_GPIO_Port GPIOB
#define RS485_DE_RE_Pin GPIO_PIN_12
#define RS485_DE_RE_GPIO_Port GPIOB
#define EXT_SPI_SCK_Pin GPIO_PIN_13
#define EXT_SPI_SCK_GPIO_Port GPIOB
#define EXT_SPI_MISO_Pin GPIO_PIN_14
#define EXT_SPI_MISO_GPIO_Port GPIOB
#define EXT_SPI_MOSI_Pin GPIO_PIN_15
#define EXT_SPI_MOSI_GPIO_Port GPIOB
#define CH1_REL2_CNTRL_Pin GPIO_PIN_6
#define CH1_REL2_CNTRL_GPIO_Port GPIOC
#define CH1_REL1_CNTRL_Pin GPIO_PIN_7
#define CH1_REL1_CNTRL_GPIO_Port GPIOC
#define CH2_REL2_CNTRL_Pin GPIO_PIN_8
#define CH2_REL2_CNTRL_GPIO_Port GPIOC
#define CH2_REL1_CNTRL_Pin GPIO_PIN_9
#define CH2_REL1_CNTRL_GPIO_Port GPIOC
#define CH3_REL2_CNTRL_Pin GPIO_PIN_8
#define CH3_REL2_CNTRL_GPIO_Port GPIOA
#define CH3_REL1_CNTRL_Pin GPIO_PIN_10
#define CH3_REL1_CNTRL_GPIO_Port GPIOA
#define F_SCK_Pin GPIO_PIN_10
#define F_SCK_GPIO_Port GPIOC
#define F_MISO_Pin GPIO_PIN_11
#define F_MISO_GPIO_Port GPIOC
#define F_MOSI_Pin GPIO_PIN_12
#define F_MOSI_GPIO_Port GPIOC
#define OW_RX_TX_Pin GPIO_PIN_6
#define OW_RX_TX_GPIO_Port GPIOB
#define CAN1_STB_Pin GPIO_PIN_7
#define CAN1_STB_GPIO_Port GPIOB
/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

/**
  * @}
  */ 

/**
  * @}
*/ 

#endif /* __MAIN_H */
/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
